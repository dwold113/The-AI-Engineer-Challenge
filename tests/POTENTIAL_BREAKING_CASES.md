# Potential Breaking Cases

This document lists potential edge cases that could break the app and should be tested.

## Validation Edge Cases

### 1. **Unicode/Special Characters**
- **Risk**: `isalnum()` might fail on certain unicode characters
- **Status**: ✅ Fixed - Added try/except around `isalnum()` check
- **Test Cases**:
  - `学习中文` (Chinese)
  - `café résumé` (accented characters)
  - `тест` (Cyrillic)
  - `🎓📚✨` (emojis)

### 2. **Empty/Whitespace Inputs**
- **Risk**: Empty strings or only spaces could cause issues
- **Status**: ⚠️ Partially handled - validation should reject, but edge cases exist
- **Test Cases**:
  - `""` (empty string)
  - `"   "` (only spaces)
  - `"\n\t"` (newlines/tabs)

### 3. **Very Long Inputs**
- **Risk**: Could exceed token limits or cause timeouts
- **Status**: ⚠️ Not explicitly handled
- **Test Cases**:
  - 500+ character strings
  - Repeated words (100x "learn")

### 4. **Special Characters in Topic Extraction**
- **Risk**: Regex might fail or extract incorrectly
- **Status**: ⚠️ Partially handled
- **Test Cases**:
  - `test@#$%^&*()`
  - `"quotes" and 'apostrophes'`
  - `test\nnewline\ttab`

### 5. **JSON Parsing Failures**
- **Risk**: AI might return invalid JSON
- **Status**: ⚠️ Handled by `parse_json_response()` but could be improved
- **Potential Issues**:
  - Malformed JSON from AI
  - Missing required fields
  - Wrong data types

### 6. **Number Extraction Edge Cases**
- **Risk**: Regex might extract wrong numbers or fail
- **Status**: ⚠️ Basic handling exists
- **Test Cases**:
  - `"give me 100 steps"` (unreasonable)
  - `"give me 0 steps"` (invalid)
  - `"give me -5 steps"` (negative)
  - `"give me 3.5 steps"` (decimal)

## API Endpoint Edge Cases

### 7. **Missing Fields in AI Response**
- **Risk**: AI might not return all expected fields
- **Status**: ⚠️ Partially handled with `.get()` but could fail
- **Potential Issues**:
  - Missing `clean_topic`
  - Missing `is_valid`
  - Missing `plan` in response

### 8. **Expand Step with Invalid Data**
- **Risk**: Missing or invalid step data could break expand
- **Status**: ⚠️ Basic error handling exists
- **Test Cases**:
  - Empty `step_title` or `step_description`
  - Very long step descriptions
  - Special characters in step data

### 9. **Concurrent Requests**
- **Risk**: Multiple simultaneous requests might cause issues
- **Status**: ❌ Not tested
- **Test Cases**:
  - 10+ simultaneous requests
  - Same topic requested multiple times

### 10. **API Timeout**
- **Risk**: Slow AI responses could timeout
- **Status**: ⚠️ 30s timeout exists but might not be enough
- **Potential Issues**:
  - Very complex topics
  - AI API slowdowns

## Data Type Edge Cases

### 11. **Wrong Data Types in Response**
- **Risk**: AI might return wrong types
- **Status**: ⚠️ Partially handled
- **Potential Issues**:
  - `num_steps` as string instead of number
  - `plan` as string instead of array
  - Array items as objects instead of strings

### 12. **None/Null Values**
- **Risk**: Missing values could cause AttributeError
- **Status**: ⚠️ Some handling with `.get()` but not comprehensive
- **Test Cases**:
  - `None` in topic
  - `null` in JSON response

## Security Edge Cases

### 13. **Injection Attempts**
- **Risk**: SQL/XSS injection attempts
- **Status**: ✅ Should be handled by validation
- **Test Cases**:
  - `'; DROP TABLE users; --`
  - `<script>alert('xss')</script>`
  - `"quotes" and 'apostrophes'`

### 14. **Very Large Payloads**
- **Risk**: Large request bodies could cause memory issues
- **Status**: ❌ Not explicitly handled
- **Test Cases**:
  - 10MB+ request body
  - Extremely long topic strings

## Integration Edge Cases

### 15. **OpenAI API Failures**
- **Risk**: API might be down or rate limited
- **Status**: ⚠️ Basic error handling exists
- **Potential Issues**:
  - Rate limiting
  - API downtime
  - Invalid API key

### 16. **Network Issues**
- **Risk**: Network timeouts or failures
- **Status**: ⚠️ httpx handles some, but not all
- **Potential Issues**:
  - Intermittent connectivity
  - DNS failures
  - SSL errors

## Recommendations

1. **Add explicit length limits** for topic input (e.g., max 500 chars)
2. **Improve JSON parsing** with better fallbacks
3. **Add rate limiting** to prevent abuse
4. **Add input sanitization** for special characters
5. **Add comprehensive error logging** for debugging
6. **Add retry logic** for transient API failures
7. **Add validation** for `num_steps` (reasonable range: 1-20)
8. **Add timeout handling** with user-friendly messages

