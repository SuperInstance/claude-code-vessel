# Task: Play-Test Crab Trap Prompt — [PROMPT NAME]

## Priority: 🟢 Low

## Objective
Test a specific lure prompt against the live MUD and report effectiveness.

## Prompt File
`SuperInstance/crab-traps/lures/[category]/[prompt-name].md`

## Test Procedure
1. Read the prompt file
2. Extract all HTTP URLs from the prompt
3. For each URL, execute a GET request
4. Verify the response:
   - Does it match what the prompt promises?
   - Is the response JSON? HTML? Error?
   - Does it contain the expected data fields?
5. Test the full flow the prompt describes:
   - Connect → look → move → examine → think → create → submit
6. Time each step
7. Note any confusing instructions or missing context

## Report Format
```
## Prompt: [name]
## Category: [category]
## Status: ✅/⚠️/❌
## Steps tested: X/Y
## Issues: [list]
## Suggestions: [list]
## Tile quality: [poor/ok/good/excellent]
```

## Acceptance Criteria
- Every URL in the prompt returns valid data
- A naive agent following the prompt can complete the full flow
- No dead ends or 404s
- Report submitted to `for-claude/crab-trap-results/`
