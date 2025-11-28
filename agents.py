"""
TutoBot Agent System (Refactored)
Multi-agent orchestration with evaluation loops and explicit session management
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
# from google.adk.tools import FunctionTool
from google.adk.models.google_llm import Gemini
from google.genai import types

from prompts import get_prompt
from tools import (
    sheets_read, sheets_write, sheets_append,
    search_ncert_content, create_google_doc, create_google_form,
    get_all_tools
)

# ========== Configuration ==========
# MODEL_ID = "gemini-2.5-flash-lite"
MODEL_ID = "gemini-2.5-flash"
QUALITY_THRESHOLD = 70  # Minimum quality score for approval

# ========== TutoBot Orchestrator ==========

def parse_json(text):
    txt_start = text.find('```') + 3
    txt_end = text.find('```', txt_start)
    text = text[txt_start:txt_end+1]
    json_str = text[text.find('{'):text.rfind('}')+1] # get json
    # json_str = ''.join(c for c in json_str if ord(c) >= 32 or c in '\n\r').replace('\u2011', '-') # clean chars
    # json_str = ' '.join(json_str.split())
    return json.loads(json_str.strip())

class TutoBot:
    """
    Main tut for TutoBot agent system.
    Manages agents, sessions, tools, and execution flow.
    """
    
    def __init__(self, spreadsheet_id, folder_id, service_account_file = '../service_account.json'):
        """
        Initialize TutoBot orchestrator
        
        Args:
            spreadsheet_id: Google Sheets ID for state storage
            service_account_file: Path to service account JSON
        """
        self.folder_id = folder_id
        self.spreadsheet_id = spreadsheet_id
        self.service_account_file = service_account_file
        
        retry_cfg = types.HttpRetryOptions(attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504])
        self.model = Gemini(model=MODEL_ID, temperature=0.9, top_p=0.95, retry_options=retry_cfg)
        
        # self.session_service = DatabaseSessionService(connection_string=f'sqlite:///tutobot_sessions.db')
        self.session_service = InMemorySessionService()
        
        self.tools = self._create_tools()
        self.agents = self._create_agents()
        self.runners = self._create_runners()
    
    def _create_tools(self) -> Dict[str, Any]:
        """Create all tool instances"""
        return {tool.name: tool for tool in get_all_tools()}
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create all agent instances"""
        agents = {}
        base_config = {'model': self.model}
        
        # === PLANNER AGENT ===
        agents['planner'] = Agent(name="CurriculumPlanner",
            description="Plans multi-week curriculum aligned with Indian education boards",
            instruction=get_prompt('planner'),
            tools=[
                self.tools['search_ncert_content'],
                self.tools['sheets_write']
            ],
            output_key="curriculum",
            **base_config
        )
        
        # === LESSON AGENT ===
        agents['lesson'] = Agent(name="LessonDesigner",
            description="Creates detailed daily lesson plans with activities",
            instruction=get_prompt('lesson'),
            tools=[
                self.tools['sheets_read'],
                self.tools['search_ncert_content'],
                self.tools['create_google_doc'],
                self.tools['sheets_append']
            ],
            output_key="lessons",
            **base_config
        )
        
        # === ASSESSMENT AGENT ===
        agents['assessment'] = Agent(name="AssessmentCreator",
            description="Generates quizzes and tests with auto-grading",
            instruction=get_prompt('assessment'),
            tools=[
                self.tools['sheets_read'],
                self.tools['create_google_form'],
                self.tools['sheets_append']
            ],
            output_key="assessments",
            **base_config
        )
        
        # === EVALUATOR AGENT ===
        agents['evaluator'] = Agent(name="QualityEvaluator",
            description="Validates content quality and alignment with objectives",
            instruction=get_prompt('evaluator'),
            tools=[],
            output_key="evaluation",
            **base_config
        )
        
        # === EXPORT AGENT ===
        agents['export'] = Agent(name="DocumentExporter",
            description="Formats and organizes final materials",
            instruction=get_prompt('export'),
            tools=[
                self.tools['sheets_read'],
                self.tools['create_google_doc'],
                self.tools['sheets_write']
            ],
            output_key="final_summary",
            **base_config
        )
        
        return agents
    
    def _create_runners(self) -> Dict[str, Runner]:
        """Create runners for each agent"""
        runners = {}
        for name, agent in self.agents.items():
            app = App(name=f"TutoBot_{name}", root_agent=agent)
            runners[name] = Runner(app=app, session_service=self.session_service)
        return runners
    
    async def _get_or_create_session(self, app_name: str, session_id: str, user_id: str = "teacher_1"):
        """Get existing session or create new one"""
        try:
            session = await self.session_service.get_session(app_name=app_name, session_id=session_id, user_id=user_id)
            if session is None:
                session = await self.session_service.create_session(app_name=app_name, session_id=session_id, user_id=user_id)
        except Exception as e:
            # If get_session raises an exception, try to create a new session
            print(f"  Warning: get_session failed ({e}), creating new session...")
            session = await self.session_service.create_session(app_name=app_name, session_id=session_id, user_id=user_id)
        if session is None:
            raise RuntimeError(f"Failed to get or create session for app_name={app_name}, session_id={session_id}")
        return session
    
    async def run_agent(self, agent_name: str, input_data: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a single agent with input data
        
        Args:
            agent_name: Name of agent to run
            input_data: Input data dictionary
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Agent output as dictionary
        """
        if session_id is None:
            session_id = f"{agent_name}_{id(input_data)}"
        
        runner = self.runners[agent_name]
        
        # Create or get session
        session = await self._get_or_create_session(app_name=runner.app_name, session_id=session_id)
        
        # Prepare message
        content = types.Content(role='user', parts=[types.Part(text=json.dumps(input_data, ensure_ascii=False))])
        
        # Run agent and collect output
        output_text = ""
        async for event in runner.run_async(user_id="teacher_1", session_id=session.id, new_message=content):
            if event.content and event.content.parts:
            # if event.content and event.content.parts and event.is_final_response():
                for part in event.content.parts:
                    if part.text:
                        output_text += part.text
        
        # Parse JSON output
        try:
            result = parse_json(output_text)
            print(f" JSON OK: {str(result)[:200]}")
        except json.JSONDecodeError as e:
            print(f"??  JSON parse error for {agent_name}: {e}")
            # print(f"Raw output: {output_text[:500]}")
            print(f"Raw output: {output_text}")
            result = {"error": "Failed to parse JSON", "raw_output": output_text}
        
        return result
    
    async def run_with_evaluation(self, generator_name: str, input_data: Dict[str, Any], content_type: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run a generator agent with a universal evaluation loop.
        
        Args:
            generator_name: Name of generator agent
            input_data: Input data for generator
            content_type: Type for logging (e.g., curriculum/lesson)
            max_iterations: Maximum revision cycles
            
        Returns:
            Final approved content
        """
        print(f"\n{'='*60}")
        print(f"Running {generator_name} with Universal Evaluation Loop")
        print(f"{'='*60}")
        
        iteration = 0
        current_input = input_data.copy()
        content = None
        evaluation = None
        
        # Retrieve the original instruction of the generator
        original_instruction = self.agents[generator_name].instruction
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # 1. Run Generator
            print(f"  Generating content with {generator_name}...")
            result = await self.run_agent(generator_name, current_input)
            
            # Handle varied output keys (some agents return wrapped dicts, others might be direct)
            content = result.get(self.agents[generator_name].output_key, result)
            
            # 2. Run Universal Evaluator
            print(f"  Evaluating content...")
            
            # Prepare universal evaluator inputs
            eval_input = {
                "generator_name": generator_name,
                "original_instruction": original_instruction,
                "generator_inputs": input_data,
                "generator_output": result
            }
            
            eval_result = await self.run_agent("evaluator", eval_input)
            evaluation = eval_result.get("evaluation_result", eval_result)
            
            status = evaluation.get("status", "REJECTED")
            score = evaluation.get("quality_score", 0)
            feedback = evaluation.get("feedback", "No feedback provided")
            
            print(f"  Quality Score: {score}/100")
            print(f"  Status: {status}")
            
            # 3. Check for Approval
            if status == "APPROVED":
                print(f"  Content approved!")
                return {"content": content, "evaluation": evaluation, "iterations": iteration}
            
            # 4. Handle Rejection / Suggestions
            if iteration < max_iterations:
                print(f"  !! Content not approved. Sending feedback to generator...")
                print(f"  Feedback: {str(feedback)[:200]}...")
                
                # Integrate suggestions into the inputs for the next iteration
                # We modify the structure of inputs to include the feedback
                current_input["previous_feedback"] = feedback
            else:
                print(f"  Feedback: {str(feedback)[:200]}...")
                print(f"  !! Max iterations reached without full approval.")
                return {"content": content, "evaluation": evaluation, "iterations": iteration,
                    "warning": "Max iterations reached without approval"}
        
        return {"content": content, "evaluation": evaluation, "iterations": iteration}
    
    async def run_full_pipeline(self, teacher_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete TutoBot pipeline with evaluation loops
        
        Args:
            teacher_input: Dictionary with board, grade, subject, duration_weeks, learning_goals
            
        Returns:
            Final output with all generated materials
        """
        print(f"""
==============================================================
                   ?? TutoBot Pipeline                        
--------------------------------------------------------------
  Board:     {teacher_input.get('board', 'N/A'):<48} 
  Grade:     {teacher_input.get('grade', 'N/A'):<48} 
  Subject:   {teacher_input.get('subject', 'N/A'):<48} 
  Duration:  {teacher_input.get('duration_weeks', 'N/A')} weeks{' ' * (44 - len(str(teacher_input.get('duration_weeks', ''))))}
==============================================================
        """)
        
        # Add spreadsheet_id to input
        teacher_input['folder_id'] = self.folder_id
        teacher_input['spreadsheet_id'] = self.spreadsheet_id
        
        results = {}
        
        # === STEP 1: Curriculum Planning with Evaluation ===
        print("\n" + "="*60)
        print("STEP 1: CURRICULUM PLANNING")
        print("="*60)
        
        curriculum_result = await self.run_with_evaluation(generator_name="planner", input_data=teacher_input, content_type="curriculum", max_iterations=3)
        results['curriculum'] = curriculum_result
        
        # === STEP 2: Lesson Design with Evaluation ===
        print("\n" + "="*60)
        print("STEP 2: LESSON DESIGN")
        print("="*60)
        
        # Generate lessons for each week
        curriculum = curriculum_result['content'].get('curriculum', [])
        all_lessons = []
        
        for week in curriculum[:2]:  # Limit to first 2 weeks for demo
            week_num = week.get('week', 1)
            lesson_input = {**teacher_input, 'curriculum': curriculum, 'week_number': week_num}
            
            lesson_result = await self.run_with_evaluation(generator_name="lesson", input_data=lesson_input, content_type="lesson", max_iterations=2)
            all_lessons.extend(lesson_result['content'].get('lessons', []))
        
        results['lessons'] = all_lessons
        
        # === STEP 3: Assessment Generation with Evaluation ===
        print("\n" + "="*60)
        print("STEP 3: ASSESSMENT GENERATION")
        print("="*60)
        
        assessment_input = {**teacher_input, 'curriculum': curriculum, 'week_number': 1, 'assessment_type': 'quiz'}
        assessment_result = await self.run_with_evaluation(generator_name="assessment", input_data=assessment_input, content_type="assessment", max_iterations=2)
        results['assessments'] = assessment_result
        
        # === STEP 4: Export (No evaluation needed) ===
        print("\n" + "="*60)
        print("STEP 4: EXPORT & ORGANIZATION")
        print("="*60)
        
        export_input = {
            'curriculum': curriculum_result['content'],
            'lessons': all_lessons,
            'assessments': [assessment_result['content']],
            'spreadsheet_id': self.spreadsheet_id,
            'teacher_info': {
                'board': teacher_input['board'],
                'grade': teacher_input['grade'],
                'subject': teacher_input['subject']
            }
        }
        
        export_result = await self.run_agent("export", export_input)
        results['export'] = export_result
        
        print(f"\n{'='*60}")
        print("? PIPELINE COMPLETE")
        print(f"{'='*60}\n")
        
        return results


# ========== Standalone Test Functions ==========


# ========== Example Usage ==========

if __name__ == "__main__":
    # Example teacher input
    sample_input = {
        "board": "SSC",
        "grade": 5,
        "subject": "Mathematics",
        "duration_weeks": 4,
        "learning_goals": "Master fractions and decimals, understand basic operations"
    }
    
    sample_spreadsheet_id = "YOUR_SPREADSHEET_ID_HERE"
    
    print("""
==============================================================
           TutoBot Agent System (Refactored)                  
==============================================================

Usage:

# Test planner with evaluation loop
await test_planner(spreadsheet_id, sample_input)

# Test lesson with evaluation loop  
await test_lesson(spreadsheet_id, sample_input)

# Run full pipeline
tut = TutoBot(spreadsheet_id)
results = await tut.run_full_pipeline(sample_input)
    """)
