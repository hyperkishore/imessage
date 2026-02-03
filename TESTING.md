# iMessage Sender - Testing Framework

## Test Results Summary
- **Last Run**: 2026-02-02
- **Analysis Type**: Static Code Review & Bug Analysis
- **Critical Path**: Not yet tested (0 automated tests exist)
- **Edge Cases**: Not yet tested
- **Total Bugs Found**: 31 (8 Critical, 12 High, 8 Medium, 3 Low)
- **Test Coverage**: 0% (No test files found)

## Project Structure Analysis

**Detected Type**: Python Flask Web Application
**Test Framework**: None detected (pytest recommended)
**Components Identified**:
- WEB: Flask web interface (`app.py`, `templates/`)
- API: REST API endpoints (`/api/*`)
- DB: SQLite database layer (`database.py`)
- CLI: Agent command-line tool (`agent.py`)
- INT: AppleScript integration (`imessage.py`)

## Critical Path Tests (Not Yet Implemented)

| ID | Journey | Priority | Status | Notes |
|----|---------|----------|--------|-------|
| WEB-1 | User login flow | Critical | ⏳ Pending | Test password authentication, session creation |
| WEB-2 | Sender profile setup | Critical | ⏳ Pending | Test profile creation and validation |
| WEB-3 | Google Sheet preview | Critical | ⏳ Pending | Test sheet URL parsing and CSV fetching |
| WEB-4 | Message template rendering | Critical | ⏳ Pending | Test variable substitution, escaping |
| WEB-5 | Single message send | Critical | ⏳ Pending | Test direct send via AppleScript |
| API-1 | Agent registration | Critical | ⏳ Pending | Test token generation, duplicate prevention |
| API-2 | Agent heartbeat/polling | Critical | ⏳ Pending | Test message queue retrieval |
| API-3 | Message status reporting | Critical | ⏳ Pending | Test status updates (sent/failed) |
| API-4 | Message queueing | Critical | ⏳ Pending | Test queue creation for remote agents |
| DB-1 | Database initialization | Critical | ⏳ Pending | Test schema creation, constraints |
| DB-2 | Concurrent access | Critical | ⏳ Pending | Test SQLite locking under load |
| CLI-1 | Agent startup and registration | Critical | ⏳ Pending | Test config saving, server connection |
| CLI-2 | Agent message processing | Critical | ⏳ Pending | Test polling loop, message sending |
| INT-1 | AppleScript message sending | Critical | ⏳ Pending | Test iMessage integration |
| INT-2 | Messages app detection | Critical | ⏳ Pending | Test app availability check |

## Edge Case Tests (Not Yet Implemented)

| ID | Journey | Priority | Status | Notes |
|----|---------|----------|--------|-------|
| WEB-E1 | Empty sheet URL | Edge | ⏳ Pending | Verify error handling |
| WEB-E2 | Invalid Google Sheets URL | Edge | ⏳ Pending | Verify rejection |
| WEB-E3 | Sheet without phone column | Edge | ⏳ Pending | Verify error message |
| WEB-E4 | Template with missing variables | Edge | ⏳ Pending | Verify graceful handling |
| WEB-E5 | Very long message (>10KB) | Edge | ⏳ Pending | Verify rejection or truncation |
| WEB-E6 | Invalid phone numbers | Edge | ⏳ Pending | Verify validation |
| WEB-E7 | Special characters in message | Edge | ⏳ Pending | Test escaping (quotes, newlines, unicode) |
| WEB-E8 | Duplicate message submissions | Edge | ⏳ Pending | Verify idempotency |
| WEB-E9 | Session expiry during operation | Edge | ⏳ Pending | Verify redirect to login |
| API-E1 | Invalid agent token | Edge | ⏳ Pending | Verify 401 response |
| API-E2 | Missing Authorization header | Edge | ⏳ Pending | Verify 401 response |
| API-E3 | Malformed JSON payload | Edge | ⏳ Pending | Verify 400 response |
| API-E4 | Queue for non-existent agent | Edge | ⏳ Pending | Verify 404 response |
| API-E5 | Duplicate agent registration | Edge | ⏳ Pending | Verify token uniqueness |
| DB-E1 | Database locked error | Edge | ⏳ Pending | Verify retry logic |
| DB-E2 | Corrupt database file | Edge | ⏳ Pending | Verify recovery or error |
| DB-E3 | Full disk space | Edge | ⏳ Pending | Verify graceful error |
| CLI-E1 | Network timeout to server | Edge | ⏳ Pending | Verify reconnection |
| CLI-E2 | Server returns 500 error | Edge | ⏳ Pending | Verify agent continues running |
| CLI-E3 | Agent config file corrupted | Edge | ⏳ Pending | Verify re-registration prompt |
| INT-E1 | Messages app not running | Edge | ⏳ Pending | Verify error message |
| INT-E2 | Messages app crashes during send | Edge | ⏳ Pending | Verify timeout and error |
| INT-E3 | iMessage not configured | Edge | ⏳ Pending | Verify AppleScript error handling |
| INT-E4 | AppleScript injection attempt | Edge | ⏳ Pending | CRITICAL - Verify escaping prevents injection |

## Security Tests (Not Yet Implemented)

| ID | Test | Priority | Status | Notes |
|----|------|----------|--------|-------|
| SEC-1 | SQL Injection in agent lookup | Critical | ⏳ Pending | Test with malicious tokens |
| SEC-2 | CSRF attack on send endpoints | Critical | ⏳ Pending | Verify CSRF protection |
| SEC-3 | Session fixation attack | Critical | ⏳ Pending | Verify session regeneration |
| SEC-4 | Password brute force | Critical | ⏳ Pending | Verify rate limiting |
| SEC-5 | Agent token brute force | Critical | ⏳ Pending | Verify rate limiting |
| SEC-6 | XSS via sheet data | High | ⏳ Pending | Test with `<script>` in cells |
| SEC-7 | XSS via error messages | High | ⏳ Pending | Test with HTML in errors |
| SEC-8 | AppleScript injection | Critical | ⏳ Pending | Test with quotes, newlines, commands |
| SEC-9 | Path traversal in URLs | High | ⏳ Pending | Test malicious sheet URLs |
| SEC-10 | Agent token theft from filesystem | High | ⏳ Pending | Verify file permissions |

## Performance Tests (Not Yet Implemented)

| ID | Test | Priority | Status | Notes |
|----|------|----------|--------|-------|
| PERF-1 | Large sheet (10,000 rows) | Medium | ⏳ Pending | Memory and time limits |
| PERF-2 | Bulk send (1,000 messages) | Medium | ⏳ Pending | Sequential timing |
| PERF-3 | Concurrent agent polling (10 agents) | Medium | ⏳ Pending | Database contention |
| PERF-4 | Slow Google Sheets response | Medium | ⏳ Pending | Timeout handling |
| PERF-5 | Agent offline recovery time | Low | ⏳ Pending | Heartbeat detection |

## Recommended Test Setup

### Install Testing Dependencies
```bash
pip install pytest pytest-cov pytest-flask requests-mock pytest-timeout
```

### Create Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_app.py              # Web endpoint tests
├── test_database.py         # Database layer tests
├── test_agent.py            # Agent CLI tests
├── test_imessage.py         # AppleScript integration tests
├── test_security.py         # Security vulnerability tests
├── test_integration.py      # End-to-end tests
└── fixtures/
    ├── sample_sheet.csv
    └── test_data.json
```

### Run Tests
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_app.py -v

# Run tests matching pattern
pytest -k "test_login" -v

# Run with debugging
pytest --pdb -v
```

## Test Implementation Priorities

### Phase 1: Critical Security Tests
1. Test AppleScript injection (INT-E4, SEC-8)
2. Test CSRF protection (SEC-2)
3. Test rate limiting (SEC-4, SEC-5)
4. Test XSS vulnerabilities (SEC-6, SEC-7)
5. Test authentication bypass attempts (API-E1, API-E2)

### Phase 2: Core Functionality Tests
1. Test login flow (WEB-1)
2. Test message sending (WEB-5, INT-1)
3. Test Google Sheets integration (WEB-3)
4. Test agent registration and polling (API-1, API-2)
5. Test database operations (DB-1)

### Phase 3: Error Handling Tests
1. Test invalid inputs (all E1-E3 tests)
2. Test network failures (CLI-E1, CLI-E2)
3. Test Messages app errors (INT-E1, INT-E2)
4. Test database errors (DB-E1, DB-E2)

### Phase 4: Performance & Load Tests
1. Test with large datasets (PERF-1)
2. Test concurrent access (PERF-3, DB-2)
3. Test bulk operations (PERF-2)

## How to Run Manual Tests

Since automated tests don't exist yet, here's how to manually test:

### Manual Test: Login Flow (WEB-1)
```bash
# Terminal 1: Start server
python app.py

# Terminal 2: Test login
curl -c cookies.txt -X POST http://localhost:5001/login \
  -d "password=changeme" \
  -H "Content-Type: application/x-www-form-urlencoded"

# Verify session cookie is set
cat cookies.txt
```

### Manual Test: Agent Registration (API-1)
```bash
# Register agent
curl -X POST http://localhost:5001/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "phone": "+1234567890"}'

# Expected: {"id": 1, "token": "long-token-string"}
```

### Manual Test: AppleScript Injection (SEC-8)
```bash
# Attempt injection
curl -X POST http://localhost:5001/send-one \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "message": "test\"; tell application \"Finder\" to activate; \""}'

# Verify: Message is sent as literal text, Finder does NOT activate
```

### Manual Test: SQLite Concurrency (DB-2)
```bash
# Terminal 1: Start 5 agents
for i in {1..5}; do
  python agent.py --server http://localhost:5001 \
    --name "Agent $i" --phone "+123456789$i" &
done

# Terminal 2: Queue 100 messages rapidly
for i in {1..100}; do
  curl -X POST http://localhost:5001/api/queue \
    -b cookies.txt \
    -H "Content-Type: application/json" \
    -d "{\"agent_id\": 1, \"phone\": \"+1234567890\", \"message\": \"Test $i\"}"
done

# Check for database lock errors in logs
```

## Code Coverage Targets

Once tests are implemented:
- **Overall Coverage Target**: 80%
- **Critical Security Code**: 100%
- **Database Layer**: 90%
- **API Endpoints**: 85%
- **AppleScript Integration**: 70% (harder to test)

## Continuous Integration

Recommended CI/CD setup (GitHub Actions example):

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: macos-latest  # Required for AppleScript tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Test Data Management

### Test Database
Create separate test database to avoid corrupting production data:

```python
# conftest.py
@pytest.fixture
def test_db():
    import database
    database.DB_PATH = ':memory:'  # Use in-memory SQLite
    database.init_db()
    yield
    # Cleanup happens automatically with in-memory DB
```

### Test Google Sheet
Create a public test sheet with known data:
- URL: https://docs.google.com/spreadsheets/d/TEST_SHEET_ID
- Columns: name, phone, company, notes
- Test data includes: valid phones, invalid phones, special characters

## Known Testing Challenges

1. **AppleScript Testing**: Requires macOS, Messages app configured, real iMessage account
   - Solution: Mock `subprocess.run()` in unit tests, manual testing on real Mac

2. **Google Sheets API**: Tests should not hit real Google Sheets
   - Solution: Use `requests-mock` to mock HTTP responses

3. **SQLite Concurrency**: Hard to reproduce race conditions reliably
   - Solution: Use `threading` to simulate concurrent access in tests

4. **Session Security**: Flask sessions are signed, hard to forge for testing
   - Solution: Use `flask.testing.FlaskClient` with `session_transaction()`

## Bug Verification Checklist

After fixing bugs from BUGS.md, verify with these tests:

- [ ] BUG-001: Test with 1000 invalid tokens, verify rate limit blocks
- [ ] BUG-002: Restart server, verify session remains valid
- [ ] BUG-003: Run concurrent access test, verify no SQLITE_BUSY errors
- [ ] BUG-004: Attempt CSRF attack, verify rejection
- [ ] BUG-005: Try default password, verify rejection or warning
- [ ] BUG-006: Check token file permissions, verify 0600
- [ ] BUG-007: Start without HTTPS in prod mode, verify refusal
- [ ] BUG-008: Send message with injection payload, verify no execution
- [ ] BUG-009: Attempt 100 logins, verify rate limit after N attempts
- [ ] BUG-010: Send to invalid phone, verify validation error
- [ ] BUG-011: Send 100KB message, verify rejection
- [ ] BUG-012: Fetch slow sheet while handling other requests, verify non-blocking
- [ ] BUG-013: Queue 100 messages, verify agent retrieves all via pagination
- [ ] BUG-014: Stop agent, wait 60s, verify UI shows offline
- [ ] BUG-015: Cause send failure, verify retry after delay
- [ ] BUG-016: Trigger error, verify structured log entry exists
- [ ] BUG-017: Sheet with XSS payload, verify escape
- [ ] BUG-018: Check debug mode in production, verify disabled
- [ ] BUG-019: Check CSP headers, verify present
- [ ] BUG-020: Attempt registration without auth, verify rejection
- [ ] BUG-021: Send with Messages app closed, verify auto-start
- [ ] BUG-022: Submit duplicate messages, verify only one queued
- [ ] BUG-023: Submit evil.com URL, verify rejection
- [ ] BUG-024: Fetch malformed CSV, verify graceful error
- [ ] BUG-025: Check old queued messages, verify expiration
- [ ] BUG-026: Queue for invalid agent_id, verify 404
- [ ] BUG-027: Return error with HTML, verify escape
- [ ] BUG-028: Fetch 10,000 row sheet, verify memory limit
- [ ] BUG-029: Check favicon, verify loads
- [ ] BUG-030: Hit /health endpoint, verify 200 OK
- [ ] BUG-031: Check timestamps, verify timezone info

## Next Steps

1. **Immediate**: Implement security tests for critical bugs (Phase 1)
2. **Short-term**: Build core functionality test suite (Phase 2)
3. **Medium-term**: Add error handling and edge case tests (Phase 3)
4. **Long-term**: Set up CI/CD and performance testing (Phase 4)

---

**Note**: This application currently has ZERO automated tests. Before deploying to production, at minimum implement Phase 1 (security tests) and Phase 2 (core functionality tests).
