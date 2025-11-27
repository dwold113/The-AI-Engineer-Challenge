# Learning Experience App - Comprehensive Test Report

Generated: 2025-11-26T10:49:28.347484

## Summary

- **Total Tests**: 30
- **Passed**: 16
- **Failed**: 14
- **Pass Rate**: 53.3%

## Results by Category

### VALID_TOPIC
- Total: 9
- Passed: 0
- Failed: 9
- Pass Rate: 0.0%

### INVALID_TOPIC
- Total: 11
- Passed: 10
- Failed: 1
- Pass Rate: 90.9%

### EDGE_CASE
- Total: 10
- Passed: 6
- Failed: 4
- Pass Rate: 60.0%

## Detailed Test Results

| Test Name | Input | API Status | API Response | UI Accessible | UI Displays | Verdict |
|-----------|-------|------------|--------------|---------------|-------------|----------|
| ❌ Valid: Basic programming topic | Python programming | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Technical topic | Machine Learning | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Popular topic | Web Development | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Practical skill | Cooking Italian food | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Language learning | Spanish language | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Creative skill | Photography basics | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Valid: Topic with step request | how to code give me 3 steps | 400 | THE PHRASE "HOW TO CODE GIVE ME" IS UNCLEAR AND LA | True | False | ❌ FAILED: API returned 400. Error: THE PHRASE "HOW TO CODE GIVE ME" IS UNCLEAR AND LACKS SPECIFICITY. A MORE VALID TOPIC WOULD BE "HOW TO CODE IN PYTHON" OR "HOW TO CODE A SIMPLE WEBSITE." |
| ❌ Valid: Topic with resource request | Python programming give me 10 resources | 400 | THE PHRASE "PYTHON PROGRAMMING GIVE ME" IS INCOMPL | True | False | ❌ FAILED: API returned 400. Error: THE PHRASE "PYTHON PROGRAMMING GIVE ME" IS INCOMPLETE AND LACKS CLARITY. A MORE SPECIFIC TOPIC COULD BE "PYTHON PROGRAMMING BASICS" OR "PYTHON PROGRAMMING FOR DATA ANALYSIS." |
| ❌ Valid: Topic with both requests | Machine Learning give 5 steps and 8 exam... | 400 | THE PHRASE "MACHINE LEARNING GIVE AND" IS INCOMPLE | True | False | ❌ FAILED: API returned 400. Error: THE PHRASE "MACHINE LEARNING GIVE AND" IS INCOMPLETE AND NONSENSICAL. A MORE SPECIFIC TOPIC COULD BE "MACHINE LEARNING ALGORITHMS" OR "APPLICATIONS OF MACHINE LEARNING." |
| ✅ Invalid: Gibberish | gfdnjlg nfgdsgdnjklgfnjs | 400 | GIBBERISH/NONSENSE. PLEASE PROVIDE A REAL, MEANING | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: GIBBERISH/NONSENSE. PLEASE PROVIDE A REAL, MEANINGFUL TOPIC FOR ANALYSIS. |
| ✅ Invalid: Abstract/philosophical | the meaning of life | 400 | TOO ABSTRACT AND PHILOSOPHICAL; CONSIDER FOCUSING  | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: TOO ABSTRACT AND PHILOSOPHICAL; CONSIDER FOCUSING ON SPECIFIC PHILOSOPHICAL THEORIES OR SCHOOLS OF THOUGHT, SUCH AS "EXISTENTIALISM" OR "EASTERN PHILOSOPHY." |
| ✅ Invalid: Random characters | asdfghjkl | 400 | RANDOM KEYBOARD MASHING; CONSIDER TOPICS LIKE "TOU | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: RANDOM KEYBOARD MASHING; CONSIDER TOPICS LIKE "TOUCH TYPING" OR "KEYBOARD SHORTCUTS" FOR A MORE STRUCTURED LEARNING APPROACH. |
| ✅ Invalid: Just numbers | 123456 | 400 | Please use words to describe what you want to lear | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: Please use words to describe what you want to learn, not just symbols or numbers. |
| ✅ Invalid: Too vague | stuff | 400 | TOO VAGUE. PLEASE SPECIFY A MORE CONCRETE TOPIC, S | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: TOO VAGUE. PLEASE SPECIFY A MORE CONCRETE TOPIC, SUCH AS "PHOTOGRAPHY TECHNIQUES" OR "BASIC COOKING SKILLS." |
| ✅ Invalid: Empty string |  | 400 | Please enter a topic you want to learn about. | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: Please enter a topic you want to learn about. |
| ✅ Invalid: Single character | a | 400 | Topic is too short. Please provide more details. | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: Topic is too short. Please provide more details. |
| ✅ Invalid: Only special characters | !!!### | 400 | Please provide a meaningful topic, not just repeat | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: Please provide a meaningful topic, not just repeated characters. |
| ❌ Invalid: Copyrighted content | marvel universe | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ✅ Invalid: Animation request | gif of dancing boy | 400 | THE TOPIC "GIF OF DANCING BOY" IS TOO VAGUE AND LA | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THE TOPIC "GIF OF DANCING BOY" IS TOO VAGUE AND LACKS A CLEAR LEARNING OBJECTIVE. A MORE SPECIFIC TOPIC COULD BE "CREATING ANIMATED GIFS USING PHOTOSHOP" OR "THE CULTURAL SIGNIFICANCE OF VIRAL DANCE GIFS." |
| ✅ Invalid: Specific person | jaxson dart running | 400 | THE TERM "JAXSON DART RUNNING" DOES NOT APPEAR TO  | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THE TERM "JAXSON DART RUNNING" DOES NOT APPEAR TO REFER TO A RECOGNIZED TOPIC OR CONCEPT. IT MAY BE A COMBINATION OF UNRELATED WORDS OR A SPECIFIC REFERENCE THAT LACKS CLARITY. A SUGGESTION WOULD BE TO CLARIFY THE INTENDED SUBJECT, SUCH AS "RUNNING TECHNIQUES" OR "DART THROWING SKILLS." |
| ✅ Edge case: Very long topic (201 chars) | AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA... | 400 | Topic is too long. Please keep it under 200 charac | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: Topic is too long. Please keep it under 200 characters. |
| ✅ Edge case: Unreasonable resource count | Python programming give me 100 resources | 400 | THE PHRASE "PYTHON PROGRAMMING GIVE ME" IS NOT A C | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THE PHRASE "PYTHON PROGRAMMING GIVE ME" IS NOT A COMPLETE OR COHERENT TOPIC FOR LEARNING. IT LACKS SPECIFICITY AND CLARITY. A MORE VALID TOPIC WOULD BE "PYTHON PROGRAMMING BASICS" OR "PYTHON PROGRAMMING FOR DATA ANALYSIS." |
| ✅ Edge case: Unreasonable step count | Machine Learning give me 50 steps | 400 | THE PHRASE "MACHINE LEARNING GIVE ME" IS INCOMPLET | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THE PHRASE "MACHINE LEARNING GIVE ME" IS INCOMPLETE AND LACKS CLARITY. A MORE SPECIFIC TOPIC COULD BE "MACHINE LEARNING ALGORITHMS" OR "MACHINE LEARNING APPLICATIONS." |
| ✅ Edge case: Too few steps | Web Development give me 1 step | 400 | THE PHRASE "WEB DEVELOPMENT GIVE ME" IS INCOMPLETE | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THE PHRASE "WEB DEVELOPMENT GIVE ME" IS INCOMPLETE AND LACKS CLARITY. A MORE SPECIFIC TOPIC COULD BE "WEB DEVELOPMENT BASICS" OR "LEARNING HTML AND CSS." |
| ❌ Edge case: Special characters | C++ programming | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
| ❌ Edge case: Unicode characters | 日本語を学ぶ | 400 | Please use words to describe what you want to lear | True | False | ❌ FAILED: API returned 400. Error: Please use words to describe what you want to learn, not just symbols or numbers. |
| ✅ Edge case: SQL injection attempt | '; DROP TABLE users; -- | 400 | THIS INPUT IS A SQL INJECTION ATTACK STRING, WHICH | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THIS INPUT IS A SQL INJECTION ATTACK STRING, WHICH IS NOT A VALID LEARNING TOPIC. INSTEAD, CONSIDER LEARNING ABOUT "SQL INJECTION PREVENTION TECHNIQUES" OR "DATABASE SECURITY BEST PRACTICES." |
| ✅ Edge case: XSS attempt | <script>alert('xss')</script> | 400 | THIS TOPIC IS A CODE SNIPPET RELATED TO A SECURITY | True | False | ✅ CORRECTLY REJECTED: API returned 400 as expected. Error: THIS TOPIC IS A CODE SNIPPET RELATED TO A SECURITY VULNERABILITY (CROSS-SITE SCRIPTING - XSS) BUT LACKS CONTEXT. A MORE SPECIFIC AND STRUCTURED TOPIC COULD BE "UNDERSTANDING AND PREVENTING CROSS-SITE SCRIPTING (XSS) ATTACKS." |
| ❌ Edge case: Very short but valid | AI | 400 | Please provide a meaningful topic, not just repeat | True | False | ❌ FAILED: API returned 400. Error: Please provide a meaningful topic, not just repeated characters. |
| ❌ Edge case: Numbers in topic | Python 3 programming | None | Timeout:  | False | False | ❌ TIMEOUT: Request timed out after 30 seconds |
