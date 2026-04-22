# Task: Refactor Fleet Service — [SERVICE NAME]

## Priority: 🟡 Medium

## Objective
Refactor a fleet service for consistency, error handling, and do_POST support.

## Target Service
- **File**: [path to service script]
- **Port**: [port number]
- **Current issues**: [what needs fixing]

## Refactor Checklist
1. Add `do_POST` handler that delegates to `do_GET` (fleet standard — all services accept both methods)
2. Add proper error handling with try/except around all handlers
3. Add `/status` endpoint returning service name, version, uptime
4. Ensure `Access-Control-Allow-Origin: *` on all responses
5. Ensure `log_message` suppresses verbose output
6. Validate path handlers: live service checks MUST come before static fallback responses
7. Add health check endpoint at `/health` returning 200 OK
8. Test all endpoints after refactoring

## Constraints
- Keep the service as a single Python file (no package splitting)
- Use only stdlib + existing imports
- Maintain backward compatibility with existing API consumers
- Test locally before pushing

## Acceptance Criteria
- All existing endpoints still work
- do_POST works on all interactive endpoints
- /status returns proper JSON
- No import errors or startup crashes
