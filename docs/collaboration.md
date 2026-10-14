# Collaboration and repository workflow

This project uses short-lived branches and pull requests to protect `main`, preserve review history, and prevent one developer's local environment from affecting another's.

## Workstation isolation

Each developer should:

- clone the repository into a separate local directory;
- create a local `.venv` after cloning;
- maintain an independent ignored `.env`;
- retrieve approved secrets from the team's private vault;
- request OAuth tokens independently; and
- never copy a personal password, access token, service-key file, or database URL through Git or chat.

A virtual environment should be recreated after the repository moves to another path.

## Start a change

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/<short-description>
```

- `git switch main` selects the protected integration branch.
- `git pull --ff-only` updates it without creating an accidental merge commit.
- `git switch -c` creates an isolated branch for the new work.

Use `fix/`, `docs/`, or `chore/` instead of `feature/` when that better describes the change.

## Validate before commit

```powershell
.\scripts\run_tests.ps1
.\scripts\security_check.ps1
git status --short
git diff --check
git diff
```

Review the complete changed-file list and diff. Confirm that `.env`, local databases, logs, service keys, and generated credentials are absent.

## Commit and push

```powershell
git add <reviewed-files>
git commit -m "Describe the completed change"
git push -u origin feature/<short-description>
```

Prefer an explicit file list over `git add .` when unrelated local changes exist. The `-u` option connects the local branch to its remote branch so later `git push` and `git pull` commands need no branch name.

## Pull request expectations

A pull request should contain:

- the problem and intended outcome;
- the main implementation decisions;
- test and security evidence;
- screenshots for material UI changes;
- integration status changes, including what is still not live;
- deployment or migration instructions when applicable; and
- rollback or failure considerations for risky changes.

At least one teammate should review changes to schemas, approval policy, credentials, deployment manifests, persistence, external integrations, and security boundaries.

## Merge policy

- Keep `main` protected.
- Merge only after required checks and review pass.
- Do not force-push shared branches.
- Do not rewrite another developer's commits without agreement.
- Delete merged remote feature branches when they are no longer needed.
- Pull the updated `main` before starting the next change.

## Suggested ownership

Use [TEAM_TASKS.md](TEAM_TASKS.md) for the current two-developer work split and [ROADMAP.md](ROADMAP.md) for priorities. Ownership does not remove the review requirement for cross-cutting changes.

## Secret incident response

If a credential may have been committed or exposed:

1. stop using it;
2. notify the credential owner privately;
3. revoke or rotate it at the source;
4. inspect access and audit logs;
5. remove it from the repository history using an approved procedure; and
6. document the incident without reproducing the secret.

Deleting a secret from the latest file is not sufficient because it may remain in Git history.
