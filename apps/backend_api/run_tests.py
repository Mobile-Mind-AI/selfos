#!/usr/bin/env python3
"""
Test runner script for SelfOS Backend API

This script provides an easy way to run tests with various options.
Usage: python run_tests.py [options]
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print stdout
    if result.stdout:
        print(result.stdout)
    
    # Print stderr if there are errors
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_module_by_module():
    """Run tests module by module to avoid test isolation issues"""
    test_modules = [
        "tests/test_main.py",
        "tests/unit/test_auth.py", 
        "tests/unit/test_goals.py",
        "tests/unit/test_tasks.py",
        "tests/unit/test_life_areas.py",
        "tests/unit/test_media_attachments.py",
        "tests/unit/test_user_preferences.py",
        "tests/unit/test_feedback_logs.py",
        "tests/unit/test_story_sessions.py",
        "tests/unit/test_assistant_profiles.py",
        "tests/unit/test_intent_service.py",
        "tests/unit/test_projects.py",
        "tests/integration/test_advanced_chat_scenarios.py",
        "tests/integration/test_ai_integration.py",
        "tests/integration/test_assistant_conversation_integration.py",
        "tests/integration/test_chat_simulation.py",
        "tests/integration/test_integration_goals_and_tasks.py"
    ]
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    failed_modules = []
    
    for module in test_modules:
        cmd = ["python", "-m", "pytest", module, "-v", "--tb=short"]
        description = f"Testing {module}"
        
        success = run_command(cmd, description)
        
        # Extract test counts from output (basic parsing)
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + result.stderr
        
        # Look for the summary line like "5 passed, 1 failed"
        import re
        summary_match = re.search(r'(\d+) failed.*?(\d+) passed|(\d+) passed.*?(\d+) failed|(\d+) passed', output)
        if summary_match:
            groups = summary_match.groups()
            if groups[0] and groups[1]:  # "X failed, Y passed" format
                failed = int(groups[0])
                passed = int(groups[1])
            elif groups[2] and groups[3]:  # "X passed, Y failed" format  
                passed = int(groups[2])
                failed = int(groups[3])
            elif groups[4]:  # "X passed" only format
                passed = int(groups[4])
                failed = 0
            else:
                passed = failed = 0
        else:
            passed = failed = 0
            
        total_tests += (passed + failed)
        total_passed += passed
        total_failed += failed
        
        if not success:
            failed_modules.append(module)
    
    # Overall summary
    print(f"\n{'='*80}")
    print(f"🏁 OVERALL TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests run: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if failed_modules:
        print(f"\n❌ Modules with failures:")
        for module in failed_modules:
            print(f"  • {module}")
        print(f"\n💡 Note: Some failures may be due to test isolation issues.")
        print(f"   Try running failing modules individually to verify functionality.")
    else:
        print(f"\n🎉 All tests passed!")
    
    print(f"{'='*80}")
    
    return len(failed_modules) == 0

def main():
    parser = argparse.ArgumentParser(description="Run SelfOS Backend API Tests")
    parser.add_argument("--all", action="store_true", help="Run all tests using module-by-module approach (default)")
    parser.add_argument("--all-together", action="store_true", help="Run all tests together (may have isolation issues)")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests only")
    parser.add_argument("--goals", action="store_true", help="Run goals tests only")
    parser.add_argument("--tasks", action="store_true", help="Run tasks tests only")
    parser.add_argument("--life-areas", action="store_true", help="Run life areas tests only")
    parser.add_argument("--media", action="store_true", help="Run media attachments tests only")
    parser.add_argument("--preferences", action="store_true", help="Run user preferences tests only")
    parser.add_argument("--feedback", action="store_true", help="Run feedback logs tests only")
    parser.add_argument("--stories", action="store_true", help="Run story sessions tests only")
    parser.add_argument("--main", action="store_true", help="Run main API tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument("--fast", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: tests/ directory not found.")
        print("Please run this script from the apps/backend_api directory.")
        sys.exit(1)
    
    # Check if we should run module-by-module (default for --all)
    if not any([args.unit, args.integration, args.auth, args.goals, args.tasks, 
                args.life_areas, args.media, args.preferences, args.feedback, args.stories, args.main, args.all_together]):
        # Default: run all tests module by module
        print("🚀 Running all tests module-by-module to avoid isolation issues...")
        success = run_module_by_module()
        sys.exit(0 if success else 1)
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    # Determine what to test
    test_targets = []
    
    if args.unit:
        test_targets.append("tests/unit/")
    elif args.integration:
        test_targets.append("tests/integration/")
    elif args.auth:
        test_targets.append("tests/unit/test_auth.py")
    elif args.goals:
        test_targets.append("tests/unit/test_goals.py")
    elif args.tasks:
        test_targets.append("tests/unit/test_tasks.py")
    elif args.life_areas:
        test_targets.append("tests/unit/test_life_areas.py")
    elif args.media:
        test_targets.append("tests/unit/test_media_attachments.py")
    elif args.preferences:
        test_targets.append("tests/unit/test_user_preferences.py")
    elif args.feedback:
        test_targets.append("tests/unit/test_feedback_logs.py")
    elif args.stories:
        test_targets.append("tests/unit/test_story_sessions.py")
    elif args.main:
        test_targets.append("tests/test_main.py")
    elif args.all_together:
        test_targets.append("tests/")
    
    # Build command
    cmd = base_cmd + test_targets
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("-v")  # Default to verbose
    
    if args.fast:
        cmd.append("-x")
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=term", "--cov-report=html"])
    
    # Add short traceback for better readability
    cmd.append("--tb=short")
    
    # Run the tests
    description = "Running " + (", ".join(test_targets) if test_targets else "all tests")
    success = run_command(cmd, description)
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("✅ Tests completed successfully!")
    else:
        print("❌ Some tests failed. See output above for details.")
    print(f"{'='*60}")
    
    # Additional commands for common workflows
    print("\n📋 Available test commands:")
    print("  python run_tests.py                 # All tests (module-by-module, recommended)")
    print("  python run_tests.py --all-together  # All tests together (may have isolation issues)")
    print("  python run_tests.py --unit          # Unit tests only")
    print("  python run_tests.py --integration   # Integration tests only")
    print("  python run_tests.py --auth          # Authentication tests only")
    print("  python run_tests.py --goals         # Goals tests only")
    print("  python run_tests.py --tasks         # Tasks tests only")
    print("  python run_tests.py --life-areas    # Life areas tests only")
    print("  python run_tests.py --media         # Media attachments tests only")
    print("  python run_tests.py --preferences   # User preferences tests only")
    print("  python run_tests.py --feedback     # Feedback logs tests only")
    print("  python run_tests.py --stories      # Story sessions tests only")
    print("  python run_tests.py --coverage      # With coverage report")
    print("  python run_tests.py --fast          # Stop on first failure")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()