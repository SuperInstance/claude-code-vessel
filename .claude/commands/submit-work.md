# Submit Completed Work

Package and report completed work back to the fleet.

## Steps
1. Check git log for your recent commits (`[CLAUDE-CODE]` prefix)
2. Summarize what was done, files changed, tests added
3. Write a worklog entry in `for-claude/completed/` with today's date
4. Update JOURNAL.md with any new patterns or gotchas discovered
5. Update REBOOT-STATE.md with current state
6. Write a bottle in `from-fleet/` for Oracle1:
   ```
   BOTTLE-FROM-CLAUDE-CODE-YYYY-MM-DD-COMPLETED-TASK.md
   ```
7. Commit and push the vessel repo
8. Submit a PLATO tile via: POST http://147.224.38.131:4042/submit/general
   with category "worklog" and content summarizing the session
