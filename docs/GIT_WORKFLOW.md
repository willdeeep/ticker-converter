# Git Workflow and GitHub Integration Guide

## Overview

This document outlines the complete Git workflow for the ticker-converter project, following the Feature Branch Workflow pattern with GitHub CLI integration for issue management and pull requests.

## Workflow Overview

```
Issue Creation → Feature Branch → Development → Quality Checks → Pull Request → Code Review → Merge → Tag Release
```

## GitHub Issue Management

### Query Existing Issues

```bash
# List all open issues
gh issue list

# List all issues (open and closed)
gh issue list --state all

# Search issues by label
gh issue list --label enhancement

# Search issues by assignee
gh issue list --assignee @me

# Filter by milestone
gh issue list --milestone "v1.0"

# View specific issue details
gh issue view 12

# View issue in browser
gh issue view 12 --web
```

### Create New Issues

```bash
# Create issue interactively
gh issue create

# Create issue with title and body
gh issue create --title "Add currency conversion endpoint" --body "Implement USD to GBP conversion functionality for stock prices"

# Create issue with labels
gh issue create --title "Fix API authentication" --body "Resolve 401 errors in production" --label bug,high-priority

# Create issue from template
gh issue create --title "Database optimization" --body-file .github/ISSUE_TEMPLATE/feature_request.md

# Assign issue to user
gh issue create --title "Performance testing" --assignee username

# Add to milestone
gh issue create --title "Documentation update" --milestone "v1.1"
```

### Update Existing Issues

```bash
# Edit issue title and body
gh issue edit 12 --title "Updated: Currency conversion with caching" --body "Enhanced currency conversion with Redis caching support"

# Add labels to existing issue
gh issue edit 12 --add-label performance,caching

# Remove labels from issue
gh issue edit 12 --remove-label bug

# Assign issue
gh issue edit 12 --add-assignee username

# Change milestone
gh issue edit 12 --milestone "v1.2"

# Close issue
gh issue close 12

# Close with comment
gh issue close 12 --comment "Fixed in PR #25"

# Reopen issue
gh issue reopen 12
```

## Project Labels

### Current Labels

```bash
# Query all existing labels
gh label list

# Current project labels:
bonus              # Optional enhancement features
bug                # Bug reports and fixes
documentation      # Documentation improvements
duplicate          # Duplicate issues
enhancement        # New features and improvements
good first issue   # Beginner-friendly issues
help wanted        # Community contribution welcome
infrastructure     # Infrastructure and tooling changes
invalid            # Invalid issues
question           # Questions and discussions
requirement-1      # API Integration requirements
requirement-2      # Data processing requirements
requirement-3      # Database requirements
requirement-4      # Orchestration requirements
requirement-5      # API endpoints requirements
testing            # Testing-related issues
wontfix            # Issues that won't be addressed
```

### Create Additional Labels

```bash
# Create priority labels
gh label create high-priority --description "High priority issues" --color "d73a4a"
gh label create medium-priority --description "Medium priority issues" --color "fbca04"
gh label create low-priority --description "Low priority issues" --color "0e8a16"

# Create type labels
gh label create feature --description "New feature implementation" --color "1d76db"
gh label create refactor --description "Code refactoring" --color "5319e7"
gh label create performance --description "Performance improvements" --color "006b75"
gh label create security --description "Security-related issues" --color "b60205"

# Create component labels
gh label create api --description "API-related changes" --color "0052cc"
gh label create database --description "Database-related changes" --color "5319e7"
gh label create frontend --description "Frontend-related changes" --color "1d76db"
gh label create etl --description "ETL pipeline changes" --color "0e8a16"

# Create status labels
gh label create blocked --description "Blocked by dependencies" --color "d93f0b"
gh label create in-progress --description "Currently being worked on" --color "fbca04"
gh label create needs-review --description "Needs code review" --color "0052cc"
```

## Feature Branch Workflow

### 1. Start New Feature

```bash
# Sync with main branch
git checkout main
git pull origin main

# Create feature branch from issue
gh issue develop 12 --checkout

# Or create branch manually
git checkout -b feature/currency-conversion-issue-12

# Verify current branch
git branch --show-current
```

### 2. Development Workflow

```bash
# Make changes and stage them
git add src/ticker_converter/api/endpoints.py
git add tests/test_currency_conversion.py

# Commit with conventional message
git commit -m "feat: implement USD to GBP currency conversion endpoint

- Add currency conversion logic to API
- Implement exchange rate caching
- Add comprehensive test coverage
- Update API documentation

Closes #12"

# Push feature branch
git push -u origin feature/currency-conversion-issue-12
```

### 3. Quality Checks

```bash
# Run all quality checks
make quality

# Individual quality tools
make lint        # Ruff linting
make format      # Black formatting
make typecheck   # MyPy type checking
make test        # Pytest test suite

# Fix any issues before proceeding
make format-fix  # Auto-fix formatting issues
```

### 4. Pull Request Creation

```bash
# Create PR from current branch
gh pr create --title "feat: Add USD to GBP currency conversion endpoint" --body "
## Overview
Implements currency conversion functionality for stock price analysis.

## Changes
- [x] Currency conversion API endpoint
- [x] Exchange rate caching with Redis
- [x] Comprehensive test coverage
- [x] API documentation updates
- [x] Performance optimization

## Testing
- Unit tests: 98% coverage
- Integration tests: All passing
- Manual testing: API endpoints verified

## Related Issues
Closes #12

## Checklist
- [x] Code follows project style guidelines
- [x] Tests added and passing
- [x] Documentation updated
- [x] No breaking changes
- [x] Performance impact assessed
"

# Create draft PR
gh pr create --draft --title "WIP: Currency conversion feature"

# Add reviewers
gh pr create --reviewer username1,username2

# Add labels
gh pr create --label enhancement,api

# Assign to milestone
gh pr create --milestone "v1.1"
```

### 5. Code Review Process

```bash
# Check PR status
gh pr status

# View PR details
gh pr view

# Request review
gh pr edit --add-reviewer username

# View PR in browser
gh pr view --web

# Respond to review comments
git add .
git commit -m "fix: address review comments for validation logic"
git push
```

### 6. Merge and Cleanup

```bash
# Merge PR (after approval)
gh pr merge --squash --delete-branch

# Or merge with different strategies
gh pr merge --merge    # Standard merge
gh pr merge --rebase   # Rebase and merge

# Sync local repository
git checkout main
git pull origin main

# Clean up local feature branch
git branch -d feature/currency-conversion-issue-12

# Tag release if needed
git tag -a v1.1.0 -m "Release v1.1.0: Currency conversion feature"
git push origin v1.1.0
```

## Commit Message Standards

### Conventional Commits Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

```bash
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation changes
style:    # Code style changes (formatting, etc.)
refactor: # Code refactoring
test:     # Adding or updating tests
chore:    # Maintenance tasks
perf:     # Performance improvements
ci:       # CI/CD changes
build:    # Build system changes
```

### Commit Examples

```bash
# Feature addition
git commit -m "feat(api): add currency conversion endpoint

Implement USD to GBP conversion for stock prices with caching support.
Includes comprehensive test coverage and performance optimization.

Closes #12"

# Bug fix
git commit -m "fix(database): resolve connection pool timeout

Fix PostgreSQL connection pool exhaustion during high load.
Increase pool size and implement proper connection cleanup.

Fixes #23"

# Documentation
git commit -m "docs: update API endpoint documentation

Add examples for currency conversion endpoints and error handling.
Update deployment guide with PostgreSQL configuration."

# Refactoring
git commit -m "refactor(etl): simplify data transformation pipeline

Remove complex feature engineering classes and replace with SQL-based approach.
Reduces code complexity by 60% while maintaining functionality.

Related to #12"

# Performance improvement
git commit -m "perf(queries): optimize stock performance query

Add database indexes and rewrite query to use window functions.
Reduces query execution time from 500ms to 50ms.

Improves #25"
```

## Issue Templates

### Feature Request Template

```markdown
## Feature Description
Brief description of the feature and its purpose.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
Detailed description of the proposed implementation.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Requirements
- Database changes needed
- API modifications required
- Performance considerations

## Testing Requirements
- Unit tests required
- Integration tests needed
- Manual testing steps

## Documentation Updates
- [ ] API documentation
- [ ] User documentation
- [ ] Technical documentation

## Dependencies
List any dependencies on other issues or external factors.

## Estimated Effort
- Small (< 1 day)
- Medium (1-3 days)  
- Large (3-5 days)
- Extra Large (> 5 days)

## Labels
enhancement, api, database, documentation
```

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug.

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens?

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- Browser: [if applicable]
- API Version: [e.g., v1.0]

## Error Messages
```
Paste any error messages or logs here
```

## Screenshots
If applicable, add screenshots to help explain the problem.

## Additional Context
Any other context about the problem.

## Possible Solution
If you have ideas on how to fix the issue.

## Impact
- Critical (system down)
- High (major feature broken)
- Medium (minor feature affected)
- Low (cosmetic issue)

## Labels
bug, high-priority, api
```

## Pull Request Template

```markdown
## Overview
Brief description of changes and motivation.

## Changes Made
- [x] Feature 1 implementation
- [x] Bug fix for issue X
- [x] Documentation updates
- [x] Test coverage improvements

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests passing

### Test Coverage
- Unit tests: X% coverage
- Integration tests: All scenarios covered
- Performance tests: Benchmarks within acceptable range

## Code Quality
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Linting passes (make lint)
- [ ] Type checking passes (make typecheck)
- [ ] Documentation updated

## Database Changes
- [ ] Schema migrations included
- [ ] Data migration scripts provided
- [ ] Backward compatibility maintained

## API Changes
- [ ] API documentation updated
- [ ] Breaking changes documented
- [ ] Version compatibility noted

## Performance Impact
- [ ] Performance impact assessed
- [ ] Benchmarks provided (if applicable)
- [ ] No significant performance degradation

## Security Considerations
- [ ] Security review completed
- [ ] No sensitive data exposed
- [ ] Input validation implemented

## Related Issues
Closes #X
Relates to #Y
Blocks #Z

## Deployment Notes
Any special deployment considerations or steps.

## Screenshots
If applicable, add screenshots showing the changes.

## Checklist
- [ ] I have read the contributing guidelines
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## Version Tagging

### Semantic Versioning

```bash
# Format: MAJOR.MINOR.PATCH
# MAJOR: Breaking changes
# MINOR: New features (backward compatible)
# PATCH: Bug fixes (backward compatible)

# Create release tag
git tag -a v1.2.3 -m "Release v1.2.3: Currency conversion and performance improvements

Features:
- Currency conversion API endpoints
- Performance optimization for database queries
- Enhanced error handling

Bug Fixes:
- Fixed connection pool timeout issue
- Resolved API authentication errors

Breaking Changes:
- None

Migration Notes:
- Update environment variables for currency API"

# Push tag to remote
git push origin v1.2.3

# Create GitHub release from tag
gh release create v1.2.3 --title "v1.2.3: Currency Conversion Release" --notes "
## Features
- Currency conversion API endpoints
- Performance optimization for database queries

## Bug Fixes  
- Fixed connection pool timeout issue
- Resolved API authentication errors

## Installation
\`\`\`bash
pip install ticker-converter==1.2.3
\`\`\`

## Migration Guide
Update your environment variables to include:
\`\`\`
CURRENCY_API_KEY=your_key_here
\`\`\`
"

# List all tags
git tag -l

# Delete tag (if needed)
git tag -d v1.2.3
git push origin --delete v1.2.3
```

### Pre-release Tags

```bash
# Alpha release
git tag -a v1.3.0-alpha.1 -m "Alpha release for testing"

# Beta release  
git tag -a v1.3.0-beta.1 -m "Beta release candidate"

# Release candidate
git tag -a v1.3.0-rc.1 -m "Release candidate 1"

# Create pre-release on GitHub
gh release create v1.3.0-alpha.1 --prerelease --title "v1.3.0-alpha.1" --notes "Alpha release for testing new features"
```

## Advanced GitHub CLI Usage

### Issue Management Automation

```bash
# Bulk label operations
gh issue list --json number,title | jq -r '.[] | select(.title | contains("API")) | .number' | xargs -I {} gh issue edit {} --add-label api

# Close multiple issues
gh issue list --label duplicate --json number | jq -r '.[].number' | xargs -I {} gh issue close {}

# Create issues from template file
gh issue create --title "Database migration" --body-file templates/migration_issue.md
```

### Repository Insights

```bash
# View repository statistics
gh api repos/:owner/:repo --jq '{name, stars: .stargazers_count, forks: .forks_count, issues: .open_issues_count}'

# List recent releases
gh release list --limit 5

# View contributor statistics
gh api repos/:owner/:repo/contributors --jq '.[] | {login, contributions}'
```

This comprehensive Git workflow ensures consistent development practices, proper issue tracking, and maintainable code quality throughout the project lifecycle.
