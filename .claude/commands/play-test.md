# Play-Test Crab Trap Prompts

Test lure prompts from the crab-traps repo against the live MUD.

## Steps
1. Clone `https://github.com/SuperInstance/crab-traps` if not already present
2. Read each prompt in `lures/` directory
3. For each prompt, simulate what an external agent would do:
   - Extract the HTTP URLs from the prompt
   - Execute GET requests to each URL
   - Verify the responses match what the prompt promises
4. Report results for each prompt:
   - ✅ Works: all endpoints return expected data
   - ⚠️ Partial: some endpoints work, some fail
   - ❌ Broken: endpoints return errors or unexpected data
5. Write findings to `for-claude/crab-trap-test-results-YYYY-MM-DD.md`
6. If broken prompts found, fix them and PR to crab-traps

## Key Endpoints to Test
- `/connect?agent=TEST&job=scholar` → should return "connected"
- `/look?agent=TEST` → should return room data with objects and exits
- `/move?agent=TEST&room=bridge` → should return "moved"
- `/interact?agent=TEST&action=examine&target=helm` → should return object description
- `/submit/room-design` POST → should accept valid room designs
