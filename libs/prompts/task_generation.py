"""
Task Generation Prompt Templates

This module contains prompt templates for generating and refining tasks,
including smart suggestions and task optimization.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class TaskContext:
    """Context information for task generation."""
    goal_id: int
    goal_title: str
    goal_description: Optional[str]
    existing_tasks: List[Dict[str, Any]]
    life_area: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None


class TaskGenerationPrompts:
    """Prompt templates for AI-powered task generation and management."""
    
    @staticmethod
    def suggest_next_tasks_prompt(
        context: TaskContext,
        completed_tasks: List[Dict[str, Any]],
        max_suggestions: int = 3
    ) -> str:
        """Generate prompt for suggesting next logical tasks."""
        
        completed_text = ""
        if completed_tasks:
            completed_text = "Recently completed tasks:\n" + "\n".join([
                f"- {task.get('title', 'Untitled')}: {task.get('description', 'No description')}"
                for task in completed_tasks[-5:]  # Last 5 completed tasks
            ])
        
        pending_text = ""
        pending_tasks = [t for t in context.existing_tasks if t.get('status') != 'completed']
        if pending_tasks:
            pending_text = "\n\nCurrent pending tasks:\n" + "\n".join([
                f"- {task.get('title', 'Untitled')}: {task.get('status', 'unknown')} status"
                for task in pending_tasks[:5]  # Limit for context
            ])
        
        life_area_text = ""
        if context.life_area:
            life_area_text = f"\n\nLife area: {context.life_area['name']}"
        
        return f"""Goal: {context.goal_title}
{context.goal_description or "No description provided"}
{life_area_text}

{completed_text}
{pending_text}

Based on my progress and current situation, please suggest {max_suggestions} specific next tasks that would help me advance toward this goal. 

For each suggestion, provide:
1. **Task title** (clear and actionable)
2. **Description** (what exactly to do)
3. **Rationale** (why this task now)
4. **Estimated time** (realistic duration)
5. **Dependencies** (what needs to be done first, if anything)

Focus on tasks that:
- Build logically on completed work
- Can be started with current resources
- Have clear success criteria
- Move the goal forward meaningfully"""
    
    @staticmethod
    def optimize_task_sequence_prompt(
        tasks: List[Dict[str, Any]],
        constraints: Optional[str] = None
    ) -> str:
        """Generate prompt for optimizing task order and dependencies."""
        
        tasks_text = ""
        for i, task in enumerate(tasks, 1):
            dependencies = task.get('dependencies', [])
            dep_text = f" (depends on: {', '.join(map(str, dependencies))})" if dependencies else ""
            tasks_text += f"{i}. {task.get('title', 'Untitled')}{dep_text}\n"
            tasks_text += f"   Duration: {task.get('duration', 'unknown')}\n"
            tasks_text += f"   Description: {task.get('description', 'No description')}\n\n"
        
        constraints_text = f"\n\nConstraints: {constraints}" if constraints else ""
        
        return f"""I have these tasks to complete:

{tasks_text}
{constraints_text}

Please help me optimize the sequence and scheduling:

1. **Recommended Order**: Best sequence for maximum efficiency
2. **Parallel Opportunities**: Which tasks can be done simultaneously
3. **Critical Path**: Which tasks are bottlenecks that could delay everything
4. **Batching Suggestions**: Tasks that should be grouped together
5. **Timeline Optimization**: How to minimize total completion time

Consider:
- Task dependencies and prerequisites
- Logical groupings and context switching
- Momentum and motivation factors
- Resource requirements and availability"""
    
    @staticmethod
    def break_down_complex_task_prompt(
        task_title: str,
        task_description: str,
        available_time: Optional[str] = None
    ) -> str:
        """Generate prompt for breaking down a complex task into subtasks."""
        
        time_text = f"\n\nAvailable time: {available_time}" if available_time else ""
        
        return f"""I have this task that feels overwhelming or complex:

**Task**: {task_title}
**Description**: {task_description}
{time_text}

Please help me break this down into smaller, manageable subtasks. For each subtask:

1. **Subtask name** (specific and actionable)
2. **Time estimate** (realistic duration)
3. **What to do** (clear steps)
4. **Success criteria** (how to know it's done)
5. **Required resources** (tools, information, etc.)

Make sure each subtask:
- Can be completed in one focused session
- Has a clear start and end point
- Builds toward the overall task completion
- Feels achievable and not overwhelming

Also suggest:
- **Starting point**: Which subtask to tackle first
- **Quick wins**: Subtasks that will build momentum
- **Preparation**: Any setup needed before starting"""
    
    @staticmethod
    def estimate_task_duration_prompt(
        task_title: str,
        task_description: str,
        user_experience: Optional[str] = None,
        similar_tasks: List[Dict[str, Any]] = None
    ) -> str:
        """Generate prompt for estimating realistic task duration."""
        
        experience_text = f"\n\nMy experience level: {user_experience}" if user_experience else ""
        
        similar_text = ""
        if similar_tasks:
            similar_text = "\n\nSimilar tasks I've completed:\n" + "\n".join([
                f"- {task.get('title', 'Untitled')}: took {task.get('actual_duration', 'unknown')} hours"
                for task in similar_tasks[-3:]  # Last 3 similar tasks
            ])
        
        return f"""I need to estimate how long this task will take:

**Task**: {task_title}
**Description**: {task_description}
{experience_text}
{similar_text}

Please provide:

1. **Base Estimate**: Core time needed for the main work
2. **Buffer Time**: Additional time for unexpected issues (typically 20-50% more)
3. **Total Estimate**: Realistic total time including buffer
4. **Breakdown**: Time allocation for different parts of the task
5. **Factors**: What could make it take longer or shorter

Consider:
- Learning curve if this is new territory
- Potential obstacles and complications
- Need for breaks and mental processing
- Quality standards and revision time
- Dependencies on other people or systems

Be realistic rather than optimistic - it's better to overestimate and finish early."""
    
    @staticmethod
    def suggest_task_improvements_prompt(
        task_title: str,
        task_description: str,
        current_progress: Optional[str] = None,
        challenges: Optional[str] = None
    ) -> str:
        """Generate prompt for improving task definition and approach."""
        
        progress_text = f"\n\nCurrent progress: {current_progress}" if current_progress else ""
        challenges_text = f"\n\nChallenges faced: {challenges}" if challenges else ""
        
        return f"""I'm working on this task and want to improve my approach:

**Task**: {task_title}
**Description**: {task_description}
{progress_text}
{challenges_text}

Please suggest improvements for:

1. **Task Clarity**: How to make the task more specific and actionable
2. **Success Criteria**: Better ways to define "done"
3. **Approach**: More efficient methods or strategies
4. **Resources**: Tools, information, or help that could make this easier
5. **Motivation**: Ways to make the task more engaging or rewarding

Also provide:
- **Quick improvements**: Changes I can implement immediately
- **Process optimization**: Better workflows or sequences
- **Quality enhancement**: Ways to improve the outcome
- **Sustainability**: How to make progress more consistent"""
    
    @staticmethod
    def generate_task_checklist_prompt(
        task_title: str,
        task_description: str,
        complexity_level: str = "medium"
    ) -> str:
        """Generate prompt for creating detailed task checklists."""
        
        return f"""I need a detailed checklist for this task:

**Task**: {task_title}
**Description**: {task_description}
**Complexity**: {complexity_level}

Please create a comprehensive checklist that includes:

**Preparation Phase:**
- [ ] Pre-task setup items
- [ ] Required resources and tools
- [ ] Information gathering needs

**Execution Phase:**
- [ ] Step-by-step action items
- [ ] Quality checkpoints
- [ ] Progress milestones

**Completion Phase:**
- [ ] Final review items
- [ ] Documentation or follow-up needed
- [ ] Cleanup and wrap-up tasks

Make each checklist item:
- Specific and actionable
- Easy to verify as complete
- Logically ordered
- Include estimated time for larger items

The checklist should be detailed enough that someone else could follow it to complete the task successfully."""


class TaskPromptUtils:
    """Utility functions for task-related prompts."""
    
    @staticmethod
    def format_task_list(tasks: List[Dict[str, Any]], include_details: bool = True) -> str:
        """Format a list of tasks for inclusion in prompts."""
        if not tasks:
            return "No tasks provided."
        
        formatted = []
        for i, task in enumerate(tasks, 1):
            title = task.get('title', 'Untitled Task')
            status = task.get('status', 'unknown')
            
            if include_details:
                description = task.get('description', 'No description')
                duration = task.get('duration', 'Not specified')
                formatted.append(f"{i}. **{title}** ({status})\n   {description}\n   Duration: {duration}")
            else:
                formatted.append(f"{i}. {title} ({status})")
        
        return "\n\n".join(formatted) if include_details else "\n".join(formatted)
    
    @staticmethod
    def extract_time_estimates(text: str) -> Dict[str, Any]:
        """Extract time estimates from AI responses."""
        # This is a placeholder for parsing logic
        # In practice, you'd implement proper parsing of time expressions
        import re
        
        patterns = {
            'hours': r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)',
            'minutes': r'(\d+)\s*(?:minutes?|mins?|m)',
            'days': r'(\d+)\s*(?:days?|d)',
            'weeks': r'(\d+)\s*(?:weeks?|w)'
        }
        
        estimates = {}
        for unit, pattern in patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                estimates[unit] = [float(m) for m in matches]
        
        return estimates
    
    @staticmethod
    def validate_task_structure(task_data: Dict[str, Any]) -> List[str]:
        """Validate that a task has required structure."""
        errors = []
        
        required_fields = ['title', 'description']
        for field in required_fields:
            if not task_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Check title length
        title = task_data.get('title', '')
        if len(title) > 200:
            errors.append("Title too long (max 200 characters)")
        
        # Check description length
        description = task_data.get('description', '')
        if len(description) > 2000:
            errors.append("Description too long (max 2000 characters)")
        
        # Validate duration if provided
        duration = task_data.get('duration')
        if duration is not None:
            try:
                duration_int = int(duration)
                if duration_int <= 0 or duration_int > 1440:  # 24 hours max
                    errors.append("Duration must be between 1 and 1440 minutes")
            except (ValueError, TypeError):
                errors.append("Duration must be a valid number")
        
        return errors