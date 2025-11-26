#!/usr/bin/env python3
"""
Comprehensive test suite for AI Background Generator API
Tests both prompt validation and image upload scenarios
"""

import httpx
import json
import os
from typing import Dict, List, Tuple
from pathlib import Path

# API endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000")
GENERATE_ENDPOINT = f"{API_URL}/api/generate-image"

# Test results storage
results = {
    "prompt_tests": [],
    "upload_tests": [],
    "summary": {}
}

def test_prompt(prompt: str, expected_result: str, category: str) -> Dict:
    """Test a prompt and return the result"""
    print(f"\n{'='*60}")
    print(f"Testing: {category}")
    print(f"Prompt: '{prompt}'")
    print(f"Expected: {expected_result}")
    print(f"{'='*60}")
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                GENERATE_ENDPOINT,
                json={"prompt": prompt}
            )
        
        status_code = response.status_code
        is_success = status_code == 200
        
        if is_success:
            data = response.json()
            has_image = "image_url" in data and data["image_url"].startswith("data:image")
            result = {
                "prompt": prompt,
                "category": category,
                "expected": expected_result,
                "actual": "SUCCESS - Image generated",
                "status_code": status_code,
                "passed": expected_result == "SUCCESS",
                "has_image": has_image
            }
        else:
            try:
                error_detail = response.json().get("detail", response.text)
            except:
                error_detail = response.text[:200]
            
            result = {
                "prompt": prompt,
                "category": category,
                "expected": expected_result,
                "actual": f"FAILED - {error_detail}",
                "status_code": status_code,
                "passed": expected_result == "FAILED",
                "error_detail": error_detail
            }
        
        print(f"Result: {result['actual']}")
        print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
        
        return result
        
    except httpx.RequestError as e:
        result = {
            "prompt": prompt,
            "category": category,
            "expected": expected_result,
            "actual": f"ERROR - {str(e)}",
            "status_code": None,
            "passed": False,
            "error": str(e)
        }
        print(f"Result: {result['actual']}")
        print(f"Status: ❌ ERROR")
        return result

def test_upload(file_path: str, expected_result: str, category: str) -> Dict:
    """Test file upload (simulated - actual upload requires frontend)"""
    print(f"\n{'='*60}")
    print(f"Testing: {category}")
    print(f"File: {file_path}")
    print(f"Expected: {expected_result}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        result = {
            "file": file_path,
            "category": category,
            "expected": expected_result,
            "actual": "SKIPPED - File not found",
            "passed": None,
            "note": "Upload testing requires actual files. This is a simulation."
        }
        print(f"Result: {result['actual']}")
        return result
    
    # Check file size
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    
    # Check file extension
    ext = Path(file_path).suffix.lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    is_valid_type = ext in valid_extensions
    
    # Simulate frontend validation
    if not is_valid_type:
        result = {
            "file": file_path,
            "category": category,
            "expected": expected_result,
            "actual": "FAILED - Invalid file type (frontend validation)",
            "passed": expected_result == "FAILED",
            "file_size_mb": round(file_size_mb, 2),
            "file_type": ext
        }
    elif file_size > 10 * 1024 * 1024:
        result = {
            "file": file_path,
            "category": category,
            "expected": expected_result,
            "actual": "FAILED - File too large (>10MB, frontend validation)",
            "passed": expected_result == "FAILED",
            "file_size_mb": round(file_size_mb, 2),
            "file_type": ext
        }
    else:
        result = {
            "file": file_path,
            "category": category,
            "expected": expected_result,
            "actual": "SUCCESS - File would be accepted (frontend validation)",
            "passed": expected_result == "SUCCESS",
            "file_size_mb": round(file_size_mb, 2),
            "file_type": ext
        }
    
    print(f"Result: {result['actual']}")
    print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL' if result['passed'] is not None else '⚠️  SKIP'}")
    
    return result

def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("AI BACKGROUND GENERATOR - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # ========== PROMPT VALIDATION TESTS ==========
    print("\n\n📝 TESTING PROMPT VALIDATION")
    print("="*60)
    
    prompt_tests = [
        # Valid prompts - should succeed
        ("a serene mountain landscape at sunset", "SUCCESS", "Valid - Clear visual scene"),
        ("cyberpunk cityscape with neon lights at night", "SUCCESS", "Valid - Descriptive scene"),
        ("tropical beach with palm trees and turquoise water", "SUCCESS", "Valid - Detailed landscape"),
        ("abstract geometric patterns in blue and purple", "SUCCESS", "Valid - Abstract but visual"),
        ("cozy coffee shop interior with warm lighting", "SUCCESS", "Valid - Interior scene"),
        ("futuristic space station orbiting a planet", "SUCCESS", "Valid - Sci-fi scene"),
        ("vintage library with bookshelves and reading nook", "SUCCESS", "Valid - Detailed interior"),
        ("aurora borealis over snowy mountains", "SUCCESS", "Valid - Natural phenomenon"),
        
        # Invalid prompts - should fail (abstract/philosophical)
        ("Open weights. Infinite possibilities. The freedom to run anywhere", "FAILED", "Invalid - Abstract/philosophical"),
        ("the meaning of life", "FAILED", "Invalid - Philosophical concept"),
        ("a feeling of joy", "FAILED", "Invalid - Emotion, not visual"),
        ("the concept of time", "FAILED", "Invalid - Abstract concept"),
        ("freedom and liberty", "FAILED", "Invalid - Abstract concepts"),
        ("success and achievement", "FAILED", "Invalid - Abstract concepts"),
        
        # Invalid prompts - should fail (too short/nonsensical)
        ("ab", "FAILED", "Invalid - Too short (< 3 chars)"),
        ("a", "FAILED", "Invalid - Single word"),
        ("test", "FAILED", "Invalid - Nonsensical single word"),
        ("dummy", "FAILED", "Invalid - Test word"),
        ("asdf", "FAILED", "Invalid - Nonsensical"),
        ("qwerty", "FAILED", "Invalid - Keyboard mashing"),
        
        # Invalid prompts - should fail (repeated characters)
        ("aaaaaaaaaaaa", "FAILED", "Invalid - Repeated characters"),
        ("111111111111", "FAILED", "Invalid - Repeated numbers"),
        ("@@@@@@@@@@@@", "FAILED", "Invalid - Repeated symbols"),
        
        # Invalid prompts - should fail (only special chars)
        ("!!!@@@###$$$", "FAILED", "Invalid - Only special characters"),
        ("123456789", "FAILED", "Invalid - Only numbers"),
        
        # Edge cases - should succeed (creative but visual)
        ("minimalist workspace with plants", "SUCCESS", "Edge - Minimal but visual"),
        ("dark forest with glowing mushrooms", "SUCCESS", "Edge - Fantasy but visual"),
        ("underwater coral reef with tropical fish", "SUCCESS", "Edge - Underwater scene"),
        
        # Edge cases - borderline (may succeed or fail depending on AI)
        ("peaceful meditation space", "SUCCESS", "Edge - Abstract but can be visualized"),
        ("energetic dance floor", "SUCCESS", "Edge - Action but visual"),
    ]
    
    for prompt, expected, category in prompt_tests:
        result = test_prompt(prompt, expected, category)
        results["prompt_tests"].append(result)
    
    # ========== UPLOAD VALIDATION TESTS ==========
    print("\n\n📸 TESTING IMAGE UPLOAD VALIDATION")
    print("="*60)
    
    # Note: These are simulated since actual upload requires frontend
    # In real testing, you'd need actual image files
    upload_tests = [
        ("test_image.jpg", "SUCCESS", "Valid - JPEG image"),
        ("test_image.png", "SUCCESS", "Valid - PNG image"),
        ("test_image.gif", "SUCCESS", "Valid - GIF image"),
        ("test_image.webp", "SUCCESS", "Valid - WebP image"),
        ("test_document.pdf", "FAILED", "Invalid - PDF file"),
        ("test_video.mp4", "FAILED", "Invalid - Video file"),
        ("test_text.txt", "FAILED", "Invalid - Text file"),
    ]
    
    for file_path, expected, category in upload_tests:
        result = test_upload(file_path, expected, category)
        results["upload_tests"].append(result)
    
    # ========== GENERATE SUMMARY ==========
    generate_summary()

def generate_summary():
    """Generate test summary"""
    print("\n\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    # Prompt test summary
    prompt_total = len(results["prompt_tests"])
    prompt_passed = sum(1 for t in results["prompt_tests"] if t.get("passed") == True)
    prompt_failed = sum(1 for t in results["prompt_tests"] if t.get("passed") == False)
    prompt_errors = sum(1 for t in results["prompt_tests"] if t.get("passed") is None)
    
    print(f"\n📝 PROMPT VALIDATION TESTS:")
    print(f"   Total: {prompt_total}")
    print(f"   ✅ Passed: {prompt_passed}")
    print(f"   ❌ Failed: {prompt_failed}")
    print(f"   ⚠️  Errors: {prompt_errors}")
    print(f"   Success Rate: {(prompt_passed/prompt_total*100):.1f}%")
    
    # Upload test summary
    upload_total = len(results["upload_tests"])
    upload_passed = sum(1 for t in results["upload_tests"] if t.get("passed") == True)
    upload_failed = sum(1 for t in results["upload_tests"] if t.get("passed") == False)
    upload_skipped = sum(1 for t in results["upload_tests"] if t.get("passed") is None)
    
    print(f"\n📸 UPLOAD VALIDATION TESTS:")
    print(f"   Total: {upload_total}")
    print(f"   ✅ Passed: {upload_passed}")
    print(f"   ❌ Failed: {upload_failed}")
    print(f"   ⚠️  Skipped: {upload_skipped}")
    
    # Category breakdown
    print(f"\n📋 RESULTS BY CATEGORY:")
    
    categories = {}
    for test in results["prompt_tests"]:
        cat = test["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0}
        categories[cat]["total"] += 1
        if test.get("passed") == True:
            categories[cat]["passed"] += 1
        elif test.get("passed") == False:
            categories[cat]["failed"] += 1
    
    for cat, stats in sorted(categories.items()):
        pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"   {cat}:")
        print(f"      {stats['passed']}/{stats['total']} passed ({pass_rate:.1f}%)")
    
    # Failed tests details
    failed_tests = [t for t in results["prompt_tests"] if t.get("passed") == False]
    if failed_tests:
        print(f"\n❌ FAILED TESTS DETAILS:")
        for test in failed_tests:
            print(f"   • {test['category']}")
            print(f"     Prompt: '{test['prompt']}'")
            print(f"     Expected: {test['expected']}, Got: {test['actual']}")
            if 'error_detail' in test:
                print(f"     Error: {test['error_detail'][:100]}")
    
    # Unexpected successes (should have failed but didn't)
    unexpected_successes = [
        t for t in results["prompt_tests"] 
        if t.get("expected") == "FAILED" and t.get("status_code") == 200
    ]
    if unexpected_successes:
        print(f"\n⚠️  UNEXPECTED SUCCESSES (should have failed):")
        for test in unexpected_successes:
            print(f"   • {test['category']}")
            print(f"     Prompt: '{test['prompt']}'")
            print(f"     This should have been rejected but was accepted!")
    
    # Unexpected failures (should have succeeded but didn't)
    unexpected_failures = [
        t for t in results["prompt_tests"] 
        if t.get("expected") == "SUCCESS" and t.get("passed") == False
    ]
    if unexpected_failures:
        print(f"\n⚠️  UNEXPECTED FAILURES (should have succeeded):")
        for test in unexpected_failures:
            print(f"   • {test['category']}")
            print(f"     Prompt: '{test['prompt']}'")
            print(f"     Error: {test.get('error_detail', test.get('actual', 'Unknown'))[:100]}")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Full results saved to: test_results.json")
    print("\n" + "="*60)

if __name__ == "__main__":
    # Check if API is running
    try:
        with httpx.Client(timeout=5.0) as client:
            health_check = client.get(f"{API_URL}/")
        print(f"✅ API is running at {API_URL}")
    except:
        print(f"❌ ERROR: Cannot connect to API at {API_URL}")
        print("   Make sure the backend is running:")
        print("   uv run uvicorn api.backend:app --reload")
        exit(1)
    
    run_all_tests()

