---
name: beads-tracker
description: Manage project issues using the beads CLI issue tracker. Use when user wants to create, list, update, search, or manage issues, tasks, and dependencies.
---

# Beads Issue Tracker

## Purpose
Manage project issues using the beads event-sourced issue tracker. This skill handles creating, listing, updating, searching, and managing dependencies for issues.

## When to use this skill
- User asks to create, list, or search issues
- User wants to see what's ready to work on next
- User needs to update issue status or metadata
- User wants to manage dependencies between issues
- User asks to attach documentation to issues
- User wants to delete or clean up issues

## Core Commands

### List & Discover
```bash
beads list                       # List open issues
beads list --all                 # List all issues (including closed)
beads list --status in_progress  # Filter by status
beads list --label bug           # Filter by label (AND logic)
beads list --label-any bug,feature  # Filter by label (OR logic)
beads list --dep-graph           # Show dependency tree
beads list --labels              # Show labels column
beads list --json                # Output as JSON

beads ready                      # Show next issue to work on (grouped by priority)
beads show <issue-id>            # Show full issue details
beads search "query text"        # Search issues
beads search "query" --title-only  # Search in titles only
beads search "query" --status open --priority high  # Search with filters
```

### Create Issues
```bash
# Basic issue
beads create -t "Title" --data '{"description": "Short summary"}'

# With labels
beads create -t "Title" --data '{"description": "text"}' -l bug,critical

# With dependencies
beads create -t "Title" --data '{"description": "text"}' --depends-on issue-1

# With documentation (note: "name:path" format!)
beads create -t "Title" --data '{"description": "text"}' --doc "spec:path/to/spec.md"

# Full example
beads create -t "Fix critical bug" \
  --data '{"description": "User login fails", "priority": 1}' \
  -l bug,critical \
  --depends-on hd-001 \
  --doc "analysis:bug-report.md"
```

### Update Issues
```bash
beads update <issue-id> --title "New Title"
beads update <issue-id> --status in_progress
beads update <issue-id> --status closed
beads update <issue-id> --status open
beads update <issue-id> --priority high
beads update <issue-id> --kind bug
beads update <issue-id> --data "New description"
```

### Delete Issues
```bash
beads delete <issue-id>                    # Soft delete (interactive)
beads delete <issue-id> --force            # Skip confirmation
beads delete <issue-id> --cascade          # Delete with dependents
beads delete --from-file issue_ids.txt     # Bulk delete from file
```

### Dependencies
```bash
beads dep show <issue-id>                  # Show dependencies both ways
beads dep add <issue-id> <depends-on-id>   # Add dependency
beads dep remove <issue-id> <depends-on-id>  # Remove dependency
```

### Labels
```bash
beads label add <issue-id> <label-name>    # Add label
beads label remove <issue-id> <label-name> # Remove label
beads label list <issue-id>                # List labels on issue
beads label list-all                       # List all labels in database
```

### Documents
```bash
# Add document - just file path, name auto-extracted
beads doc add <issue-id> <file-path>       # Relative path
beads doc add <issue-id> /full/path/to/document.md  # Absolute path

beads doc list <issue-id>                  # List attached docs
beads doc edit <issue-id> <doc-name>       # Export to workspace for editing
beads doc sync <issue-id> <doc-name>       # Sync changes back to blob store
```

### Sync
```bash
beads sync                                 # Apply new events from log
beads sync --full                          # Full sync
```

## Important Conventions

### Priority System
- Priority is a **NUMBER** (not a string!)
- `--priority 1` = High priority (shows first in `beads ready`)
- `--priority 2` = Medium priority
- `--priority 3` = Low priority
- **NOT** "high", "medium", "low" - use numbers!

### Status Values
- `open` - Default for new issues
- `in_progress` - Currently working on it
- `closed` - Completed/resolved

### Data Field - JSON Only
- **CORRECT**: `--data '{"description": "text", "priority": 1}'`
- Priority must be a number, not string
- Must be a JSON object, not a plain string
- Safe fields: type, description, kind, priority

### File Paths & Current Directory
- `beads doc add` uses paths **relative to current directory**
- **Always check `pwd` before adding documents!**
- Use absolute paths if uncertain
- If "File not found": verify with `ls -la <filename>` and check current directory

### Document Attachment - Two Different Syntaxes

**During issue creation (--doc flag):**
```bash
beads create -t "Title" --data '{}' --doc "name:path/to/file.md"
#                                          ^^^^^ name:path format
```

**After issue created (beads doc add):**
```bash
beads doc add <issue-id> path/to/file.md
#                        ^^^^^^^^^^^^^^^ just path, name auto-extracted
```

## Common Workflows

### Complete Issue Workflow
```bash
# 1. See what's next
beads ready

# 2. Start working
beads update <issue-id> --status in_progress

# 3. Do the work...

# 4. Add results/documentation
beads doc add <issue-id> IMPLEMENTATION_SUMMARY.md

# 5. Close issue
beads update <issue-id> --status closed

# 6. See what's next
beads ready
```

### Create Feature with Documentation
```bash
beads create -t "Add user authentication" \
  --data '{"description": "Implement JWT-based auth"}' \
  -l feature,backend \
  --doc "spec:docs/auth-spec.md"
```

### Create Bug with Dependencies
```bash
beads create -t "Fix login redirect" \
  --data '{"description": "Users aren't redirected after login"}' \
  -l bug,critical \
  --depends-on bd-15
```

### Find All Critical Bugs
```bash
beads search "bug" --priority high --kind bug
# OR
beads list --label critical --label bug
```

### Viewing Issue Details
```bash
beads show <issue-id>              # Full issue details
beads doc list <issue-id>          # See attached docs
beads dep show <issue-id>          # See dependencies
beads list --dep-graph             # Visual dependency tree
```

### Efficient Filtering
```bash
beads list --status open --label critical    # Open critical issues
beads list --labels                          # Show labels column
beads search "smali" --status open           # Search open issues only
```

## Pre-execution Checks

Before running beads commands:
1. Check if beads is initialized in the repo: `ls -la .beads/`
2. If not initialized: ask user about prefix before running `beads init --prefix <PREFIX>`
3. Check current directory with `pwd` before document operations
4. Verify file exists with `ls -la <file>` before `beads doc add`

## Verification
- After creating: run `beads show <issue-id>` to verify creation
- After updates: confirm with `beads show <issue-id>` or `beads list`
- After adding docs: run `beads doc list <issue-id>` to confirm attachment
- For dependencies: run `beads list --dep-graph` to see relationships

## Error Handling
- If "File not found" during doc add: verify pwd and file existence
- If priority seems wrong: ensure using numbers (1, 2, 3) not strings
- If command fails: check that beads is initialized (`ls .beads/`)
- If dependency issues: verify both issue IDs exist with `beads show`
