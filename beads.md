

# Beads CLI - Issue Management Cheatsheet

## Getting Started

### Initialize Repository
```bash
beads init --prefix <PREFIX>    # e.g., beads init --prefix proj
```

## Core Issue Commands

### Create Issue
```bash
# Basic issue with JSON data
beads create -t "Title" --data '{"description": "Short summary"}'

# With labels
beads create -t "Title" --data '{"description": "Short summary"}' -l bug,critical

# With dependencies
beads create -t "Title" --data '{"description": "Detailed explanation"}' \
  --depends-on issue-1 --depends-on issue-2

# With documentation (note the "name:path" format!)
beads create -t "Title" --data '{"description": "Detailed explanation"}' \
  --doc "spec:path/to/spec.md"

# Full example with everything
beads create -t "Fix critical bug" \
  --data '{"description": "User login fails", "priority": 1}' \
  -l bug,critical \
  --depends-on hd-001 \
  --doc "analysis:bug-report.md"
```


### List Issues
```bash
beads list                       # List open issues
beads list --all                # List all issues (including closed)
beads list --status in_progress # Filter by status
beads list --label bug          # Filter by label (AND - must have ALL)
beads list --label-any bug,feature  # Filter by label (OR - at least ONE)
beads list --dep-graph          # Show dependency tree
beads list --labels             # Show labels column
beads list --json               # Output as JSON
```

### Show Issue Details
```bash
beads show <issue-id>           # e.g., beads show bd-10
```

### Update Issue
```bash
beads update <issue-id> --title "New Title"
beads update <issue-id> --status in_progress
beads update <issue-id> --priority high
beads update <issue-id> --kind bug
beads update <issue-id> --data "New description"
```

### Delete Issues
```bash
beads delete <issue-id>                    # Soft delete (interactive)
beads delete <issue-id> --force            # Skip confirmation
beads delete <issue-id> --cascade          # Delete with dependents
beads delete --from-file issue_ids.txt     # Delete from file
```

## Search & Discovery

### Search Issues
```bash
beads search "query text"
beads search "query" --title-only
beads search "query" --kind bug
beads search "query" --status open
beads search "query" --priority high
```

### Ready to Work
```bash
beads ready                      # Show next issue to work on (grouped by priority)
```

## Dependency Management

### Show Dependencies
```bash
beads dep show <issue-id>        # Show what this issue depends on & what depends on it
```

### Add Dependency
```bash
beads dep add <issue-id> <depends-on-id>  # This issue depends on another
```

### Remove Dependency
```bash
beads dep remove <issue-id> <depends-on-id>
```

## Label Management

### Add/Remove Labels
```bash
beads label add <issue-id> <label-name>
beads label remove <issue-id> <label-name>
```

### List Labels
```bash
beads label list <issue-id>      # List labels on specific issue
beads label list-all             # List all labels in database
```

## Document Management

### Add Document
```bash
# IMPORTANT: Syntax differs from --doc flag in create command!
beads doc add <issue-id> <file-path>        # Just file path, name auto-extracted

# Examples:
beads doc add hd-002 IMPLEMENTATION_SUMMARY.md           # Relative path
beads doc add hd-002 /full/path/to/document.md           # Absolute path

# NOTE: When creating issue, use different format:
beads create -t "Title" --data '{}' --doc "name:path/to/file.md"
#                                          ^^^^^ name:path format only for create!
```

### List Documents
```bash
beads doc list <issue-id>                   # See all attached docs
```

### Edit Document
```bash
beads doc edit <issue-id> <doc-name>        # Export to workspace for editing
```

### Sync Document
```bash
beads doc sync <issue-id> <doc-name>        # Sync changes back to blob store
```

## Sync & Maintenance

### Sync Database
```bash
beads sync                       # Apply new events from log
beads sync --full                # Full sync
```

## Common Workflows

### Create Feature with Documentation
```bash
beads create -t "Add user authentication" \
  --data "Implement JWT-based auth" \
  -l feature,backend \
  --doc "spec:docs/auth-spec.md"
```

### Create Bug with Dependencies
```bash
beads create -t "Fix login redirect" \
  --data "Users aren't redirected after login" \
  -l bug,critical \
  --depends-on bd-15
```

### Start Working on Next Issue
```bash
beads ready                      # Find next issue
beads update bd-42 --status in_progress
```

### Complete Issue
```bash
beads update bd-42 --status closed
```

### Find All Critical Bugs
```bash
beads search "bug" --priority high --kind bug
# or
beads list --label critical --label bug
```

---

## Important Gotchas & Clarifications

### Priority System
```bash
# Priority is a NUMBER (not a string!)
--priority 1    # High priority (shows first in beads ready)
--priority 2    # Medium priority
--priority 3    # Low priority

# NOT "high", "medium", "low" - use numbers!
```

### Status Values
```bash
--status open          # Default for new issues
--status in_progress   # Currently working on it
--status closed        # Completed/resolved
```

### Data Field - JSON Only
```bash
# CORRECT: Use proper JSON
beads create -t "Title" --data '{"description": "text", "priority": 1}'
                                                          ^^^ number, not string

# WRONG: These will fail
beads create -t "Title" --data "Simple string"           # Must be JSON object
beads update hd-001 --data '{"notes": "some note"}'      # "notes" not in schema

# Safe fields for --data:
# - type, description, kind, priority (as number)
# - Custom fields depend on your schema
```

### File Paths & Current Directory
```bash
# beads doc add uses paths relative to current directory
pwd                    # Check where you are first!
cd /path/to/project    # Navigate to project root
beads doc add hd-002 SUMMARY.md    # Uses current dir

# Or use absolute paths:
beads doc add hd-002 /full/path/to/file.md
```

### Document Attachment - Two Different Syntaxes

**During Issue Creation (--doc flag):**
```bash
beads create -t "Title" --data '{}' --doc "name:path/to/file.md"
#                                          ^^^^^ name:path format
```

**After Issue Created (beads doc add):**
```bash
beads doc add <issue-id> path/to/file.md
#                        ^^^^^^^^^^^^^^^ just path, name auto-extracted from filename
```

### Working Directory Matters!
```bash
# If beads doc add says "File not found":
ls -la MYFILE.md       # Check file exists in current dir
pwd                    # Verify you're in the right directory
cd /correct/path       # Navigate to where file is
beads doc add hd-001 MYFILE.md   # Try again
```

---

## Lessons Learned (Real Usage)

### Complete Issue Workflow
```bash
# 1. See what's next
beads ready

# 2. Start working
beads update hd-003 --status in_progress

# 3. Do the work...

# 4. Add results/documentation
beads doc add hd-003 IMPLEMENTATION_SUMMARY.md

# 5. Close issue
beads update hd-003 --status closed

# 6. See what's next
beads ready
```

### Viewing Issue Details
```bash
beads show hd-003              # Full issue details
beads doc list hd-003          # See attached docs
beads dep show hd-003          # See dependencies
beads list --dep-graph         # Visual dependency tree
```

### Efficient Filtering
```bash
beads list --status open --label critical    # Open critical issues
beads list --labels                           # Show labels column
beads search "smali" --status open            # Search open issues only
```

