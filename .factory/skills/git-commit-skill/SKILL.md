---
name: smart-git-commit
description: Stages only the specific files modified during the current session and generates a meaningful semantic commit message.
---

# Smart Git Commit

## Goal
Selectively stage files modified by the agent in the current workflow and commit them with a descriptive, semantic message.

## Instructions

1.  **Identify and Stage Session Changes**
    *   Run `git status` to see all modified or untracked files.
    *   **CRITICAL**: Review your recent conversation history and tool outputs. Identify *only* the specific files you created, modified, or deleted during this session.
    *   Run `git add <file_path_1> <file_path_2> ...` targeting *only* those specific files.
    *   **PROHIBITED**: Do NOT run `git add .` or `git add -A`. Do not stage files that were modified externally unless explicitly asked.

2.  **Verify Staging**
    *   Run `git diff --staged --name-only` to confirm the correct files are staged.
    *   If the output is empty, inform the user that no files matched the session changes and stop.

3.  **Generate Meaningful Commit Message**
    *   Run `git diff --staged` to analyze the actual code changes.
    *   Draft a commit message using the **Conventional Commits** format: `type(scope): description`.
    *   **If a beads issue is available in session history**: Include the issue ID in the description like: `type(scope): [issue-id] description`
    *   **Guidelines for "Meaningful":**
        *   **Type**: Use `feat`, `fix`, `refactor`, `docs`, `style`, or `chore`.
        *   **Scope**: The module or file affected (e.g., `auth`, `navbar`, `utils`).
        *   **Description**: concise summary of the change.
        *   **Body (Optional)**: If the change is non-trivial, add a bullet point explaining *why* the change was made or *how* it solves the problem.
    *   *Example without beads:*
        ```text
        fix(auth): resolve token expiration loop

        - Updated session check to handle 401 errors correctly
        - Cleared local storage on logout
        ```
    *   *Example with beads issue:*
        ```text
        fix(auth): [bd-042] resolve token expiration loop

        - Updated session check to handle 401 errors correctly
        - Cleared local storage on logout
        ```

4.  **Execute Commit**
    *   Run `git commit -m "<message>"`.
    *   Return the commit hash and the full message to the user.
