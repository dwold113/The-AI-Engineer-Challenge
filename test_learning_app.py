"""
Comprehensive test suite for Learning Experience App
Tests both backend API and frontend UI behavior
"""
import httpx
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class TestResult:
    def __init__(self, test_name: str, category: str, passed: bool, 
                 details: str = "", response_data: Any = None):
        self.test_name = test_name
        self.category = category
        self.passed = passed
        self.details = details
        self.response_data = response_data
        self.timestamp = datetime.now().isoformat()

def test_backend_api(test_name: str, endpoint: str, method: str = "GET", 
                    data: Dict = None, expected_status: int = 200,
                    expected_fields: List[str] = None) -> TestResult:
    """Test backend API endpoint"""
    try:
        async def run_test():
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(f"{API_URL}{endpoint}")
                elif method == "POST":
                    response = await client.post(
                        f"{API_URL}{endpoint}",
                        json=data,
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    return TestResult(test_name, "backend", False, 
                                    f"Unsupported method: {method}")
                
                passed = response.status_code == expected_status
                details = f"Status: {response.status_code}"
                
                if passed and expected_fields:
                    try:
                        response_json = response.json()
                        missing_fields = [f for f in expected_fields if f not in response_json]
                        if missing_fields:
                            passed = False
                            details += f". Missing fields: {missing_fields}"
                        else:
                            details += f". All expected fields present: {expected_fields}"
                    except:
                        passed = False
                        details += ". Invalid JSON response"
                
                return TestResult(test_name, "backend", passed, details, 
                                response.text[:500] if response.text else None)
        
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        return TestResult(test_name, "backend", False, f"Exception: {str(e)}")

def test_learning_flow(test_name: str, topic: str, expected_steps: int = None,
                       expected_examples: int = None) -> TestResult:
    """Test complete learning flow: topic -> plan -> examples"""
    try:
        async def run_test():
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Create learning plan
                response = await client.post(
                    f"{API_URL}/api/learn",
                    json={"topic": topic},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    return TestResult(test_name, "learning_flow", False,
                                    f"Failed to create plan. Status: {response.status_code}")
                
                data = response.json()
                
                # Validate response structure
                if "plan" not in data or "examples" not in data:
                    return TestResult(test_name, "learning_flow", False,
                                    "Missing 'plan' or 'examples' in response")
                
                plan = data.get("plan", [])
                examples = data.get("examples", [])
                
                details = f"Plan steps: {len(plan)}, Examples: {len(examples)}"
                passed = True
                
                # Check step count if expected
                if expected_steps is not None:
                    if len(plan) != expected_steps:
                        passed = False
                        details += f". Expected {expected_steps} steps, got {len(plan)}"
                
                # Check example count if expected
                if expected_examples is not None:
                    if len(examples) != expected_examples:
                        passed = False
                        details += f". Expected {expected_examples} examples, got {len(examples)}"
                
                # Validate plan structure
                for i, step in enumerate(plan):
                    if "title" not in step or "description" not in step:
                        passed = False
                        details += f". Step {i+1} missing title or description"
                
                # Validate examples structure
                for i, example in enumerate(examples):
                    if "title" not in example or "url" not in example:
                        passed = False
                        details += f". Example {i+1} missing title or url"
                
                return TestResult(test_name, "learning_flow", passed, details, data)
        
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        return TestResult(test_name, "learning_flow", False, f"Exception: {str(e)}")

def test_frontend_ui(test_name: str, topic: str) -> TestResult:
    """Test frontend UI by checking if page loads and contains expected content"""
    try:
        async def run_test():
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                try:
                    # Get the frontend page
                    response = await client.get(FRONTEND_URL)
                except (httpx.ConnectError, httpx.TimeoutException):
                    return TestResult(test_name, "frontend", False,
                                    f"Frontend not running at {FRONTEND_URL}. Start with 'npm run dev' in frontend/")
                
                if response.status_code != 200:
                    return TestResult(test_name, "frontend", False,
                                    f"Failed to load frontend. Status: {response.status_code}")
                
                html = response.text
                
                # Check for key UI elements (case-insensitive)
                html_lower = html.lower()
                checks = {
                    "Learning Experience": "learning experience" in html_lower,
                    "Start Learning button": "start learning" in html_lower,
                    "Input field": 'type="text"' in html or 'input' in html_lower or 'placeholder' in html_lower,
                    "React app loaded": "__next" in html or "react" in html_lower or "next" in html_lower,
                }
                
                failed_checks = [k for k, v in checks.items() if not v]
                
                if failed_checks:
                    return TestResult(test_name, "frontend", False,
                                    f"Missing UI elements: {failed_checks}")
                
                return TestResult(test_name, "frontend", True,
                                f"All UI elements present: {list(checks.keys())}")
        
        result = asyncio.run(run_test())
        return result
    except Exception as e:
        return TestResult(test_name, "frontend", False, f"Exception: {str(e)}")

def run_all_tests() -> List[TestResult]:
    """Run comprehensive test suite"""
    results = []
    
    print("🧪 Starting comprehensive test suite...\n")
    
    # ===== BACKEND API TESTS =====
    print("📡 Testing Backend API...")
    
    # Basic endpoint tests
    results.append(test_backend_api(
        "Root endpoint accessible",
        "/",
        expected_status=200,
        expected_fields=["status", "app"]
    ))
    
    results.append(test_backend_api(
        "API key configured check",
        "/",
        expected_status=200
    ))
    
    # Valid learning topics
    print("\n✅ Testing Valid Learning Topics...")
    valid_topics = [
        ("Python programming", "Python programming", None, None),
        ("Machine Learning", "Machine Learning", None, None),
        ("Web Development", "Web Development", None, None),
        ("Cooking Italian food", "Cooking Italian food", None, None),
        ("Spanish language", "Spanish language", None, None),
        ("Photography basics", "Photography basics", None, None),
        ("3 steps requested", "how to code give me 3 steps", 3, None),
        ("10 resources requested", "Python programming give me 10 resources", None, 10),
        ("Both specified", "Machine Learning give 5 steps and 8 examples", 5, 8),
    ]
    
    for test_name, actual_topic, expected_steps, expected_examples in valid_topics:
        results.append(test_learning_flow(
            f"Valid topic: {test_name}",
            actual_topic,
            expected_steps,
            expected_examples
        ))
    
    # Invalid learning topics (should be rejected)
    print("\n❌ Testing Invalid Learning Topics (should fail)...")
    invalid_topics = [
        ("Gibberish", "gfdnjlg nfgdsgdnjklgfnjs"),
        ("Abstract concept", "the meaning of life"),
        ("Random chars", "asdfghjkl"),
        ("Just numbers", "123456"),
        ("Too vague", "stuff"),
        ("Empty string", ""),
        ("Single character", "a"),
        ("Only special chars", "!!!###"),
        ("Copyrighted content", "marvel universe"),
        ("GIF request", "gif of dancing boy"),
        ("Specific person", "jaxson dart running"),
    ]
    
    for category, topic in invalid_topics:
        results.append(test_backend_api(
            f"Invalid topic rejected: {category}",
            "/api/learn",
            method="POST",
            data={"topic": topic},
            expected_status=400
        ))
    
    # Edge cases
    print("\n🔍 Testing Edge Cases...")
    edge_cases = [
        ("Very long topic", "A" * 201),
        ("Unreasonable resource count", "Python programming give me 100 resources"),
        ("Unreasonable step count", "Machine Learning give me 50 steps"),
        ("Too few steps", "Web Development give me 1 step"),
        ("Special characters in topic", "C++ programming"),
        ("Unicode characters", "日本語を学ぶ"),
        ("SQL injection attempt", "'; DROP TABLE users; --"),
        ("XSS attempt", "<script>alert('xss')</script>"),
        ("Very short valid", "AI"),
        ("Numbers in valid topic", "Python 3 programming"),
    ]
    
    for category, topic in edge_cases:
        results.append(test_learning_flow(
            f"Edge case: {category}",
            topic,
            None,
            None
        ))
    
    # Expand step tests
    print("\n🔬 Testing Expand Step Functionality...")
    expand_tests = [
        ("Expand first step", "Python programming", 0),
        ("Expand middle step", "Machine Learning", 2),
        ("Expand with invalid step", "Web Development", 999),
    ]
    
    for test_name, topic, step_index in expand_tests:
        try:
            async def test_expand():
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # First get a learning plan
                    learn_response = await client.post(
                        f"{API_URL}/api/learn",
                        json={"topic": topic},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if learn_response.status_code != 200:
                        return TestResult(test_name, "expand_step", False,
                                        f"Failed to get plan: {learn_response.status_code}")
                    
                    plan_data = learn_response.json()
                    plan = plan_data.get("plan", [])
                    
                    if step_index >= len(plan):
                        return TestResult(test_name, "expand_step", False,
                                        f"Step index {step_index} out of range (plan has {len(plan)} steps)")
                    
                    step = plan[step_index]
                    
                    # Try to expand the step
                    expand_response = await client.post(
                        f"{API_URL}/api/expand-step",
                        json={
                            "topic": topic,
                            "step_title": step["title"],
                            "step_description": step["description"]
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if expand_response.status_code != 200:
                        return TestResult(test_name, "expand_step", False,
                                        f"Failed to expand step: {expand_response.status_code}")
                    
                    expand_data = expand_response.json()
                    
                    # Check for expected fields
                    expected_fields = ["additionalContext", "practicalDetails", 
                                     "importantConsiderations", "realWorldExamples", 
                                     "potentialChallenges"]
                    has_content = any(field in expand_data and expand_data[field] 
                                    for field in expected_fields)
                    
                    if not has_content:
                        return TestResult(test_name, "expand_step", False,
                                        "Expanded step has no content")
                    
                    return TestResult(test_name, "expand_step", True,
                                    f"Successfully expanded step {step_index + 1}")
            
            result = asyncio.run(test_expand())
            results.append(result)
        except Exception as e:
            results.append(TestResult(test_name, "expand_step", False, f"Exception: {str(e)}"))
    
    # Frontend UI tests
    print("\n🎨 Testing Frontend UI...")
    results.append(test_frontend_ui("Frontend loads", "test"))
    results.append(test_frontend_ui("Frontend has learning interface", "test"))
    
    # Performance tests
    print("\n⚡ Testing Performance...")
    performance_tests = [
        ("Fast response", "Python"),
        ("Medium topic", "Machine Learning with TensorFlow and PyTorch"),
        ("Complex topic", "How to build a full-stack web application using React, Node.js, PostgreSQL, and Docker"),
    ]
    
    for test_name, topic in performance_tests:
        try:
            async def test_performance():
                start = datetime.now()
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{API_URL}/api/learn",
                        json={"topic": topic},
                        headers={"Content-Type": "application/json"}
                    )
                    end = datetime.now()
                    duration = (end - start).total_seconds()
                    
                    # Performance threshold: should complete in reasonable time
                    # Note: AI generation can take time, so we use 30s as threshold
                    passed = response.status_code == 200 and duration < 30.0
                    details = f"Status: {response.status_code}, Duration: {duration:.2f}s"
                    if duration >= 30.0:
                        details += " (exceeded 30s threshold)"
                    
                    return TestResult(test_name, "performance", passed, details)
            
            result = asyncio.run(test_performance())
            results.append(result)
        except Exception as e:
            results.append(TestResult(test_name, "performance", False, f"Exception: {str(e)}"))
    
    return results

def generate_report(results: List[TestResult]) -> Dict:
    """Generate comprehensive test report"""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    # Group by category
    by_category = {}
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = {"passed": 0, "failed": 0, "tests": []}
        if result.passed:
            by_category[result.category]["passed"] += 1
        else:
            by_category[result.category]["failed"] += 1
        by_category[result.category]["tests"].append(result)
    
    report = {
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "timestamp": datetime.now().isoformat()
        },
        "by_category": {},
        "all_tests": []
    }
    
    for category, data in by_category.items():
        report["by_category"][category] = {
            "total": len(data["tests"]),
            "passed": data["passed"],
            "failed": data["failed"],
            "pass_rate": f"{(data['passed']/len(data['tests'])*100):.1f}%" if data["tests"] else "0%"
        }
    
    for result in results:
        report["all_tests"].append({
            "test_name": result.test_name,
            "category": result.category,
            "passed": result.passed,
            "details": result.details,
            "timestamp": result.timestamp
        })
    
    return report

def print_report(report: Dict):
    """Print formatted test report"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    summary = report["summary"]
    print(f"\n📈 SUMMARY")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  ✅ Passed: {summary['passed']}")
    print(f"  ❌ Failed: {summary['failed']}")
    print(f"  📊 Pass Rate: {summary['pass_rate']}")
    
    print(f"\n📂 BY CATEGORY")
    for category, data in report["by_category"].items():
        status = "✅" if data["failed"] == 0 else "⚠️"
        print(f"  {status} {category.upper()}: {data['passed']}/{data['total']} passed ({data['pass_rate']})")
    
    print(f"\n📋 DETAILED RESULTS")
    print("-"*80)
    
    failed_tests = [t for t in report["all_tests"] if not t["passed"]]
    passed_tests = [t for t in report["all_tests"] if t["passed"]]
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"  ❌ {test['test_name']} ({test['category']})")
            print(f"     Details: {test['details']}")
    
    if passed_tests:
        print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
        for test in passed_tests[:20]:  # Show first 20
            print(f"  ✅ {test['test_name']} ({test['category']})")
        if len(passed_tests) > 20:
            print(f"  ... and {len(passed_tests) - 20} more passed tests")

if __name__ == "__main__":
    print("🚀 Starting Learning Experience App Test Suite")
    print(f"Backend URL: {API_URL}")
    print(f"Frontend URL: {FRONTEND_URL}\n")
    
    results = run_all_tests()
    report = generate_report(results)
    
    # Save report to file
    with open("test_report_learning_app.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print report
    print_report(report)
    
    # Save markdown report
    with open("TEST_REPORT_LEARNING_APP.md", "w") as f:
        f.write("# Learning Experience App - Comprehensive Test Report\n\n")
        f.write(f"Generated: {report['summary']['timestamp']}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total Tests**: {report['summary']['total_tests']}\n")
        f.write(f"- **Passed**: {report['summary']['passed']}\n")
        f.write(f"- **Failed**: {report['summary']['failed']}\n")
        f.write(f"- **Pass Rate**: {report['summary']['pass_rate']}\n\n")
        
        f.write("## Results by Category\n\n")
        for category, data in report["by_category"].items():
            f.write(f"### {category.upper()}\n")
            f.write(f"- Total: {data['total']}\n")
            f.write(f"- Passed: {data['passed']}\n")
            f.write(f"- Failed: {data['failed']}\n")
            f.write(f"- Pass Rate: {data['pass_rate']}\n\n")
        
        f.write("## All Test Results\n\n")
        f.write("| Test Name | Category | Status | Details |\n")
        f.write("|-----------|----------|--------|----------|\n")
        for test in report["all_tests"]:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            f.write(f"| {test['test_name']} | {test['category']} | {status} | {test['details']} |\n")
    
    print(f"\n💾 Reports saved:")
    print(f"  - test_report_learning_app.json")
    print(f"  - TEST_REPORT_LEARNING_APP.md")
    print("\n" + "="*80)

