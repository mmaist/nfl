# Security Cleanup Instructions

## IMMEDIATE ACTIONS REQUIRED:

1. **Change your NFL.com password** - The current password is exposed in git history
2. **Regenerate your bearer token** - Log out and back into pro.nfl.com

## Removing Sensitive Data from Git History

Since .env has been committed previously, you need to remove it from all git history.

### Option 1: Using BFG Repo-Cleaner (Recommended)
```bash
# Install BFG
brew install bfg

# Clone a fresh copy of your repo
git clone --mirror https://github.com/YOUR_USERNAME/nfl.git nfl-mirror
cd nfl-mirror

# Remove .env file from all commits
bfg --delete-files .env

# Clean up the commits
git reflog expire --expire=now --all && git gc --prune=now --aggressive

# Push the cleaned history
git push --force
```

### Option 2: Using git filter-branch
```bash
# Remove .env from all history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push to remote
git push origin --force --all
git push origin --force --tags
```

## After Cleanup:

1. All collaborators must delete their local repos and clone fresh
2. Create a new .env file based on .env.example
3. Use new credentials
4. Never commit .env again

## Preventing Future Issues:

- .env is already in .gitignore
- Always use .env.example for documentation
- Consider using a secrets manager for production