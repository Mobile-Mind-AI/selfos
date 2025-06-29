#!/usr/bin/env python3
"""
System Test Script

This script tests all components of the SelfOS backend API
including the event-driven AI system.
"""

import asyncio
import requests
import json
import time
import sys
import os
from typing import Dict, Any, Optional

# Add parent directory to Python path to find app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "username": "testuser_" + str(int(time.time())),
    "email": f"test_{int(time.time())}@example.com",
    "password": "testpass123"
}

class SystemTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token: Optional[str] = None
        self.test_data = {}
        
    def print_status(self, message: str, success: bool = True):
        """Print colored status messages."""
        color = "\033[92m" if success else "\033[91m"  # Green or Red
        reset = "\033[0m"
        status = "✓" if success else "✗"
        print(f"{color}{status} {message}{reset}")
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling."""
        url = f"{self.base_url}{endpoint}"
        
        if self.token and "headers" not in kwargs:
            kwargs["headers"] = {"Authorization": f"Bearer {self.token}"}
        elif self.token and "headers" in kwargs:
            kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            
        response = requests.request(method, url, **kwargs)
        return response
        
    def test_basic_health(self) -> bool:
        """Test basic health endpoint."""
        try:
            response = self.make_request("GET", "/health")
            if response.status_code == 200:
                data = response.json()
                self.print_status(f"Basic health check: {data['status']}")
                return True
            else:
                self.print_status(f"Health check failed: {response.status_code}", False)
                return False
        except Exception as e:
            self.print_status(f"Health check error: {e}", False)
            return False
            
    def test_detailed_health(self) -> bool:
        """Test detailed health endpoint."""
        try:
            response = self.make_request("GET", "/health/detailed")
            if response.status_code == 200:
                data = response.json()
                self.print_status(f"System health: {data['status']}")
                
                # Check individual components
                for component, status in data["components"].items():
                    component_status = status.get("status", "unknown")
                    self.print_status(f"  {component}: {component_status}", 
                                    component_status == "healthy")
                return data["status"] in ["healthy", "degraded"]
            else:
                self.print_status(f"Detailed health check failed: {response.status_code}", False)
                return False
        except Exception as e:
            self.print_status(f"Detailed health check error: {e}", False)
            return False
            
    def test_event_system(self) -> bool:
        """Test event system."""
        try:
            response = self.make_request("POST", "/health/test-event")
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.print_status(f"Event system test: {data.get('status', 'unknown')}", success)
                return success
            else:
                self.print_status(f"Event system test failed: {response.status_code}", False)
                return False
        except Exception as e:
            self.print_status(f"Event system test error: {e}", False)
            return False
            
    def test_services(self) -> bool:
        """Test individual AI services."""
        services = ["progress", "storytelling", "notifications", "memory"]
        all_success = True
        
        for service in services:
            try:
                response = self.make_request("GET", f"/health/services/{service}")
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("status") == "healthy"
                    self.print_status(f"  {service} service: {data.get('status', 'unknown')}", success)
                    if not success:
                        all_success = False
                else:
                    self.print_status(f"  {service} service: HTTP {response.status_code}", False)
                    all_success = False
            except Exception as e:
                self.print_status(f"  {service} service error: {e}", False)
                all_success = False
                
        return all_success
        
    def test_authentication(self) -> bool:
        """Test user registration and authentication."""
        try:
            # Register user
            response = self.make_request("POST", "/auth/register", 
                                       json=TEST_USER)
            if response.status_code == 201:
                self.print_status("User registration successful")
            else:
                self.print_status(f"User registration failed: {response.status_code}", False)
                return False
                
            # Login
            response = self.make_request("POST", "/auth/login",
                                       json={
                                           "username": TEST_USER["username"],
                                           "password": TEST_USER["password"]
                                       })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.print_status("User login successful")
                return True
            else:
                self.print_status(f"User login failed: {response.status_code}", False)
                return False
                
        except Exception as e:
            self.print_status(f"Authentication error: {e}", False)
            return False
            
    def test_api_workflow(self) -> bool:
        """Test complete API workflow with event system."""
        try:
            # Create life area
            response = self.make_request("POST", "/api/life-areas",
                                       json={
                                           "name": "Test Life Area",
                                           "description": "Test area for system testing"
                                       })
            if response.status_code == 201:
                life_area_id = response.json()["id"]
                self.test_data["life_area_id"] = life_area_id
                self.print_status("Life area created")
            else:
                self.print_status(f"Life area creation failed: {response.status_code}", False)
                return False
                
            # Create goal
            response = self.make_request("POST", "/api/goals",
                                       json={
                                           "title": "Test Goal",
                                           "description": "Test goal for system testing",
                                           "life_area_id": life_area_id,
                                           "target_date": "2024-12-31"
                                       })
            if response.status_code == 201:
                goal_id = response.json()["id"]
                self.test_data["goal_id"] = goal_id
                self.print_status("Goal created")
            else:
                self.print_status(f"Goal creation failed: {response.status_code}", False)
                return False
                
            # Create task
            response = self.make_request("POST", "/api/tasks",
                                       json={
                                           "title": "Test Task",
                                           "description": "Test task for system testing",
                                           "goal_id": goal_id,
                                           "duration": 25
                                       })
            if response.status_code == 201:
                task_id = response.json()["id"]
                self.test_data["task_id"] = task_id
                self.print_status("Task created")
            else:
                self.print_status(f"Task creation failed: {response.status_code}", False)
                return False
                
            # CRITICAL: Complete task (this triggers AI events!)
            response = self.make_request("PUT", f"/api/tasks/{task_id}/complete")
            if response.status_code == 200:
                self.print_status("Task completed - AI events triggered!")
                
                # Give the event system a moment to process
                time.sleep(2)
                
                # Check if story was generated
                response = self.make_request("GET", "/api/story-sessions")
                if response.status_code == 200:
                    stories = response.json()
                    if stories:
                        self.print_status(f"Story generated: {len(stories)} story sessions found")
                    else:
                        self.print_status("No stories generated yet (may take time)", False)
                        
                # Check goal progress
                response = self.make_request("GET", f"/api/goals/{goal_id}")
                if response.status_code == 200:
                    goal_data = response.json()
                    progress = goal_data.get("progress", 0)
                    self.print_status(f"Goal progress updated: {progress}%")
                    
                return True
            else:
                self.print_status(f"Task completion failed: {response.status_code}", False)
                return False
                
        except Exception as e:
            self.print_status(f"API workflow error: {e}", False)
            return False
            
    def test_database_migration(self) -> bool:
        """Test database migration status."""
        try:
            response = self.make_request("GET", "/health/database/migration-status")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                self.print_status(f"Database migration: {status}", status == "healthy")
                return status == "healthy"
            else:
                self.print_status(f"Migration check failed: {response.status_code}", False)
                return False
        except Exception as e:
            self.print_status(f"Migration check error: {e}", False)
            return False
            
    def run_all_tests(self) -> bool:
        """Run all system tests."""
        print("\n🚀 Starting SelfOS System Tests")
        print("=" * 50)
        
        tests = [
            ("Basic Health", self.test_basic_health),
            ("Detailed Health", self.test_detailed_health),
            ("Database Migration", self.test_database_migration),
            ("Event System", self.test_event_system),
            ("AI Services", self.test_services),
            ("Authentication", self.test_authentication),
            ("API Workflow", self.test_api_workflow),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} Tests:")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.print_status(f"{test_name} test failed with exception: {e}", False)
                results.append((test_name, False))
                
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("-" * 25)
        
        passed = 0
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            color = "\033[92m" if result else "\033[91m"
            print(f"{color}{status}\033[0m - {test_name}")
            if result:
                passed += 1
                
        print(f"\n📈 Overall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("\n🎉 All tests passed! System is fully operational.")
            return True
        else:
            print(f"\n⚠️  {len(results) - passed} tests failed. Check the logs above.")
            return False

def main():
    """Main function to run system tests."""
    tester = SystemTester()
    
    try:
        success = tester.run_all_tests()
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()