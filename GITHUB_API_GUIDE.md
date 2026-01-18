# GitHub API Guide for AI Assistants

This guide documents how to fetch complete GitHub PR feedback using the GitHub REST API. It's designed to be repository-agnostic and can be copied to any project.

## Three Types of PR Feedback

When reviewing a PR, you should always fetch **all three types** of feedback:

1. **PR Details** - Metadata, stats, description, author, branch info
2. **General Comments** - PR-level comments (not tied to specific code lines)
3. **Review Comments** - Line-specific code review comments

The helper script automatically fetches all three types.

## Environment Variables

The following environment variables should be configured:

- `GITHUB_TOKEN` - GitHub Personal Access Token (format: `ghp_...` or `github_pat_...`)
- `GITHUB_REPO` - Repository in format `owner/repo` (e.g., `myorg/myproject`)
- `GITHUB_API_BASE` - GitHub API base URL (default: `https://api.github.com`)

## Quick Start

### Using the Helper Script

The helper script automatically fetches all three types of PR feedback: details, general comments, and review comments.

```bash
# Make script executable (first time only)
chmod +x fetch-pr-comments.sh

# List 20 most recent PRs
./fetch-pr-comments.sh list

# Search for PRs by branch name (client-side, first 100 PRs)
./fetch-pr-comments.sh search "feature-branch"

# Search using GitHub Search API (server-side, comprehensive)
./fetch-pr-comments.sh api-search "feature-branch"

# Fetch all three types of feedback for specific PR
./fetch-pr-comments.sh 68

# Fetch all feedback for PR of current branch
./fetch-pr-comments.sh current
```

### Direct API Calls

#### Authentication Header Format ⚠️ IMPORTANT

**Use `Bearer` token format** (NOT `token`):

```bash
-H "Authorization: Bearer $GITHUB_TOKEN"
```

#### Required Headers

```bash
-H "Accept: application/vnd.github+json"
-H "Authorization: Bearer $GITHUB_TOKEN"
-H "X-GitHub-Api-Version: 2022-11-28"
-H "Content-Type: application/json"  # For POST/PATCH/PUT requests
```

## Common Operations

### 1. List Pull Requests

```bash
curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls?state=all&per_page=20"
```

**Note**: This returns only the first 20 results. Use pagination or increase `per_page` (max 100) for more.

### 2. Search PRs - Client-Side Filtering

This method fetches PRs and filters them locally. **Limitation**: Only searches the fetched results (up to 100).

```bash
curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls?state=all&per_page=100" \
  | python3 << 'PYEOF'
import json, sys

search_term = "your-search-term"  # Replace with actual search term
prs = json.load(sys.stdin)

for pr in prs:
    if search_term.lower() in pr['head']['ref'].lower():
        print(f"PR #{pr['number']}: {pr['title']}")
        print(f"Branch: {pr['head']['ref']}")
        print(f"URL: {pr['html_url']}")
        print()
PYEOF
```

### 3. Search PRs - GitHub Search API (Recommended)

For large repositories or comprehensive searches, use the **GitHub Search API**. This performs server-side filtering and searches across all PRs.

```bash
# Search for PRs with "feature" in the branch name
SEARCH_TERM="feature"
QUERY="repo:$GITHUB_REPO is:pr $SEARCH_TERM in:branch"

curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/search/issues?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")&per_page=20"
```

**Benefits of Search API**:
- Searches all PRs in the repository, not just recent ones
- Server-side filtering is more efficient
- Supports complex queries (e.g., `is:open`, `author:username`, `label:bug`)

**Search query syntax**:
- `repo:owner/repo` - Specify repository
- `is:pr` - Limit to pull requests
- `is:open` or `is:closed` - Filter by state
- `author:username` - Filter by author
- `label:labelname` - Filter by label
- `created:>=2024-01-01` - Filter by date
- `in:branch` or `in:title` - Where to search

Example complex query:
```bash
QUERY="repo:$GITHUB_REPO is:pr is:open feature in:branch"
```

### 4. Get Complete PR Feedback

To get complete PR feedback, you need to fetch **three types** of information:

#### A. PR Details

Get the PR metadata, stats, description, and other details.

```bash
PR_NUMBER=123

curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls/$PR_NUMBER"
```

#### B. General PR Comments (Issue Comments)

These are comments on the PR as a whole, not tied to specific code lines.

```bash
PR_NUMBER=123

curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/issues/$PR_NUMBER/comments"
```

**Important**: Uses `/issues/` endpoint, not `/pulls/`

#### C. Code Review Comments (Line-Specific)

These are comments on specific lines of code in the PR diff.

```bash
PR_NUMBER=123

curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls/$PR_NUMBER/comments"
```

## Complete Example: Fetch All Three Types of PR Feedback

```bash
PR_NUMBER=123

echo "=== PR Details ==="
curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls/$PR_NUMBER" \
  | python3 -m json.tool

echo ""
echo "=== General Comments ==="
curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/issues/$PR_NUMBER/comments" \
  | python3 -m json.tool

echo ""
echo "=== Review Comments ==="
curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/pulls/$PR_NUMBER/comments" \
  | python3 -m json.tool
```

## Troubleshooting

### 401 Bad Credentials Error

**Problem**: Getting `{"message": "Bad credentials", "status": "401"}`

**Solutions**:
1. ✅ Ensure using `Bearer` format: `Authorization: Bearer $GITHUB_TOKEN`
2. ❌ NOT `token` format: `Authorization: token $GITHUB_TOKEN`
3. Verify token is set: `echo ${GITHUB_TOKEN:0:10}`
4. Check token hasn't expired
5. Verify token has required permissions (at minimum: `repo` scope for private repos, `public_repo` for public)

### Empty Response or No Results

**Problem**: Getting `[]` empty array or no search results

**Possible causes**:
- No comments exist on that PR yet
- Using wrong endpoint (e.g., `/pulls/` instead of `/issues/` for general comments)
- PR number doesn't exist
- Search term doesn't match any PRs in the fetched results
- For client-side search: Result is beyond the first 100 PRs (use GitHub Search API instead)

### Pipeline Failures

**Problem**: Script exits unexpectedly or doesn't catch errors in pipelines

**Solution**: Ensure script uses `set -e -o pipefail` at the beginning. The `-o pipefail` flag ensures that errors in any part of a pipeline cause the script to exit, not just the last command.

## Security Best Practices

### Command Injection Prevention

When passing user input to Python scripts, always use command-line arguments instead of string interpolation:

❌ **Insecure** (vulnerable to injection):
```bash
python3 -c "search = '$search_term'; ..."
```

✅ **Secure** (safe from injection):
```bash
python3 -c "import sys; search = sys.argv[1]; ..." "$search_term"
```

### Token Security

- Never commit tokens to version control
- Store tokens in environment variables only
- Use fine-grained personal access tokens when possible
- Limit token permissions to minimum required scopes
- Rotate tokens regularly

## Useful Python Snippets

### Pretty Print Comment Summary

```python
import json, sys

comments = json.load(sys.stdin)
for c in comments:
    user = c['user']['login']
    created = c['created_at']
    body = c['body'][:200]  # First 200 chars
    print(f"@{user} ({created}):")
    print(f"  {body}...")
    print()
```

### Extract Code Review Suggestions

```python
import json, sys

comments = json.load(sys.stdin)
for c in comments:
    path = c.get('path', 'N/A')
    line = c.get('original_line', 'N/A')
    body = c['body']
    print(f"{path}:{line}")
    print(f"  {body}")
    print()
```

### Search Results with Formatting

```python
import json, sys

result = json.load(sys.stdin)
items = result.get('items', [])
total_count = result.get('total_count', 0)

print(f"Found {total_count} result(s)\n")

for pr in items:
    print(f"PR #{pr['number']}: {pr['title']}")
    print(f"  State: {pr['state']}")
    print(f"  URL: {pr['html_url']}")
    print()
```

## API Rate Limits

GitHub API has rate limits:
- **Authenticated requests**: 5,000 requests per hour
- **Unauthenticated requests**: 60 requests per hour

Check your current rate limit status:
```bash
curl -s -L \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "$GITHUB_API_BASE/rate_limit"
```

## References

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Pull Request Comments API](https://docs.github.com/en/rest/pulls/comments)
- [Issue Comments API](https://docs.github.com/en/rest/issues/comments)
- [Search API](https://docs.github.com/en/rest/search)
- [Search Syntax](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
- [Authentication Guide](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)

## Adding Labels to Pull Requests

### Using the Helper Script

```bash
# Add label to specific PR
./scripts/add-pr-label.sh 73 claude

# Add label to PR for current branch
./scripts/add-pr-label.sh current claude

# Add label with custom color (default is 0E8A16 - green) and description
./scripts/add-pr-label.sh 73 claude 0E8A16 "Created by Claude AI"
```

### Required Token Permissions

To add labels to PRs, your `GITHUB_TOKEN` needs **write access to Issues**:

**For Personal Access Tokens (classic)**:
- ✅ `repo` scope (for private repositories)
- ✅ `public_repo` scope (for public repositories only)

**For Fine-Grained Personal Access Tokens**:
- ✅ Repository permissions → Issues → **Read and write**

### Direct API Call

```bash
PR_NUMBER=73
LABEL_NAME="claude"

# Safely create JSON payload using Python to prevent injection
PAYLOAD=$(python3 -c 'import json, sys; print(json.dumps({"labels": [sys.argv[1]]}))' "$LABEL_NAME")

# Add label to PR
curl -s -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  "$GITHUB_API_BASE/repos/$GITHUB_REPO/issues/$PR_NUMBER/labels" \
  -d "$PAYLOAD"
```

**Security Note**: Always use `json.dumps()` to create JSON payloads. Never embed variables directly in JSON strings as this can lead to injection vulnerabilities.

## Quick Reference for AI Assistants

When asked to fetch PR feedback:

1. **Read this file first**: `GITHUB_API_GUIDE.md`
2. **Use the helper script**: `./fetch-pr-comments.sh <PR_NUMBER>` or `./fetch-pr-comments.sh current`
   - The script automatically fetches **all three types** of feedback
3. **Three types of feedback** (all required):
   - PR Details: `/repos/$GITHUB_REPO/pulls/$PR_NUMBER`
   - General Comments: `/repos/$GITHUB_REPO/issues/$PR_NUMBER/comments`
   - Review Comments: `/repos/$GITHUB_REPO/pulls/$PR_NUMBER/comments`
4. **Use Bearer token**: Always use `Authorization: Bearer $GITHUB_TOKEN`
5. **For searches**: Use `api-search` command for comprehensive results
6. **Parse with Python**: Use `python3 -m json.tool` or custom Python for formatting
7. **Security**: Pass user input as command-line arguments, not string interpolation

When asked to add labels to PRs:

1. **Use the helper script**: `scripts/add-pr-label.sh <PR_NUMBER> <LABEL_NAME>`
2. **For current branch**: `scripts/add-pr-label.sh current claude`
3. **Note**: Requires token with Issues write permission
