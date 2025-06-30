"""
Goal Decomposition Prompt Templates

This module contains prompt templates for breaking down high-level goals 
into actionable tasks and subtasks.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GoalContext:
    """Context information for goal decomposition."""
    user_id: str
    life_areas: List[Dict[str, Any]]
    existing_goals: List[Dict[str, Any]]
    user_preferences: Optional[Dict[str, Any]] = None
    current_date: Optional[str] = None


class GoalDecompositionPrompts:
    """Prompt templates for AI-powered goal decomposition."""
    
    @staticmethod
    def system_prompt(user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Base system prompt for goal decomposition conversations."""
        tone = "friendly and encouraging"
        if user_preferences and user_preferences.get("tone"):
            tone_mapping = {
                "friendly": "friendly and encouraging",
                "coach": "direct and motivational like a personal coach",
                "minimal": "concise and to-the-point",
                "professional": "professional and structured"
            }
            tone = tone_mapping.get(user_preferences["tone"], tone)
        
        return f"""You are SelfOS, an AI life management assistant that helps users break down their goals into actionable tasks. 

Your personality is {tone}. You excel at:
- Breaking down complex goals into smaller, manageable tasks
- Suggesting realistic timelines and milestones
- Considering the user's life context and priorities
- Providing practical, actionable advice
- Identifying potential obstacles and solutions

When decomposing goals:
1. Ask clarifying questions if the goal is vague or too broad
2. Break goals into 3-7 main tasks (not too many to overwhelm)
3. Each task should be specific, measurable, and time-bound when possible
4. Consider dependencies between tasks
5. Suggest appropriate life areas for categorization
6. Estimate realistic timeframes
7. Identify potential challenges and mitigation strategies

Always respond in a structured format that can be easily parsed and converted into tasks."""
    
    @staticmethod
    def decompose_goal_prompt(
        goal_description: str,
        context: GoalContext,
        additional_info: Optional[str] = None
    ) -> str:
        """Generate a prompt for decomposing a specific goal."""
        
        # Format life areas
        life_areas_text = ""
        if context.life_areas:
            areas = [f"- {area['name']}: {area.get('description', 'No description')}" 
                    for area in context.life_areas]
            life_areas_text = f"""
Available Life Areas:
{chr(10).join(areas)}
"""
        
        # Format existing goals
        existing_goals_text = ""
        if context.existing_goals:
            goals = [f"- {goal['title']}: {goal.get('status', 'unknown')} status" 
                    for goal in context.existing_goals[:5]]  # Limit to 5 for context
            existing_goals_text = f"""
User's Existing Goals:
{chr(10).join(goals)}
"""
        
        additional_context = f"\n\nAdditional Information: {additional_info}" if additional_info else ""
        
        current_date = context.current_date or datetime.now().strftime("%Y-%m-%d")
        
        return f"""I want to achieve this goal: "{goal_description}"

Current Date: {current_date}

{life_areas_text}
{existing_goals_text}
{additional_context}

Please help me break this goal down into specific, actionable tasks. For each task, provide:

1. **Task Title**: Clear, action-oriented title
2. **Description**: What exactly needs to be done
3. **Estimated Duration**: How long this task might take
4. **Dependencies**: Which other tasks (if any) should be completed first
5. **Life Area**: Which life area this task belongs to
6. **Timeline**: Suggested timeframe or deadline
7. **Success Criteria**: How to know when this task is complete

Also provide:
- **Overall Timeline**: Realistic timeframe for the entire goal
- **Potential Challenges**: What obstacles might arise
- **Success Metrics**: How to measure progress and success
- **Next Steps**: What should be the very first action to take

Please format your response as a structured breakdown that I can easily follow and track."""
    
    @staticmethod
    def refine_tasks_prompt(
        original_goal: str,
        proposed_tasks: List[Dict[str, Any]],
        user_feedback: str
    ) -> str:
        """Generate a prompt for refining tasks based on user feedback."""
        
        tasks_text = ""
        for i, task in enumerate(proposed_tasks, 1):
            tasks_text += f"""
{i}. **{task.get('title', 'Untitled Task')}**
   - Description: {task.get('description', 'No description')}
   - Duration: {task.get('duration', 'Not specified')}
   - Timeline: {task.get('timeline', 'Not specified')}
"""
        
        return f"""I asked you to help me break down this goal: "{original_goal}"

You suggested these tasks:
{tasks_text}

My feedback: {user_feedback}

Please revise the task breakdown based on my feedback. Maintain the same structured format but adjust:
- Task complexity or granularity
- Timelines and estimates
- Dependencies and ordering
- Any specific concerns I mentioned

Provide the updated task breakdown with explanations for the changes you made."""
    
    @staticmethod
    def suggest_life_area_prompt(
        goal_description: str,
        existing_life_areas: List[Dict[str, Any]]
    ) -> str:
        """Generate a prompt for suggesting appropriate life area categorization."""
        
        areas_text = ""
        if existing_life_areas:
            areas_text = "\n".join([
                f"- {area['name']}: {area.get('description', 'No description')}"
                for area in existing_life_areas
            ])
        
        return f"""I have this goal: "{goal_description}"

My current life areas are:
{areas_text}

Which existing life area would be most appropriate for this goal? Or should I create a new life area?

If suggesting a new life area, please provide:
- Name for the new life area
- Description of what it encompasses
- Why it's distinct from existing areas

Please explain your reasoning briefly."""
    
    @staticmethod
    def estimate_timeline_prompt(
        goal_description: str,
        tasks: List[Dict[str, Any]],
        user_availability: Optional[str] = None
    ) -> str:
        """Generate a prompt for estimating realistic timelines."""
        
        tasks_text = "\n".join([
            f"- {task.get('title', 'Untitled')}: {task.get('duration', 'unknown duration')}"
            for task in tasks
        ])
        
        availability_text = f"\n\nMy availability: {user_availability}" if user_availability else ""
        
        return f"""Goal: {goal_description}

Planned tasks:
{tasks_text}
{availability_text}

Based on these tasks and my availability, please provide:

1. **Realistic Timeline**: Overall timeframe to complete this goal
2. **Milestone Schedule**: Key checkpoints and deadlines
3. **Weekly Breakdown**: How much time per week should be allocated
4. **Buffer Time**: Additional time to account for unexpected delays
5. **Critical Path**: Which tasks are most time-sensitive

Consider that people often underestimate time requirements and that life can be unpredictable."""
    
    @staticmethod
    def identify_obstacles_prompt(
        goal_description: str,
        tasks: List[Dict[str, Any]],
        user_context: Optional[str] = None
    ) -> str:
        """Generate a prompt for identifying potential obstacles and solutions."""
        
        tasks_text = "\n".join([
            f"- {task.get('title', 'Untitled')}"
            for task in tasks
        ])
        
        context_text = f"\n\nMy situation: {user_context}" if user_context else ""
        
        return f"""Goal: {goal_description}

Planned approach:
{tasks_text}
{context_text}

Please help me anticipate potential obstacles and prepare solutions:

1. **Common Challenges**: What typically goes wrong with this type of goal?
2. **Personal Obstacles**: Based on my situation, what specific challenges might I face?
3. **Mitigation Strategies**: How can I prepare for or avoid these obstacles?
4. **Contingency Plans**: What should I do if things don't go as planned?
5. **Warning Signs**: How can I recognize when I'm getting off track?
6. **Recovery Strategies**: How to get back on track if I fall behind

Be realistic about challenges while maintaining an encouraging tone."""


class PromptFormatter:
    """Utility class for formatting prompts with dynamic content."""
    
    @staticmethod
    def format_user_context(
        user_preferences: Optional[Dict[str, Any]] = None,
        life_areas: List[Dict[str, Any]] = None,
        recent_activity: Optional[str] = None
    ) -> str:
        """Format user context for inclusion in prompts."""
        context_parts = []
        
        if user_preferences:
            prefs = []
            if user_preferences.get("tone"):
                prefs.append(f"Communication style: {user_preferences['tone']}")
            if user_preferences.get("default_view"):
                prefs.append(f"Preferred organization: {user_preferences['default_view']}")
            if prefs:
                context_parts.append("Preferences: " + ", ".join(prefs))
        
        if life_areas:
            areas = [area["name"] for area in life_areas[:5]]  # Limit for brevity
            context_parts.append(f"Life areas: {', '.join(areas)}")
        
        if recent_activity:
            context_parts.append(f"Recent activity: {recent_activity}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    @staticmethod
    def clean_response_for_parsing(response: str) -> str:
        """Clean AI response for easier parsing."""
        # Remove markdown formatting
        response = response.replace("**", "").replace("*", "")
        
        # Normalize line endings
        response = response.replace("\r\n", "\n").replace("\r", "\n")
        
        # Remove excessive whitespace
        lines = [line.strip() for line in response.split("\n")]
        response = "\n".join(line for line in lines if line)
        
        return response