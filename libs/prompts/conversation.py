"""
Conversation Prompt Templates

This module contains prompt templates for natural language conversations
about goals, tasks, and life management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class ConversationPrompts:
    """Prompt templates for conversational AI interactions."""
    
    @staticmethod
    def chat_system_prompt(user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """System prompt for general chat conversations about life management."""
        
        tone = "friendly and supportive"
        if user_preferences and user_preferences.get("tone"):
            tone_mapping = {
                "friendly": "friendly and supportive",
                "coach": "direct and motivational, like a personal coach",
                "minimal": "concise and focused on actionable advice",
                "professional": "professional yet warm and helpful"
            }
            tone = tone_mapping.get(user_preferences["tone"], tone)
        
        return f"""You are SelfOS, a conversational AI assistant focused on helping users manage their life goals and tasks effectively.

Your communication style is {tone}. You are knowledgeable about:
- Goal setting and achievement strategies
- Task management and productivity techniques
- Life balance and prioritization
- Motivation and habit formation
- Time management and planning

Key principles:
1. **Listen actively** - Understand the user's context and feelings
2. **Ask clarifying questions** - Help users think through their goals
3. **Provide actionable advice** - Give concrete, practical suggestions
4. **Encourage progress** - Celebrate wins and help with setbacks
5. **Respect boundaries** - Don't be pushy; follow the user's lead
6. **Stay organized** - Help structure thoughts and plans

When users mention goals or tasks:
- Ask about specifics, timelines, and obstacles
- Suggest breaking large goals into smaller steps
- Offer to help create concrete action plans
- Connect new goals to existing life areas when relevant

Response Guidelines:
- When users suggest good ideas (like "working out in the morning"), respond positively with words like "great", "excellent", "smart", or "good idea"
- When users mention specific skills or interests (like "portrait photography", "guitar"), acknowledge them directly and provide relevant advice about equipment, skills, or next steps
- When users are struggling or overwhelmed, use supportive language like "understand", "common", "normal", and offer practical solutions
- For complex goals, acknowledge the complexity and suggest breaking things down into manageable steps
- When discussing habits, focus on small starts, consistency, and building sustainable routines

Keep responses conversational but purposeful. You're here to help users achieve their life goals through better planning and execution."""
    
    @staticmethod
    def check_in_prompt(
        recent_activities: List[Dict[str, Any]],
        pending_tasks: List[Dict[str, Any]],
        user_name: Optional[str] = None
    ) -> str:
        """Generate a prompt for proactive check-ins with users."""
        
        greeting = f"Hi {user_name}!" if user_name else "Hi there!"
        
        activities_text = ""
        if recent_activities:
            activities_text = "I noticed you recently:\n" + "\n".join([
                f"- {activity.get('description', 'Had some activity')}"
                for activity in recent_activities[-3:]  # Last 3 activities
            ])
        
        pending_text = ""
        if pending_tasks:
            urgent_tasks = [t for t in pending_tasks if t.get('due_date')]
            if urgent_tasks:
                pending_text = "\n\nYou have some upcoming tasks:\n" + "\n".join([
                    f"- {task.get('title', 'Untitled task')}"
                    for task in urgent_tasks[:3]
                ])
        
        return f"""{greeting}

{activities_text}
{pending_text}

How are things going with your goals? Is there anything you'd like to work on or discuss today?

I'm here to help with:
- Planning next steps on existing goals
- Breaking down complex tasks
- Adjusting timelines or priorities
- Brainstorming new goals or projects
- Just talking through challenges or wins

What would be most helpful right now?"""
    
    @staticmethod
    def goal_exploration_prompt(initial_idea: str) -> str:
        """Generate a prompt for exploring and clarifying a goal idea."""
        
        return f"""You mentioned wanting to work on: "{initial_idea}"

That sounds interesting! Let me help you explore this goal to make it more concrete and actionable.

A few questions to help us dig deeper:

1. **What does success look like?** How will you know when you've achieved this goal?

2. **Why is this important to you?** What's driving this goal right now?

3. **What's your timeline?** When would you ideally like to accomplish this?

4. **What resources do you have?** Time, money, skills, support, etc.

5. **What obstacles do you anticipate?** What might make this challenging?

6. **How does this fit with your other priorities?** Where does this rank among your current goals?

You don't need to answer all of these at once - just share what comes to mind. We can work through this together to create a clear, achievable plan."""
    
    @staticmethod
    def progress_review_prompt(
        goal: Dict[str, Any],
        completed_tasks: List[Dict[str, Any]],
        challenges: Optional[str] = None
    ) -> str:
        """Generate a prompt for reviewing progress on a goal."""
        
        goal_title = goal.get('title', 'Your goal')
        goal_progress = goal.get('progress', 0)
        
        completed_text = ""
        if completed_tasks:
            completed_text = "Tasks you've completed:\n" + "\n".join([
                f"✓ {task.get('title', 'Completed task')}"
                for task in completed_tasks[-5:]  # Last 5 completed
            ])
        
        challenges_text = f"\n\nChallenges mentioned: {challenges}" if challenges else ""
        
        return f"""Let's review your progress on: {goal_title}

Current progress: {goal_progress}%

{completed_text}
{challenges_text}

Great work on what you've accomplished! Let's reflect on this progress:

1. **What's working well?** What strategies or approaches have been most effective?

2. **What's been challenging?** Are there patterns in what's slowing you down?

3. **How do you feel about the pace?** Are you moving faster or slower than expected?

4. **What have you learned?** Any insights about yourself, the goal, or the process?

5. **What needs adjustment?** Should we modify the approach, timeline, or scope?

Based on your experience so far, what would help you maintain momentum and tackle the next phase?"""
    
    @staticmethod
    def motivation_boost_prompt(
        goal: Dict[str, Any],
        recent_setback: Optional[str] = None
    ) -> str:
        """Generate a motivational prompt to help users overcome challenges."""
        
        goal_title = goal.get('title', 'your goal')
        
        setback_text = ""
        if recent_setback:
            setback_text = f"\n\nI understand you're dealing with: {recent_setback}"
        
        return f"""I can see you're working on {goal_title}, and it sounds like you might be hitting some bumps along the way.{setback_text}

First, remember that challenges are a normal part of any meaningful goal. The fact that you're encountering obstacles means you're pushing yourself and trying something worthwhile.

Let's reframe this situation:

**What you've already accomplished:** Every step forward, no matter how small, is progress. What have you done so far that you can feel good about?

**What this setback teaches:** Often our biggest challenges reveal important information about better approaches or missing resources. What might this experience be telling you?

**Your why:** What originally motivated you to pursue this goal? Sometimes reconnecting with that deeper purpose can reignite your energy.

**Small next step:** What's one tiny action you could take today that would move you forward? It doesn't have to be big - just something to rebuild momentum.

Remember: Progress isn't always linear, and persistence often matters more than perfection. You've got this, and I'm here to help you figure out the next move.

What feels like the most helpful thing to focus on right now?"""
    
    @staticmethod
    def planning_session_prompt(
        available_time: Optional[str] = None,
        current_priorities: List[str] = None
    ) -> str:
        """Generate a prompt for structured planning sessions."""
        
        time_text = f"Available time: {available_time}" if available_time else ""
        
        priorities_text = ""
        if current_priorities:
            priorities_text = "Current priorities:\n" + "\n".join([
                f"- {priority}" for priority in current_priorities
            ])
        
        return f"""Let's do some planning together! I'll help you organize your thoughts and create actionable next steps.

{time_text}
{priorities_text}

We can work on:

**🎯 Goal Planning**
- Setting new goals or refining existing ones
- Breaking down big goals into manageable tasks
- Creating realistic timelines

**📅 Schedule Optimization**
- Planning your week or month
- Balancing different life areas
- Finding time for what matters most

**🚀 Next Actions**
- Identifying immediate next steps
- Clearing blockers and obstacles
- Setting up systems for success

**🔄 Review & Adjust**
- Evaluating current progress
- Adjusting plans based on what you've learned
- Celebrating wins and learning from setbacks

What would be most valuable to focus on in our planning session today?"""
    
    @staticmethod
    def reflection_prompt(
        time_period: str = "week",
        completed_items: List[Dict[str, Any]] = None
    ) -> str:
        """Generate a prompt for reflection and learning."""
        
        period_text = {
            "day": "today",
            "week": "this week", 
            "month": "this month",
            "quarter": "this quarter"
        }.get(time_period, f"this {time_period}")
        
        completed_text = ""
        if completed_items:
            completed_text = f"\nAccomplishments from {period_text}:\n" + "\n".join([
                f"✓ {item.get('title', 'Completed item')}"
                for item in completed_items
            ])
        
        return f"""Let's take a moment to reflect on {period_text}.{completed_text}

Reflection helps us learn, appreciate progress, and improve our approach going forward.

**Looking back:**
1. What went really well? What are you proud of?
2. What was more challenging than expected?
3. What did you learn about yourself or your goals?
4. What would you do differently if you could repeat this period?

**Looking forward:**
1. What insights can you apply going forward?
2. What patterns do you notice in what works vs. what doesn't?
3. How might you adjust your approach or expectations?
4. What support or resources would be helpful?

Take your time with this - there's value in both celebrating wins and learning from challenges. What stands out most to you about {period_text}?"""


class ConversationUtils:
    """Utility functions for conversation management."""
    
    @staticmethod
    def format_context_summary(
        goals: List[Dict[str, Any]],
        recent_tasks: List[Dict[str, Any]],
        life_areas: List[Dict[str, Any]]
    ) -> str:
        """Create a context summary for conversation continuity."""
        
        context_parts = []
        
        if goals:
            active_goals = [g for g in goals if g.get('status') != 'completed']
            if active_goals:
                goal_list = [f"- {g.get('title', 'Untitled goal')}" for g in active_goals[:3]]
                context_parts.append(f"Active goals:\n" + "\n".join(goal_list))
        
        if recent_tasks:
            completed_recently = [t for t in recent_tasks if t.get('status') == 'completed']
            if completed_recently:
                task_list = [f"- {t.get('title', 'Completed task')}" for t in completed_recently[-3:]]
                context_parts.append(f"Recently completed:\n" + "\n".join(task_list))
        
        if life_areas:
            area_list = [area.get('name', 'Unnamed area') for area in life_areas[:4]]
            context_parts.append(f"Life areas: {', '.join(area_list)}")
        
        return "\n\n".join(context_parts) if context_parts else "No recent activity to display."
    
    @staticmethod
    def suggest_conversation_starters() -> List[str]:
        """Provide conversation starter suggestions."""
        return [
            "I want to set a new goal",
            "Help me plan my week",
            "I'm feeling stuck on a project",
            "Let's review my progress",
            "I need motivation to keep going",
            "How can I be more productive?",
            "I want to organize my priorities",
            "Let's break down a big task"
        ]
    
    @staticmethod
    def detect_conversation_intent(user_message: str) -> Dict[str, Any]:
        """Analyze user message to detect intent and extract key information."""
        message_lower = user_message.lower()
        
        intent_keywords = {
            "goal_setting": ["goal", "want to", "achieve", "accomplish", "work on"],
            "task_help": ["task", "todo", "need to do", "break down", "steps"],
            "planning": ["plan", "schedule", "organize", "week", "month"],
            "progress_review": ["progress", "review", "how am i doing", "check in"],
            "motivation": ["stuck", "motivation", "discouraged", "hard", "difficult"],
            "reflection": ["reflect", "think about", "learned", "went well"]
        }
        
        detected_intents = []
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Extract potential goal/task mentions
        goal_indicators = ["want to", "need to", "goal", "achieve", "work on"]
        potential_goals = []
        
        for indicator in goal_indicators:
            if indicator in message_lower:
                # Simple extraction - in practice, you'd use more sophisticated NLP
                parts = message_lower.split(indicator, 1)
                if len(parts) > 1:
                    potential_goals.append(parts[1].strip()[:100])  # Limit length
        
        return {
            "intents": detected_intents,
            "potential_goals": potential_goals,
            "message_length": len(user_message),
            "question_words": ["what", "how", "when", "where", "why", "which"] 
                             if any(q in message_lower for q in ["what", "how", "when", "where", "why", "which"]) else []
        }