"""
Comprehensive test suite for Learning Experience App
Tests: Input → API Response → UI Display
"""
import httpx
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class ComprehensiveTestResult:
    def __init__(self, test_name: str, category: str):
        self.test_name = test_name
        self.category = category
        self.input = ""
        self.api_status = None
        self.api_response = None
        self.api_error = None
        self.ui_accessible = False
        self.ui_displays_content = False
        self.ui_error = None
        self.passed = False
        self.verdict = ""
        self.timestamp = datetime.now().isoformat()

async def test_complete_flow_async(test_name: str, topic: str, category: str, 
                                   should_succeed: bool = True) -> ComprehensiveTestResult:
    """
    Test complete flow: Input → API → UI Display (async implementation)
    """
    result = ComprehensiveTestResult(test_name, category)
    result.input = topic
    
    # Step 1: Test API
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            api_response = await client.post(
                f"{API_URL}/api/learn",
                json={"topic": topic},
                headers={"Content-Type": "application/json"}
            )
            
            result.api_status = api_response.status_code
            
            if api_response.status_code == 200:
                try:
                    result.api_response = api_response.json()
                    result.api_error = None
                except:
                    result.api_response = None
                    result.api_error = "Invalid JSON response"
            else:
                try:
                    error_data = api_response.json()
                    result.api_error = error_data.get("detail", f"Status {api_response.status_code}")
                except:
                    result.api_error = api_response.text[:200] if api_response.text else f"Status {api_response.status_code}"
            
            # Step 2: Test UI (only if API succeeded or we want to test UI anyway)
            try:
                ui_response = await client.get(FRONTEND_URL, timeout=10.0)
                result.ui_accessible = ui_response.status_code == 200
                
                if result.ui_accessible:
                    html = ui_response.text.lower()
                    # Check if UI has the learning interface
                    has_interface = (
                        "learning experience" in html and
                        "start learning" in html and
                        ("input" in html or "placeholder" in html)
                    )
                    result.ui_displays_content = has_interface
                    
                    if not has_interface:
                        result.ui_error = "UI missing key elements"
            except (httpx.ConnectError, httpx.TimeoutException):
                result.ui_accessible = False
                result.ui_error = f"Frontend not accessible at {FRONTEND_URL}"
            except Exception as e:
                result.ui_error = f"UI test error: {str(e)}"
            
            # Determine verdict
            if should_succeed:
                # Should succeed: API 200, has plan/examples, UI accessible
                if result.api_status == 200:
                    if result.api_response and "plan" in result.api_response and "examples" in result.api_response:
                        plan = result.api_response.get("plan", [])
                        examples = result.api_response.get("examples", [])
                        if len(plan) > 0 and len(examples) > 0:
                            result.passed = True
                            result.verdict = f"✅ SUCCESS: Generated {len(plan)} steps and {len(examples)} examples. UI accessible: {result.ui_accessible}"
                        else:
                            result.passed = False
                            result.verdict = f"❌ PARTIAL: API returned 200 but plan ({len(plan)} steps) or examples ({len(examples)} examples) are empty"
                    else:
                        result.passed = False
                        result.verdict = f"❌ FAILED: API 200 but missing plan/examples in response"
                else:
                    result.passed = False
                    result.verdict = f"❌ FAILED: API returned {result.api_status}. Error: {result.api_error}"
            else:
                # Should fail: API 400, clear error message
                if result.api_status == 400:
                    result.passed = True
                    result.verdict = f"✅ CORRECTLY REJECTED: API returned 400 as expected. Error: {result.api_error}"
                elif result.api_status == 200:
                    result.passed = False
                    result.verdict = f"❌ SECURITY ISSUE: Should have been rejected but API returned 200. This is dangerous!"
                else:
                    result.passed = False
                    result.verdict = f"⚠️ UNEXPECTED: API returned {result.api_status} instead of 400. Error: {result.api_error}"
            
            return result
        except httpx.TimeoutException as e:
            result.api_error = f"Timeout: {str(e)}"
            result.passed = False
            result.verdict = f"❌ TIMEOUT: Request timed out after 30 seconds"
            return result
        except httpx.ConnectError as e:
            result.api_error = f"Connection Error: {str(e)}"
            result.passed = False
            result.verdict = f"❌ CONNECTION ERROR: Cannot connect to {API_URL}. Is the backend running?"
            return result
        except Exception as e:
            import traceback
            error_msg = f"Exception: {str(e)}"
            result.api_error = error_msg
            result.passed = False
            result.verdict = f"❌ EXCEPTION: {str(e)}"
            return result

def test_complete_flow(test_name: str, topic: str, category: str, 
                       should_succeed: bool = True) -> ComprehensiveTestResult:
    """Wrapper to run async test"""
    return asyncio.run(test_complete_flow_async(test_name, topic, category, should_succeed))

def run_all_comprehensive_tests() -> List[ComprehensiveTestResult]:
    """Run comprehensive test suite"""
    results = []
    
    print("🧪 Starting Comprehensive Test Suite...")
    print(f"Backend: {API_URL}")
    print(f"Frontend: {FRONTEND_URL}\n")
    
    # ===== VALID LEARNING TOPICS (Should Succeed) =====
    print("="*80)
    print("✅ TESTING VALID LEARNING TOPICS (Should Succeed)")
    print("="*80)
    
    valid_topics = [
        ("Python programming", "Basic programming topic"),
        ("Machine Learning", "Technical topic"),
        ("Web Development", "Popular topic"),
        ("Cooking Italian food", "Practical skill"),
        ("Spanish language", "Language learning"),
        ("Photography basics", "Creative skill"),
        ("how to code give me 3 steps", "Topic with step request"),
        ("Python programming give me 10 resources", "Topic with resource request"),
        ("Machine Learning give 5 steps and 8 examples", "Topic with both requests"),
    ]
    
    for topic, description in valid_topics:
        print(f"\n📝 Testing: {description}")
        print(f"   Input: '{topic}'")
        result = test_complete_flow(f"Valid: {description}", topic, "valid_topic", should_succeed=True)
        results.append(result)
        print(f"   Result: {result.verdict}")
    
    # ===== INVALID LEARNING TOPICS (Should Fail) =====
    print("\n" + "="*80)
    print("❌ TESTING INVALID LEARNING TOPICS (Should Be Rejected)")
    print("="*80)
    
    invalid_topics = [
        ("gfdnjlg nfgdsgdnjklgfnjs", "Gibberish"),
        ("the meaning of life", "Abstract/philosophical"),
        ("asdfghjkl", "Random characters"),
        ("123456", "Just numbers"),
        ("stuff", "Too vague"),
        ("", "Empty string"),
        ("a", "Single character"),
        ("!!!###", "Only special characters"),
        ("marvel universe", "Copyrighted content"),
        ("gif of dancing boy", "Animation request"),
        ("jaxson dart running", "Specific person"),
    ]
    
    for topic, description in invalid_topics:
        print(f"\n📝 Testing: {description}")
        print(f"   Input: '{topic}'")
        result = test_complete_flow(f"Invalid: {description}", topic, "invalid_topic", should_succeed=False)
        results.append(result)
        print(f"   Result: {result.verdict}")
    
    # ===== EDGE CASES =====
    print("\n" + "="*80)
    print("🔍 TESTING EDGE CASES")
    print("="*80)
    
    edge_cases = [
        ("A" * 201, "Very long topic (201 chars)", False),  # Should be rejected
        ("Python programming give me 100 resources", "Unreasonable resource count", False),  # Should be adjusted/rejected
        ("Machine Learning give me 50 steps", "Unreasonable step count", False),  # Should be adjusted/rejected
        ("Web Development give me 1 step", "Too few steps", False),  # Should be adjusted/rejected
        ("C++ programming", "Special characters", True),  # Should work
        ("日本語を学ぶ", "Unicode characters", True),  # Should work
        ("'; DROP TABLE users; --", "SQL injection attempt", False),  # Should be rejected
        ("<script>alert('xss')</script>", "XSS attempt", False),  # Should be rejected
        ("AI", "Very short but valid", True),  # Should work
        ("Python 3 programming", "Numbers in topic", True),  # Should work
    ]
    
    for topic, description, should_succeed in edge_cases:
        print(f"\n📝 Testing: {description}")
        print(f"   Input: '{topic[:50]}{'...' if len(topic) > 50 else ''}'")
        result = test_complete_flow(f"Edge case: {description}", topic, "edge_case", should_succeed=should_succeed)
        results.append(result)
        print(f"   Result: {result.verdict}")
    
    return results

def generate_comprehensive_report(results: List[ComprehensiveTestResult]) -> Dict:
    """Generate comprehensive test report"""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    # Group by category
    by_category = {}
    for result in results:
        if result.category not in by_category:
            by_category[result.category] = {"total": 0, "passed": 0, "failed": 0, "tests": []}
        by_category[result.category]["total"] += 1
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
        "detailed_results": []
    }
    
    for category, data in by_category.items():
        report["by_category"][category] = {
            "total": data["total"],
            "passed": data["passed"],
            "failed": data["failed"],
            "pass_rate": f"{(data['passed']/data['total']*100):.1f}%" if data["total"] > 0 else "0%"
        }
    
    for result in results:
        report["detailed_results"].append({
            "test_name": result.test_name,
            "category": result.category,
            "input": result.input,
            "api_status": result.api_status,
            "api_error": result.api_error,
            "api_response_summary": {
                "has_plan": result.api_response and "plan" in result.api_response if result.api_response else False,
                "plan_steps": len(result.api_response.get("plan", [])) if result.api_response and "plan" in result.api_response else 0,
                "has_examples": result.api_response and "examples" in result.api_response if result.api_response else False,
                "example_count": len(result.api_response.get("examples", [])) if result.api_response and "examples" in result.api_response else 0,
            } if result.api_response else None,
            "ui_accessible": result.ui_accessible,
            "ui_displays_content": result.ui_displays_content,
            "ui_error": result.ui_error,
            "passed": result.passed,
            "verdict": result.verdict,
            "timestamp": result.timestamp
        })
    
    return report

def print_comprehensive_report(report: Dict):
    """Print formatted comprehensive test report"""
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
    
    for test in report["detailed_results"]:
        status = "✅" if test["passed"] else "❌"
        print(f"\n{status} {test['test_name']}")
        print(f"   Input: '{test['input'][:80]}{'...' if len(test['input']) > 80 else ''}'")
        print(f"   API Status: {test['api_status']}")
        if test['api_error']:
            print(f"   API Error: {test['api_error'][:100]}")
        if test['api_response_summary']:
            summary = test['api_response_summary']
            print(f"   API Response: {summary['plan_steps']} steps, {summary['example_count']} examples")
        print(f"   UI Accessible: {test['ui_accessible']}")
        print(f"   UI Displays Content: {test['ui_displays_content']}")
        if test['ui_error']:
            print(f"   UI Error: {test['ui_error']}")
        print(f"   Verdict: {test['verdict']}")
    
    # Final Verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT")
    print("="*80)
    
    pass_rate = float(summary['pass_rate'].rstrip('%'))
    if pass_rate >= 90:
        verdict = "🟢 EXCELLENT: System is working correctly!"
    elif pass_rate >= 75:
        verdict = "🟡 GOOD: System mostly works but has some issues to address"
    elif pass_rate >= 50:
        verdict = "🟠 NEEDS WORK: System has significant issues that need fixing"
    else:
        verdict = "🔴 CRITICAL: System has major problems that need immediate attention"
    
    print(f"\n{verdict}")
    print(f"\nPass Rate: {summary['pass_rate']} ({summary['passed']}/{summary['total_tests']} tests passed)")
    
    # Key Issues
    failed_tests = [t for t in report["detailed_results"] if not t["passed"]]
    if failed_tests:
        print(f"\n⚠️ KEY ISSUES ({len(failed_tests)} failed tests):")
        for test in failed_tests[:10]:  # Show first 10
            print(f"   - {test['test_name']}: {test['verdict']}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Learning Experience App Test Suite")
    print("Testing: Input → API Response → UI Display\n")
    
    results = run_all_comprehensive_tests()
    report = generate_comprehensive_report(results)
    
    # Save report to file
    with open("comprehensive_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print report
    print_comprehensive_report(report)
    
    # Save markdown report
    with open("COMPREHENSIVE_TEST_REPORT.md", "w") as f:
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
        
        f.write("## Detailed Test Results\n\n")
        f.write("| Test Name | Input | API Status | API Response | UI Accessible | UI Displays | Verdict |\n")
        f.write("|-----------|-------|------------|--------------|---------------|-------------|----------|\n")
        for test in report["detailed_results"]:
            api_resp = ""
            if test['api_response_summary']:
                s = test['api_response_summary']
                api_resp = f"{s['plan_steps']} steps, {s['example_count']} examples"
            elif test['api_error']:
                api_resp = test['api_error'][:50]
            else:
                api_resp = "N/A"
            
            input_short = test['input'][:40] + "..." if len(test['input']) > 40 else test['input']
            status_icon = "✅" if test["passed"] else "❌"
            f.write(f"| {status_icon} {test['test_name']} | {input_short} | {test['api_status']} | {api_resp} | {test['ui_accessible']} | {test['ui_displays_content']} | {test['verdict']} |\n")
    
    print(f"\n💾 Reports saved:")
    print(f"  - comprehensive_test_report.json")
    print(f"  - COMPREHENSIVE_TEST_REPORT.md")
    print("\n" + "="*80)

