"""
TutoBot - Main Entry Point (Refactored)
Uses TutoBotOrchestrator class with evaluation loops
"""

import asyncio
import argparse
import json
from typing import Dict, List, Any, Optional

from agents import TutoBot

async def test_planner(spreadsheet_id: str, teacher_input: Dict[str, Any]):
    """Test Planner agent with evaluation loop"""
    tut = TutoBot(spreadsheet_id)
    
    teacher_input['spreadsheet_id'] = spreadsheet_id
    result = await tut.run_with_evaluation(generator_name="planner", input_data=teacher_input, content_type="curriculum", max_iterations=3)
    
    print("\n" + "="*60)
    print("CURRICULUM PLANNING RESULT")
    print("="*60)
    print(f"Iterations: {result['iterations']}")
    print(f"Quality Score: {result['evaluation']['quality_score']}/100")
    print(f"Status: {result['evaluation']['status']}")
    print("\nCurriculum:")
    print(json.dumps(result['content'], indent=2))


async def test_lesson(spreadsheet_id: str, folder_id: str, teacher_input: Dict[str, Any]):
    """Test Lesson agent with evaluation loop"""
    tut = TutoBot(spreadsheet_id, folder_id)
    
    # First generate curriculum
    teacher_input['folder_id'] = folder_id
    teacher_input['spreadsheet_id'] = spreadsheet_id
    curriculum_result = await tut.run_agent("planner", teacher_input)
    
    # Then test lesson generation
    lesson_input = {**teacher_input, 'curriculum': curriculum_result.get('curriculum', []), 'week_number': 1}
    result = await tut.run_with_evaluation(generator_name="lesson", input_data=lesson_input, content_type="lesson", max_iterations=3)
    
    print("\n" + "="*60)
    print("LESSON DESIGN RESULT")
    print("="*60)
    print(f"Iterations: {result['iterations']}")
    print(f"Quality Score: {result['evaluation']['quality_score']}/100")
    print(f"Status: {result['evaluation']['status']}")


def main():
    parser = argparse.ArgumentParser(description="TutoBot - AI Lesson Planning Agent (Refactored)")
    parser.add_argument("--mode", choices=["full", "planner", "lesson"], default="planner", help="Run mode: full pipeline, planner only, or lesson only")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID (share with service account)")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID (share with service account)")
    parser.add_argument("--board", default="SSC", choices=["SSC", "CBSE", "ICSE", "IGCSE"], help="Education board")
    parser.add_argument("--grade", type=int, default=5, choices=range(1, 13), help="Student grade (1-12)")
    parser.add_argument("--subject", default="Mathematics", help="Subject to teach")
    parser.add_argument("--weeks", type=int, default=2, help="Duration in weeks")
    parser.add_argument("--goals", default="Master fractions and decimals", help="Learning goals")
    
    args = parser.parse_args()
    
    teacher_input = {
        "board": args.board,
        "grade": args.grade,
        "subject": args.subject,
        "duration_weeks": args.weeks,
        "learning_goals": args.goals
    }
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                   🎓 TutoBot Starting 🎓                     ║
╟──────────────────────────────────────────────────────────────╢
║  Board:     {args.board:<48} ║
║  Grade:     {args.grade:<48} ║
║  Subject:   {args.subject:<48} ║
║  Duration:  {args.weeks} weeks{' ' * (44 - len(str(args.weeks)))}║
║  Sheet ID:  {args.spreadsheet_id[:20]}...{' ' * 27}║
║  Mode:      {args.mode:<48} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.mode == "full":
        print("\n🚀 Running FULL PIPELINE (with evaluation loops)...\n")
        tutobot = TutoBot(args.spreadsheet_id, args.folder_id)
        asyncio.run(tutobot.run_full_pipeline(teacher_input))
    
    elif args.mode == "planner":
        print("\n🧠 Testing PLANNER AGENT (with evaluation loop)...\n")
        asyncio.run(test_planner(args.spreadsheet_id, teacher_input))
    
    elif args.mode == "lesson":
        print("\n📚 Testing LESSON AGENT (with evaluation loop)...\n")
        asyncio.run(test_lesson(args.spreadsheet_id, args.folder_id, teacher_input))
    
    print("\n✅ TutoBot execution complete! Check your Google Sheet for results.")


if __name__ == "__main__":
    main()
