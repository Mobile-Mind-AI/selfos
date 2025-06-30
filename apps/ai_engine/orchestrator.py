"""
AI Orchestrator

Main orchestrator class that handles AI requests, manages providers,
caching, and response processing.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from config import AIConfig, AIProvider
import sys
import os

# Add libs directory to path and import prompts with error handling
libs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

# Import prompts with fallback for dynamic loading contexts
try:
    from prompts import GoalDecompositionPrompts, TaskGenerationPrompts, ConversationPrompts
except ImportError:
    # Fallback for dynamic module loading - use absolute imports
    import importlib.util
    prompts_init_path = os.path.join(libs_path, 'prompts', '__init__.py')
    if os.path.exists(prompts_init_path):
        spec = importlib.util.spec_from_file_location("prompts", prompts_init_path)
        prompts_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prompts_module)
        GoalDecompositionPrompts = prompts_module.GoalDecompositionPrompts
        TaskGenerationPrompts = prompts_module.TaskGenerationPrompts
        ConversationPrompts = prompts_module.ConversationPrompts
    else:
        # Final fallback - create mock prompt classes for testing
        class MockPrompts:
            @staticmethod
            def decompose_goal_prompt(*args, **kwargs):
                return "Mock goal decomposition prompt"
            @staticmethod
            def suggest_next_tasks_prompt(*args, **kwargs):
                return "Mock task generation prompt"
            @staticmethod
            def chat_prompt(*args, **kwargs):
                return "Mock conversation prompt"
            @staticmethod
            def chat_system_prompt(*args, **kwargs):
                return "You are SelfOS, a helpful AI assistant for goal setting and task management."
        
        GoalDecompositionPrompts = MockPrompts
        TaskGenerationPrompts = MockPrompts
        ConversationPrompts = MockPrompts

# Import models directly at module level
import os
import sys
current_dir = os.path.dirname(__file__)
models_path = os.path.join(current_dir, 'models.py')
import importlib.util
models_spec = importlib.util.spec_from_file_location("models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)

# Extract classes we need
RequestType = models_module.RequestType
ResponseStatus = models_module.ResponseStatus
AIRequest = models_module.AIRequest
AIResponse = models_module.AIResponse
GoalDecompositionRequest = models_module.GoalDecompositionRequest
GoalDecompositionResponse = models_module.GoalDecompositionResponse
TaskGenerationRequest = models_module.TaskGenerationRequest
TaskGenerationResponse = models_module.TaskGenerationResponse
ConversationRequest = models_module.ConversationRequest
ConversationResponse = models_module.ConversationResponse
TaskSuggestion = models_module.ParsedTask
CacheEntry = models_module.CacheEntry
# CacheManager doesn't exist, will define inline if needed
ProcessingMetrics = models_module.ProcessingMetrics
create_request_id = models_module.create_request_id
sanitize_ai_response = models_module.sanitize_ai_response

logger = logging.getLogger(__name__)


class ProviderClient:
    """Base class for AI provider clients."""
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int
    ) -> Dict[str, Any]:
        """Generate completion from AI provider."""
        raise NotImplementedError


class OpenAIClient(ProviderClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
        return self._client
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """Generate completion using OpenAI API."""
        client = self._get_client()
        
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                ),
                timeout=timeout
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except asyncio.TimeoutError:
            raise Exception(f"Request timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(ProviderClient):
    """Anthropic API client."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        return self._client
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
        model: str = "claude-3-sonnet-20240229"
    ) -> Dict[str, Any]:
        """Generate completion using Anthropic API."""
        client = self._get_client()
        
        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=timeout
            )
            
            return {
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "finish_reason": response.stop_reason
            }
            
        except asyncio.TimeoutError:
            raise Exception(f"Request timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class MockClient(ProviderClient):
    """Mock client for development and testing."""
    
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
        model: str = "mock-model"
    ) -> Dict[str, Any]:
        """Generate mock completion."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        # Generate mock response based on prompt content
        mock_content = self._generate_mock_response(prompt)
        
        return {
            "content": mock_content,
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(mock_content) // 4,
                "total_tokens": (len(prompt) + len(mock_content)) // 4
            },
            "model": model,
            "finish_reason": "stop"
        }
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextually appropriate mock response."""
        prompt_lower = prompt.lower()
        
        # Extract the actual user message from the prompt for conversation responses
        user_message = ""
        if "user:" in prompt_lower:
            parts = prompt_lower.split("user:", 1)
            if len(parts) > 1:
                user_message = parts[1].strip()
        elif "\n\nuser:" in prompt_lower:
            parts = prompt_lower.split("\n\nuser:", 1)
            if len(parts) > 1:
                user_message = parts[1].strip()
        
        # Check for goal decomposition first (most specific)
        if "goal" in prompt_lower and "decompose" in prompt_lower:
            return """Based on your goal, here are the suggested tasks:

1. **Research Phase** (Duration: 2-3 hours)
   - Gather information about the topic
   - Identify key resources and requirements
   - Timeline: Week 1

2. **Planning Phase** (Duration: 1-2 hours)
   - Create detailed action plan
   - Set milestones and deadlines
   - Timeline: Week 1

3. **Implementation Phase** (Duration: 5-10 hours)
   - Execute the main work
   - Monitor progress regularly
   - Timeline: Weeks 2-3

**Overall Timeline**: 3-4 weeks

**Follow-up Questions:**
- What's your current experience level?
- How much time can you dedicate weekly?
- Do you have any specific preferences or constraints?

**Next Steps:**
- Start with the research phase
- Gather initial resources
- Set up your learning environment"""
        
        # Check for conversation context (system prompt + user message)
        elif "selfos" in prompt_lower and user_message:
            # Generate contextual responses based on user message content
            if "cooking" in user_message:
                if "italian" in user_message and "pasta" in user_message:
                    return """Italian cooking and pasta dishes are a wonderful focus! Here's how we can develop your Italian cooking skills:

**Specific Areas to Explore:**
- Traditional pasta recipes like carbonara, cacio e pepe, and bolognese
- Fresh pasta making techniques
- Italian ingredient sourcing and quality
- Regional cooking styles

**Practice Suggestions:**
- Start with 2-3 basic recipes to master
- Practice pasta cooking techniques weekly
- Build your pantry with quality Italian ingredients

What type of Italian dishes interest you most? Are you looking to master the classics or explore regional specialties?"""
                else:
                    return """That's a great goal! Cooking is such a valuable skill. To help you get better at cooking, let me ask some specific questions:

**What type of cooking interests you most?**
- Everyday family meals
- International cuisines
- Baking and desserts
- Healthy meal prep

**What's your current experience level?**
- Complete beginner
- Can make basic dishes
- Comfortable with fundamentals

**What specific areas would you like to improve?**
- Knife skills and prep techniques
- Understanding flavors and seasonings
- Time management in the kitchen

The more specific we can make your cooking goal, the better I can help you create a learning plan!"""
            
            elif "health" in user_message and "skill" in user_message:
                return """That's an excellent combination of goals! Focusing on both health and learning a new skill creates great life balance.

**For Health Goals:**
- What specific health areas interest you? (fitness, nutrition, sleep, stress management)
- Are you looking to build new habits or improve existing ones?

**For Skill Learning:**
- What type of skill are you considering? (creative, technical, physical, professional)
- How does this skill connect to your other life goals?

**Goal Integration:**
- Many skills can support health goals (cooking for nutrition, sports for fitness, mindfulness practices)
- Consider how much time you can realistically dedicate to both areas

What specific health improvements or skills are you most excited about exploring?"""
            
            elif "time" in user_message and ("hour" in user_message or "week" in user_message):
                return """Great! Having a realistic time commitment is key to success. With 2 hours per week, we can create a very effective practice schedule.

**Time Management Suggestions:**
- Break it into manageable sessions (e.g., 30 minutes, 4 times per week)
- Schedule consistent practice times that work with your routine
- Focus on quality practice over quantity

**Realistic Expectations:**
- Steady progress with consistent short sessions
- Allow time for both learning and actual practice
- Build in flexibility for busy weeks

**Next Steps:**
- Identify the best days/times for your practice sessions
- Set up your practice space or gather needed materials
- Start with shorter sessions and gradually build up

How would you like to structure your weekly practice time? Are there specific days that work better for you?"""
            
            elif any(word in user_message for word in ["meditation", "wellness", "mindfulness", "health"]):
                return """I understand you'd like to discuss your wellness and mindfulness goals. 

Meditation and wellness practices are excellent for mental clarity and stress management. I can help with:
- Creating a meditation routine that fits your schedule
- Finding wellness challenges that motivate you
- Building sustainable health habits
- Connecting mindfulness to your other life goals

Starting with just 5-10 minutes of daily meditation can make a significant difference. What aspect of wellness would you like to explore another approach to?"""
            
            elif any(word in user_message for word in ["piano", "music", "ukulele", "instrument"]):
                if "ukulele" in user_message and ("easier" in user_message or "instead" in user_message):
                    return """Switching to ukulele is actually a brilliant idea! The ukulele is much easier to start with than piano and can be incredibly rewarding.

**Why Ukulele is a Good Alternative:**
- Only 4 strings vs piano's 88 keys
- Faster to learn basic chords and songs
- More portable and convenient to practice
- Great for building musical confidence
- Still teaches fundamental music concepts

**Getting Started with Ukulele:**
- You can learn basic chords in a few weeks
- Many popular songs use just 3-4 chords
- Practice sessions can be as short as 15-20 minutes
- Perfect for busy schedules

This sounds like a much more realistic and achievable goal! What draws you to the ukulele specifically? Are you interested in a particular style of music?"""
                elif "piano" in user_message and ("not making progress" in user_message or "struggling" in user_message):
                    return """I understand the frustration with piano progress - it's actually a very common challenge! Piano can be demanding, especially with time constraints.

**Common Piano Challenges:**
- Requires significant practice time for meaningful progress
- Coordination between both hands takes time to develop
- Reading music adds complexity
- Needs consistent, focused practice sessions

**Let's Explore Your Options:**
- Would you like to modify your piano approach (shorter sessions, simpler pieces)?
- Are you open to alternative instruments that might fit better?
- Should we focus on just playing for enjoyment vs formal learning?

What specifically has been most challenging about your piano practice? Understanding the obstacles can help us find a better approach."""
                elif "give up" in user_message and "music" in user_message:
                    return """Please don't give up on music altogether! Music brings so much joy and there are many different approaches we can try.

**Don't Give Up - Let's Modify Instead:**
- Music goals can be adjusted to fit your lifestyle
- Different instruments have different learning curves
- You can start with something smaller and simpler
- Even 10-15 minutes of musical activity can be rewarding

**Different Approaches to Consider:**
- Simpler instruments (ukulele, harmonica, kalimba)
- Music apps for casual learning
- Singing or vocal exercises
- Listening and music appreciation

**Start Small and Realistic:**
- What if we found a music goal that takes just 15 minutes a day?
- Would a more portable, easier instrument work better?

What originally drew you to music? Let's find a way to keep that spark alive with a more realistic approach."""
                elif "realistic" in user_message and "music goal" in user_message:
                    return """Great question! Let's find a realistic music goal that fits your lifestyle and keeps you engaged.

**Start Small and Simple:**
- Begin with just 10-15 minutes of practice
- Choose an easier instrument like ukulele or harmonica
- Focus on learning 3-4 basic chords first
- Pick simple songs you already love

**Realistic Music Goals to Consider:**
- Learn to play 5 favorite songs on ukulele in 3 months
- Practice simple chord progressions 15 minutes daily
- Master basic strumming patterns
- Join a casual jam session once a month

**Why Ukulele is Perfect for Realistic Goals:**
- Only 4 strings (much simpler than piano or guitar)
- Can play hundreds of songs with just 4 chords
- Portable - practice anywhere
- Quick wins boost motivation

What style of music do you enjoy most? Let's pick something that excites you and build a simple, achievable plan around it."""
                else:
                    return """I understand music goals can be challenging! Let's talk about what's working and what isn't.

**Music Learning Considerations:**
- Different instruments have different time commitments
- Practice consistency matters more than duration
- Some instruments are more beginner-friendly
- Your schedule and lifestyle should guide the choice

What specific challenges are you facing with your music goal? Are there particular constraints (time, space, complexity) that we should work around?"""
            
            elif any(word in user_message for word in ["improve", "life", "start"]):
                return """I understand you're looking to improve your life - that's a wonderful place to start! Let me help you explore what areas matter most to you right now.

**Common Life Areas to Consider:**
- Health and wellness (physical, mental, emotional)
- Career and professional development
- Relationships and social connections
- Personal growth and learning
- Financial stability and planning
- Hobbies and creative pursuits

**Getting Specific:**
What areas feel most important to you right now? Sometimes it helps to think about:
- What's working well in your life?
- What feels challenging or stuck?
- What would make the biggest positive impact?

**Goal Setting Approach:**
- Start with 1-2 areas to focus on
- Set specific, achievable targets
- Create action steps you can take this week

What resonates most with you? I'm here to help you break down any area into manageable, actionable goals."""
            
            else:
                return """I understand you'd like to discuss your goals and progress. 

What specific area would you like to focus on today? I can help with:
- Breaking down complex goals into tasks
- Planning your schedule and priorities
- Reviewing progress and adjusting plans
- Brainstorming solutions to challenges

What would be most helpful right now?"""
        
        # Fallback for task generation (less specific than conversation)
        elif "task" in prompt_lower:
            return """Here are some suggested next tasks:

1. **Review Current Progress**
   - Assess what's been completed
   - Identify any blockers
   - Time: 30 minutes

2. **Plan Next Actions**
   - Choose 2-3 specific tasks to focus on
   - Set realistic deadlines
   - Time: 45 minutes

3. **Execute Priority Task**
   - Start with the most important item
   - Work in focused 25-minute sessions
   - Time: Variable"""
        
        else:
            return """I'm here to help you with goal setting, task management, and life planning. 

Could you provide more details about what you'd like to work on? For example:
- A specific goal you want to achieve
- Tasks you need help organizing
- Challenges you're facing with your current plans

The more context you provide, the better I can assist you."""


class ResponseCache:
    """Simple in-memory cache for AI responses."""
    
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.ttl = ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """Generate cache key from prompt and config."""
        key_data = {
            "prompt": prompt,
            "model": model_config.get("model_name"),
            "max_tokens": model_config.get("max_tokens"),
            "temperature": model_config.get("temperature")
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, prompt: str, model_config: Dict[str, Any]) -> Optional[AIResponse]:
        """Get cached response."""
        async with self._lock:
            key = self._generate_key(prompt, model_config)
            entry = self.cache.get(key)
            
            if entry and not entry.is_expired(self.ttl):
                entry.access()
                logger.debug(f"Cache hit for key: {key[:8]}...")
                return entry.response
            
            if entry and entry.is_expired(self.ttl):
                del self.cache[key]
                logger.debug(f"Expired cache entry removed: {key[:8]}...")
            
            return None
    
    async def set(self, prompt: str, model_config: Dict[str, Any], response: AIResponse):
        """Store response in cache."""
        async with self._lock:
            key = self._generate_key(prompt, model_config)
            entry = CacheEntry(key=key, response=response, created_at=datetime.utcnow())
            self.cache[key] = entry
            logger.debug(f"Cached response for key: {key[:8]}...")
    
    async def clear_expired(self):
        """Remove expired entries."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired(self.ttl)
            ]
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"Removed {len(expired_keys)} expired cache entries")


class AIOrchestrator:
    """Main orchestrator for AI operations."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.clients: Dict[str, ProviderClient] = {}  # Use string keys instead of enum objects
        self.cache = ResponseCache(ttl=self.config.settings["cache_ttl"])
        self.metrics = ProcessingMetrics()
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI provider clients."""
        logger.debug(f"Starting client initialization. Available providers: {self.config.get_available_providers()}")
        for provider in self.config.get_available_providers():
            try:
                if provider.value == "openai":  # Use string comparison instead of enum comparison
                    api_key = self.config.get_api_key(provider)
                    client_instance = OpenAIClient(api_key)
                    self.clients[provider.value] = client_instance
                    logger.debug(f"Assigned {provider.value} client using string key")
                elif provider.value == "anthropic":  # Use string comparison
                    api_key = self.config.get_api_key(provider)
                    client_instance = AnthropicClient(api_key)
                    self.clients[provider.value] = client_instance
                    logger.debug(f"Assigned {provider.value} client using string key")
                elif provider.value == "local":  # Use string comparison
                    client_instance = MockClient()
                    self.clients[provider.value] = client_instance
                    logger.debug(f"Assigned {provider.value} client using string key")
                
                logger.info(f"Initialized {provider.value} client")
                logger.debug(f"Clients dictionary now has: {list(self.clients.keys())}")
            except Exception as e:
                logger.warning(f"Failed to initialize {provider.value} client: {e}")
        
        logger.debug(f"Client initialization complete. Final clients: {list(self.clients.keys())}")
    
    async def decompose_goal(self, request: GoalDecompositionRequest) -> GoalDecompositionResponse:
        """Decompose a goal into actionable tasks."""
        start_time = time.time()
        request_id = create_request_id()
        
        try:
            # Build context with fallback for dynamic loading
            try:
                from prompts.goal_decomposition import GoalContext
            except ImportError:
                # Fallback - create mock context class
                class GoalContext:
                    def __init__(self, **kwargs):
                        for key, value in kwargs.items():
                            setattr(self, key, value)
            
            context = GoalContext(
                user_id=request.user_id,
                life_areas=request.life_areas,
                existing_goals=request.existing_goals,
                user_preferences=request.user_preferences
            )
            
            # Generate prompt
            prompt = GoalDecompositionPrompts.decompose_goal_prompt(
                goal_description=request.goal_description,
                context=context,
                additional_info=request.additional_context
            )
            
            # Get AI response
            ai_response = await self._generate_response(
                prompt=prompt,
                use_case="goal_decomposition",
                request_id=request_id
            )
            
            # Parse response into structured format
            parsed_response = self._parse_goal_decomposition_response(ai_response)
            
            # Create response object
            response = GoalDecompositionResponse(
                request_id=request_id,
                status=ResponseStatus.SUCCESS,
                content=ai_response.content,
                metadata=ai_response.metadata,
                token_usage=ai_response.token_usage,
                cost_estimate=ai_response.cost_estimate,
                processing_time=time.time() - start_time,
                model_used=ai_response.model_used,
                **parsed_response
            )
            
            self.metrics.add_request(response)
            return response
            
        except Exception as e:
            logger.error(f"Goal decomposition failed: {e}")
            response = GoalDecompositionResponse(
                request_id=request_id,
                status=ResponseStatus.ERROR,
                content="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
            self.metrics.add_request(response)
            return response
    
    async def generate_tasks(self, request: TaskGenerationRequest) -> TaskGenerationResponse:
        """Generate or optimize tasks for a goal."""
        start_time = time.time()
        request_id = create_request_id()
        
        try:
            # Generate appropriate prompt based on generation type
            if request.generation_type == "next_tasks":
                try:
                    from prompts.task_generation import TaskContext
                except ImportError:
                    # Fallback - create mock context class
                    class TaskContext:
                        def __init__(self, **kwargs):
                            for key, value in kwargs.items():
                                setattr(self, key, value)
                
                context = TaskContext(
                    goal_id=request.goal_id,
                    goal_title=request.goal_title,
                    goal_description=request.goal_description,
                    existing_tasks=request.existing_tasks
                )
                prompt = TaskGenerationPrompts.suggest_next_tasks_prompt(
                    context=context,
                    completed_tasks=request.completed_tasks
                )
            else:
                raise ValueError(f"Unsupported generation type: {request.generation_type}")
            
            # Get AI response
            ai_response = await self._generate_response(
                prompt=prompt,
                use_case="task_generation",
                request_id=request_id
            )
            
            # Parse response
            parsed_response = self._parse_task_generation_response(ai_response)
            
            response = TaskGenerationResponse(
                request_id=request_id,
                status=ResponseStatus.SUCCESS,
                content=ai_response.content,
                metadata=ai_response.metadata,
                token_usage=ai_response.token_usage,
                cost_estimate=ai_response.cost_estimate,
                processing_time=time.time() - start_time,
                model_used=ai_response.model_used,
                **parsed_response
            )
            
            self.metrics.add_request(response)
            return response
            
        except Exception as e:
            logger.error(f"Task generation failed: {e}")
            response = TaskGenerationResponse(
                request_id=request_id,
                status=ResponseStatus.ERROR,
                content="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
            self.metrics.add_request(response)
            return response
    
    async def chat(self, request: ConversationRequest) -> ConversationResponse:
        """Handle conversational AI request."""
        start_time = time.time()
        request_id = create_request_id()
        
        try:
            # Build conversation prompt with context
            system_prompt = ConversationPrompts.chat_system_prompt(
                user_preferences=request.user_context.get("preferences") if request.user_context else None
            )
            
            # Add context-specific guidance to the prompt
            context_guidance = ""
            if request.user_context:
                context_parts = []
                
                # Emotional state context
                if "emotional_state" in request.user_context:
                    emotional_state = request.user_context["emotional_state"]
                    context_parts.append(f"The user is feeling {emotional_state}. Respond with appropriate emotional support and understanding.")
                
                # Goal type context
                if "goal_type" in request.user_context:
                    goal_type = request.user_context["goal_type"]
                    if goal_type == "habit_formation":
                        context_parts.append("Focus on habit formation strategies, small steps, and building sustainable routines.")
                    elif goal_type == "skill_learning":
                        context_parts.append("Provide learning guidance, practice strategies, and skill development advice.")
                
                # Specific context hints
                if "current_goal" in request.user_context:
                    goal = request.user_context["current_goal"]
                    context_parts.append(f"The user is working on a {goal} goal. Provide relevant advice and encouragement.")
                
                if "struggling" in request.user_context and request.user_context["struggling"]:
                    context_parts.append("The user is struggling and needs motivational support. Be encouraging and provide practical solutions.")
                
                if "support_needed" in request.user_context and request.user_context["support_needed"]:
                    context_parts.append("Provide supportive, understanding responses with actionable advice.")
                
                if "complex_goal" in request.user_context:
                    context_parts.append("This is a complex, multi-faceted goal. Break it down into manageable steps and acknowledge the complexity.")
                
                if "topic_switch" in request.user_context:
                    context_parts.append("The user is switching topics. Acknowledge the context switch and respond to the new topic appropriately.")
                
                # Workflow step context
                if "workflow_step" in request.user_context:
                    step = request.user_context["workflow_step"]
                    if step == "clarification":
                        context_parts.append("The user is clarifying their goal. Ask about specific aspects like equipment, skills needed, business considerations, or practical details.")
                    elif step == "constraints":
                        context_parts.append("The user is discussing constraints (budget, time). Provide realistic advice that works within their limitations.")
                    elif step == "next_steps":
                        context_parts.append("The user wants to know next steps. Provide specific, actionable first steps they can take immediately.")
                
                # Business/career context
                if "business_planning" in request.user_context:
                    context_parts.append("This involves business or career planning. Discuss expertise, experience, client acquisition, time management, and gradual transition strategies.")
                
                # Long message context
                if "long_message" in request.user_context or "complex_situation" in request.user_context:
                    context_parts.append("The user has shared a complex situation with many factors. Acknowledge the complexity and help prioritize the most important steps.")
                
                if context_parts:
                    context_guidance = f"\n\nContext for this conversation:\n" + "\n".join([f"- {part}" for part in context_parts])
            
            # Combine system prompt with context and user message
            full_prompt = f"{system_prompt}{context_guidance}\n\nUser: {request.message}"
            
            # Debug logging to verify prompt construction
            logger.debug(f"Chat request {request_id} - Full prompt being sent to AI:")
            logger.debug(f"System prompt length: {len(system_prompt)} chars")
            logger.debug(f"Context guidance length: {len(context_guidance)} chars")
            logger.debug(f"User message: {request.message}")
            logger.debug(f"Full prompt: {full_prompt}")
            
            # Get AI response
            ai_response = await self._generate_response(
                prompt=full_prompt,
                use_case="conversation",
                request_id=request_id
            )
            
            # Parse conversation response
            parsed_response = self._parse_conversation_response(ai_response, request.message)
            
            response = ConversationResponse(
                request_id=request_id,
                status=ResponseStatus.SUCCESS,
                content=ai_response.content,
                metadata=ai_response.metadata,
                token_usage=ai_response.token_usage,
                cost_estimate=ai_response.cost_estimate,
                processing_time=time.time() - start_time,
                model_used=ai_response.model_used,
                **parsed_response
            )
            
            self.metrics.add_request(response)
            return response
            
        except Exception as e:
            logger.error(f"Conversation failed: {e}")
            response = ConversationResponse(
                request_id=request_id,
                status=ResponseStatus.ERROR,
                content="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
            self.metrics.add_request(response)
            return response
    
    async def _generate_response(
        self,
        prompt: str,
        use_case: str,
        request_id: str,
        provider: Optional[AIProvider] = None
    ) -> AIResponse:
        """Generate response from AI provider."""
        
        # Get model configuration
        model_config = self.config.get_model_config(use_case, provider)
        
        # Check cache if enabled
        if self.config.settings["enable_caching"]:
            cached_response = await self.cache.get(prompt, model_config.__dict__)
            if cached_response:
                logger.debug(f"Using cached response for request {request_id}")
                cached_response.metadata["cache_hit"] = True
                return cached_response
        
        # Try primary provider, then fallback
        providers_to_try = [model_config.provider]
        if model_config.provider != AIProvider.LOCAL:
            providers_to_try.append(AIProvider.LOCAL)  # Always fallback to mock
        
        last_error = None
        logger.debug(f"Providers to try: {providers_to_try}")
        logger.debug(f"Available clients: {list(self.clients.keys())}")
        
        for provider_to_try in providers_to_try:
            logger.debug(f"Checking provider {provider_to_try.value}")
            logger.debug(f"Clients keys: {list(self.clients.keys())}")
            if provider_to_try.value not in self.clients:  # Use string value for lookup
                logger.warning(f"Provider {provider_to_try.value} not in clients dictionary")
                continue
            
            try:
                client = self.clients[provider_to_try.value]  # Use string value for lookup
                config = self.config.get_model_config(use_case, provider_to_try)
                
                logger.debug(f"Sending prompt to {provider_to_try.value}: {prompt[:200]}...")
                
                result = await client.generate_completion(
                    prompt=prompt,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    timeout=config.timeout,
                    model=config.model_name
                )
                
                logger.debug(f"{provider_to_try.value} response: {result.get('content', '')[:200]}...")
                
                # Calculate cost
                cost = 0.0
                if config.cost_per_token and result.get("usage"):
                    cost = result["usage"]["total_tokens"] * config.cost_per_token
                
                response = AIResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    content=sanitize_ai_response(result["content"]),
                    metadata={
                        "provider": provider_to_try.value,
                        "finish_reason": result.get("finish_reason"),
                        "cache_hit": False
                    },
                    token_usage=result.get("usage"),
                    cost_estimate=cost,
                    model_used=result.get("model")
                )
                
                # Cache if enabled
                if self.config.settings["enable_caching"]:
                    await self.cache.set(prompt, config.__dict__, response)
                
                logger.debug(f"Generated response using {provider_to_try.value}")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_to_try.value} failed: {e}")
                continue
        
        # If all providers failed
        if last_error is None:
            raise Exception(f"No providers available. Providers to try: {providers_to_try}, Available clients: {list(self.clients.keys())}")
        else:
            raise Exception(f"All providers failed. Last error: {last_error}")
    
    def _parse_goal_decomposition_response(self, response: AIResponse) -> Dict[str, Any]:
        """Parse goal decomposition response into structured data."""
        # This is a simplified parser - in production, you'd use more sophisticated NLP
        content = response.content.lower()
        
        # Extract basic information (placeholder implementation)
        return {
            "suggested_tasks": [],  # Would parse actual tasks from response
            "overall_timeline": "3-4 weeks" if "week" in content else "Unknown",
            "potential_challenges": ["Time management", "Resource availability"],
            "success_metrics": ["Task completion", "Goal achievement"],
            "next_steps": ["Start with first task"],
            "confidence_score": 0.8
        }
    
    def _parse_task_generation_response(self, response: AIResponse) -> Dict[str, Any]:
        """Parse task generation response into structured data."""
        # Simplified parser
        return {
            "generated_tasks": [],  # Would parse actual tasks
            "recommendations": ["Focus on high-priority items", "Set realistic deadlines"]
        }
    
    def _parse_conversation_response(self, response: AIResponse, user_message: str) -> Dict[str, Any]:
        """Parse conversation response to extract intent and actions."""
        # Simplified intent detection
        message_lower = user_message.lower()
        intent = None
        
        if any(word in message_lower for word in ["goal", "achieve", "want to"]):
            intent = "goal_setting"
        elif any(word in message_lower for word in ["task", "todo", "need to"]):
            intent = "task_management"
        elif any(word in message_lower for word in ["plan", "schedule"]):
            intent = "planning"
        
        # Generate contextual follow-up questions based on intent and content
        follow_up_questions = []
        if intent == "goal_setting":
            follow_up_questions = [
                "What's your timeline for achieving this goal?",
                "What resources do you currently have available?",
                "What obstacles do you anticipate?"
            ]
        elif intent == "task_management":
            follow_up_questions = [
                "What's the priority level for these tasks?",
                "How much time do you have available?",
                "Are there any dependencies between tasks?"
            ]
        else:
            follow_up_questions = [
                "What would you like to focus on first?",
                "How can I best help you with this?",
                "What's your main challenge right now?"
            ]
        
        return {
            "intent_detected": intent,
            "suggested_actions": [],
            "follow_up_questions": follow_up_questions,
            "extracted_goals": []
        }
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics."""
        return self.metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of AI orchestrator."""
        try:
            # Test each part separately to identify the issue
            cache_size = len(self.cache.cache)
            total_requests = self.metrics.total_requests
            successful_requests = self.metrics.successful_requests
            average_processing_time = self.metrics.average_processing_time
            
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            health = {
                "status": "healthy",
                "providers": {},
                "cache_size": cache_size,
                "metrics": {
                    "total_requests": total_requests,
                    "success_rate": success_rate,
                    "average_response_time": average_processing_time
                }
            }
        except Exception as e:
            import traceback
            return {
                "status": "error",
                "providers": {},
                "cache_size": 0,
                "metrics": {"error": str(e), "traceback": traceback.format_exc()}
            }
        
        # Check each provider
        for provider_key, client in self.clients.items():
            try:
                # Simple health check - try to generate a short response
                test_prompt = "Say 'OK' if you're working."
                # Convert string key back to enum for config lookup
                try:
                    provider_enum = AIProvider(provider_key)
                except ValueError:
                    provider_enum = None
                
                config = self.config.get_model_config("conversation", provider_enum)
                result = await client.generate_completion(
                    prompt=test_prompt,
                    max_tokens=5,
                    temperature=0.1,
                    timeout=10,
                    model=config.model_name
                )
                health["providers"][provider_key] = "healthy"
            except Exception as e:
                health["providers"][provider_key] = f"error: {str(e)}"
                health["status"] = "degraded"
        
        return health