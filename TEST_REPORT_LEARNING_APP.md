# Learning Experience App - Comprehensive Test Report

Generated: 2025-11-26T10:32:49.991940

## Summary

- **Total Tests**: 40
- **Passed**: 24
- **Failed**: 16
- **Pass Rate**: 60.0%

## Results by Category

### BACKEND
- Total: 13
- Passed: 12
- Failed: 1
- Pass Rate: 92.3%

### LEARNING_FLOW
- Total: 19
- Passed: 8
- Failed: 11
- Pass Rate: 42.1%

### EXPAND_STEP
- Total: 3
- Passed: 2
- Failed: 1
- Pass Rate: 66.7%

### FRONTEND
- Total: 2
- Passed: 0
- Failed: 2
- Pass Rate: 0.0%

### PERFORMANCE
- Total: 3
- Passed: 2
- Failed: 1
- Pass Rate: 66.7%

## All Test Results

| Test Name | Category | Status | Details |
|-----------|----------|--------|----------|
| Root endpoint accessible | backend | ✅ PASS | Status: 200. All expected fields present: ['status', 'app'] |
| API key configured check | backend | ✅ PASS | Status: 200 |
| Valid topic: Python programming | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: Machine Learning | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: Web Development | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: Cooking Italian food | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: Spanish language | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: Photography basics | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Valid topic: 3 steps requested | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Valid topic: 10 resources requested | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Valid topic: Both specified | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Invalid topic rejected: Gibberish | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Abstract concept | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Random chars | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Just numbers | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Too vague | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Empty string | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Single character | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Only special chars | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Copyrighted content | backend | ❌ FAIL | Status: 200 |
| Invalid topic rejected: GIF request | backend | ✅ PASS | Status: 400 |
| Invalid topic rejected: Specific person | backend | ✅ PASS | Status: 400 |
| Edge case: Very long topic | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Unreasonable resource count | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Unreasonable step count | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Too few steps | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Special characters in topic | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Edge case: Unicode characters | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: SQL injection attempt | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: XSS attempt | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Very short valid | learning_flow | ❌ FAIL | Failed to create plan. Status: 400 |
| Edge case: Numbers in valid topic | learning_flow | ✅ PASS | Plan steps: 7, Examples: 5 |
| Expand first step | expand_step | ✅ PASS | Successfully expanded step 1 |
| Expand middle step | expand_step | ✅ PASS | Successfully expanded step 3 |
| Expand with invalid step | expand_step | ❌ FAIL | Step index 999 out of range (plan has 7 steps) |
| Frontend loads | frontend | ❌ FAIL | Missing UI elements: ['Start Learning button', 'Input field'] |
| Frontend has learning interface | frontend | ❌ FAIL | Missing UI elements: ['Start Learning button', 'Input field'] |
| Fast response | performance | ✅ PASS | Status: 200, Duration: 19.58s |
| Medium topic | performance | ✅ PASS | Status: 200, Duration: 20.96s |
| Complex topic | performance | ❌ FAIL | Exception:  |
