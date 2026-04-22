# Fleet Task Runner

Read and execute a task from `for-claude/`.

## Steps
1. List all files in `for-claude/` (excluding templates/)
2. If a task file is specified as argument, read that one. Otherwise, read the highest priority task.
3. Parse the task: REPO, GOAL, CONSTRAINTS, ACCEPTANCE CRITERIA
4. Clone the target repo if needed
5. Execute the task following all coding standards in CLAUDE.md
6. Write tests
7. Commit with `[CLAUDE-CODE]` prefix
8. Push to the target repo
9. Update JOURNAL.md with lessons learned
10. Move completed task to `for-claude/completed/`
11. Write REBOOT-STATE.md with current state

## Task Priority
Tasks with 🔴 in the title are highest priority. 🟡 is medium. 🟢 is low.

## If Task Requires Tools You Don't Have
- Deep reasoning → suggest using `kimi-cli --work-dir <repo>`
- Test generation → use `aider` or write manually
- Quick patch → use `crush`
