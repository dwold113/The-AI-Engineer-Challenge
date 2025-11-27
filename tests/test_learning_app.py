"""
Test suite for Learning Experience App
Tests the simplified backend (no resources/examples)
"""
import httpx
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

API_URL = "http://localhost:8000"

class TestResult:
    def __init__(self, test_name: str, category: str):
        self.test_name = test_name
        self.category = category
        self.input = ""
        self.api_status = None
        self.api_response = None
        self.api_error = None
        self.passed = False
        self.verdict = ""
        self.timestamp = datetime.now().isoformat()

async def test_api_call(test_name: str, topic: str, category: str, 
                       should_succeed: bool = True) -> TestResult:
    """Test API endpoint with given topic"""
    result = TestResult(test_name, category)
    result.input = topic
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_URL}/api/learn",
                json={"topic": topic},
                headers={"Content-Type": "application/json"}
            )
            
            result.api_status = response.status_code
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result.api_response = data
                    
                    # Validate response structure
                    if "plan" in data and isinstance(data["plan"], list):
                        plan = data["plan"]
                        if len(plan) > 0:
                            # Check plan structure
                            has_valid_steps = all(
                                "title" in step and "description" in step 
                                for step in plan
                            )
                            if has_valid_steps:
                                result.passed = should_succeed
                                result.verdict = f"✅ SUCCESS: Generated {len(plan)} steps"
                            else:
                                result.passed = False
                                result.verdict = "❌ FAILED: Plan steps missing title/description"
                        else:
                            result.passed = False
                            result.verdict = "❌ FAILED: Plan is empty"
                    else:
                        result.passed = False
                        result.verdict = "❌ FAILED: Missing or invalid 'plan' field"
                except json.JSONDecodeError:
                    result.api_error = "Invalid JSON response"
                    result.passed = False
                    result.verdict = "❌ FAILED: Invalid JSON"
            else:
                # Expected failure
                if not should_succeed:
                    result.passed = True
                    result.verdict = f"✅ CORRECTLY REJECTED: {response.status_code}"
                else:
                    try:
                        error_data = response.json()
                        result.api_error = error_data.get("detail", f"Status {response.status_code}")
                    except:
                        result.api_error = response.text[:200] if response.text else f"Status {response.status_code}"
                    result.passed = False
                    result.verdict = f"❌ FAILED: {result.api_error}"
                    
        except httpx.TimeoutException:
            result.api_error = "Request timeout"
            result.passed = False
            result.verdict = "❌ FAILED: Request timed out"
        except httpx.ConnectError:
            result.api_error = "Cannot connect to API"
            result.passed = False
            result.verdict = "❌ FAILED: Cannot connect to API (is it running?)"
        except Exception as e:
            result.api_error = str(e)
            result.passed = False
            result.verdict = f"❌ FAILED: {str(e)}"
    
    return result

async def test_expand_step(topic: str, step_title: str, step_description: str) -> TestResult:
    """Test expand-step endpoint"""
    result = TestResult("Expand Step", "expand_step")
    result.input = f"{topic} - {step_title}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_URL}/api/expand-step",
                json={
                    "topic": topic,
                    "step_title": step_title,
                    "step_description": step_description
                },
                headers={"Content-Type": "application/json"}
            )
            
            result.api_status = response.status_code
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result.api_response = data
                    
                    # Check for expected fields
                    expected_fields = ["additionalContext", "practicalDetails", 
                                     "importantConsiderations", "realWorldExamples", 
                                     "potentialChallenges"]
                    has_fields = all(field in data for field in expected_fields)
                    
                    if has_fields:
                        result.passed = True
                        result.verdict = "✅ SUCCESS: Expanded step returned all fields"
                    else:
                        result.passed = False
                        result.verdict = "❌ FAILED: Missing expected fields"
                except json.JSONDecodeError:
                    result.passed = False
                    result.verdict = "❌ FAILED: Invalid JSON"
            else:
                result.api_error = f"Status {response.status_code}"
                result.passed = False
                result.verdict = f"❌ FAILED: {result.api_error}"
                
        except Exception as e:
            result.api_error = str(e)
            result.passed = False
            result.verdict = f"❌ FAILED: {str(e)}"
    
    return result

# Test cases
TEST_CASES = [
    # Valid topics (should succeed)
    ("Valid: Language", "amharic", "valid", True),
    ("Valid: Language with prefix", "learning spanish", "valid", True),
    ("Valid: Skill", "cooking", "valid", True),
    ("Valid: Subject", "mathematics", "valid", True),
    ("Valid: Concept", "machine learning", "valid", True),
    ("Valid: With steps request", "python programming give me 3 steps", "valid", True),
    ("Valid: Practical topic", "how to run a marathon", "valid", True),
    
    # Invalid topics (should be rejected)
    ("Invalid: Gibberish", "fgnrjk gnsogfd", "invalid", False),
    ("Invalid: Random characters", "asdfgh jklqwerty", "invalid", False),
    ("Invalid: Person name", "donald trump", "invalid", False),
    ("Invalid: Person name", "barack obama", "invalid", False),
    ("Invalid: Person name", "elon musk", "invalid", False),
    ("Invalid: Nonsensical words", "time space coffee", "invalid", False),
    ("Invalid: Nonsensical words", "car tree music", "invalid", False),
    
    # Edge cases (potential breaking points)
    ("Edge: Empty string", "", "edge_case", False),
    ("Edge: Single character", "a", "edge_case", False),
    ("Edge: Only spaces", "   ", "edge_case", False),
    ("Edge: Very long topic", "a" * 500, "edge_case", False),
    ("Edge: Numbers only", "123456", "edge_case", False),
    ("Edge: Special characters", "test@#$%^&*()", "edge_case", False),
    ("Edge: SQL injection attempt", "'; DROP TABLE users; --", "edge_case", False),
    ("Edge: XSS attempt", "<script>alert('xss')</script>", "edge_case", False),
    ("Edge: Unicode", "学习中文", "edge_case", True),  # Chinese "learn Chinese" is valid
    ("Edge: Emoji only", "🎓📚✨", "edge_case", False),
    ("Edge: Newlines/tabs", "test\nnewline\ttab", "edge_case", False),
    ("Edge: Extreme steps request", "python give me 100 steps", "edge_case", True),  # Should work but adjust
    ("Edge: Zero steps", "python give me 0 steps", "edge_case", True),  # Should work but adjust
    ("Edge: Negative steps", "python give me -5 steps", "edge_case", False),  # Should reject negative steps
    ("Edge: Just 'learning'", "learning", "edge_case", False),
    ("Edge: Just 'how to'", "how to", "edge_case", False),
    ("Edge: Multiple languages", "amharic and spanish and french", "edge_case", True),
    ("Edge: Very short valid", "python", "edge_case", True),
    ("Edge: Very long valid", "machine learning and artificial intelligence and deep learning and neural networks", "edge_case", True),
]

async def run_all_tests():
    """Run all test cases"""
    print("=" * 80)
    print("Learning Experience App - Test Suite")
    print("=" * 80)
    print()
    
    results = []
    
    # Test /api/learn endpoint
    print("Testing /api/learn endpoint...")
    print("-" * 80)
    
    for test_name, topic, category, should_succeed in TEST_CASES:
        result = await test_api_call(test_name, topic, category, should_succeed)
        results.append(result)
        
        status_icon = "✅" if result.passed else "❌"
        print(f"{status_icon} {result.test_name}")
        print(f"   Input: {repr(result.input[:60])}")
        print(f"   Status: {result.api_status}")
        print(f"   Verdict: {result.verdict}")
        if result.api_error:
            print(f"   Error: {result.api_error}")
        print()
    
    # Test /api/expand-step endpoint
    print("Testing /api/expand-step endpoint...")
    print("-" * 80)
    
    expand_tests = [
        ("python", "Step 1: Learn Basics", "Start with Python syntax and variables"),
        ("cooking", "Step 2: Practice", "Try making simple dishes"),
    ]
    
    for topic, step_title, step_description in expand_tests:
        result = await test_expand_step(topic, step_title, step_description)
        results.append(result)
        
        status_icon = "✅" if result.passed else "❌"
        print(f"{status_icon} {result.test_name}")
        print(f"   Input: {topic} - {step_title}")
        print(f"   Status: {result.api_status}")
        print(f"   Verdict: {result.verdict}")
        if result.api_error:
            print(f"   Error: {result.api_error}")
        print()
    
    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print()
    
    # Group by category
    by_category = {}
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = {"total": 0, "passed": 0}
        by_category[result.category]["total"] += 1
        if result.passed:
            by_category[result.category]["passed"] += 1
    
    print("By Category:")
    for category, stats in by_category.items():
        pct = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {category}: {stats['passed']}/{stats['total']} ({pct:.1f}%)")
    print()
    
    # Failed tests
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        print("Failed Tests:")
        for result in failed_tests:
            print(f"  ❌ {result.test_name}: {result.verdict}")
        print()
    
    # Save results
    results_dict = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed/total*100 if total > 0 else 0
        },
        "by_category": {
            cat: {"total": stats["total"], "passed": stats["passed"], 
                  "pass_rate": stats["passed"]/stats["total"]*100 if stats["total"] > 0 else 0}
            for cat, stats in by_category.items()
        },
        "results": [
            {
                "test_name": r.test_name,
                "category": r.category,
                "input": r.input,
                "api_status": r.api_status,
                "passed": r.passed,
                "verdict": r.verdict,
                "api_error": r.api_error,
                "timestamp": r.timestamp
            }
            for r in results
        ]
    }
    
    with open("tests/test_results.json", "w") as f:
        json.dump(results_dict, f, indent=2)
    
    print(f"Results saved to tests/test_results.json")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())
