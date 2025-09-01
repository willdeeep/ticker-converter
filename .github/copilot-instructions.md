# GitHub Workflow Instructions

These instructions guide GitHub Copilot in managing GitHub-specific workflows, issue creation, and CI/CD processes for this repository.

## Makefile Modernization Project (Issue #62)

### Cross-Platform Development Support

When working with Makefile-related tasks, consider cross-platform compatibility:

1. **Platform Detection**: Use conditional logic for OS-specific commands
2. **Tool Availability**: Implement graceful degradation when tools are missing
3. **Path Handling**: Account for different path separators and conventions
4. **Package Managers**: Support multiple package managers (brew, apt, choco)

### Modular Makefile Structure

The project is transitioning to a modular Makefile structure:

```
make/
├── Makefile.platform     # OS detection and platform configurations
├── Makefile.env          # Environment setup and validation
├── Makefile.install      # Installation and dependency management
├── Makefile.database     # PostgreSQL and database operations
├── Makefile.airflow      # Airflow orchestration and management
├── Makefile.testing      # Test execution and coverage
├── Makefile.quality      # Code quality, linting, and validation
├── Makefile.cleanup      # Cleaning and teardown operations
└── help.sh               # Enhanced help system
```

### Implementation Guidelines

When implementing Makefile modernization features:

1. **Backward Compatibility**: Ensure all existing commands continue to work
2. **Testing Strategy**: Test across macOS, Linux, and Windows environments
3. **Documentation**: Update platform-specific setup instructions
4. **Performance**: Monitor for any performance impact from modularization

## Issue Management

### Issue Creation Protocol

When creating GitHub issues from project roadmap phases:

1. **Review Existing Labels**: Use `gh issue list` to understand current labeling system
2. **Create Descriptive Issues**: Each deliverable becomes one issue
3. **Include Phase Context**: Reference current phase milestones and completion status
4. **Use Consistent Labels**: Apply appropriate labels for tracking and organization

### Long Documentation Submission Protocol

For any long documentation, comments, or content containing code snippets submitted via Git or GitHub CLI commands, ALWAYS use EOF (heredoc) syntax instead of quoted strings to prevent quote escaping issues:

**✅ CORRECT - Use EOF syntax with GitHub CLI:**
```bash
cat <<EOF | gh issue comment 123 --body-file -
## Progress Update

### Code Examples
\`\`\`python
def example():
    return "This won't break the command"
\`\`\`

**Bold text**, _italic text_, and other markdown formatting work safely.
EOF
```

**✅ CORRECT - Alternative GitHub CLI EOF syntax:**
```bash
gh issue create --title "Feature Request" --body-file - <<EOF
## Description
This is a multi-line description with code:

\`\`\`bash
make test
\`\`\`

And it handles quotes "safely" without escaping issues.
EOF
```

**❌ INCORRECT - Avoid quoted strings for long content:**
```bash
gh issue comment 123 --body "This will break with quotes and code snippets"
```

**Benefits of EOF syntax:**
- Prevents quote escaping issues with code snippets
- Preserves markdown formatting (bold, italic, code blocks)
- Handles multi-line content safely
- Avoids shell interpretation of special characters
- More readable for complex documentation

### Issue Template Structure

```markdown
## Deliverable: [Brief Description]

### Context
- **Project**: [Project Name from roadmap]
- **Phase**: [Current Phase Number and Name]
- **Related Issues**: [Links to dependent issues]

### Acceptance Criteria
- [ ] [Specific, testable criteria]
- [ ] [Implementation requirements]
- [ ] [Quality gates passed]

### Implementation Notes
- **Files to modify**: [List expected files]
- **Tests required**: [Test coverage expectations]
- **Documentation updates**: [Required doc changes]

### Phase Milestones Status
- [ ] [Phase milestone 1]
- [ ] [Phase milestone 2]
- [ ] [Current deliverable milestone]

### Definition of Done
- [ ] All tests pass
- [ ] Code coverage maintained above 50%
- [ ] Pylint score maintained at 10.00/10
- [ ] MyPy validation clean
- [ ] GitHub Actions CI/CD passes
- [ ] Pull request merged to dev
```

## Branch Management

### Feature Branch Creation

```bash
# Always start from updated dev branch
git checkout dev
git pull origin dev

# Create feature branch with consistent naming
git checkout -b feature/issue-[number]-[brief-description]

# Set upstream and push
git push -u origin feature/issue-[number]-[brief-description]
```

### Branch Naming Convention

- **Format**: `feature/issue-[number]-[brief-description]`
- **Examples**: 
  - `feature/issue-42-add-currency-validation`
  - `feature/issue-73-refactor-database-manager`
  - `feature/issue-15-implement-error-handling`

### Git Commit Message Protocol

For multi-line commit messages with detailed descriptions, use EOF syntax to avoid quote escaping issues:

**✅ CORRECT - Use EOF for detailed commits:**
```bash
git commit -m <<EOF
feat: implement comprehensive error handling system

- Added custom exception hierarchy in src/ticker_converter/exceptions.py
- Replaced generic Exception catches with specific types:
  * DataIngestionException for pipeline errors
  * APIConnectionException for external API failures
  * DatabaseOperationException for SQL operation failures
- Maintained Pylint 10.00/10 score throughout implementation
- All 241 tests passing with enhanced error handling

Resolves: #58 (Phase 2 - Enhanced Error Handling)
EOF
```

**❌ INCORRECT - Avoid quoted strings for detailed commits:**
```bash
git commit -m "Complex message with code examples that break quotes"
```

## Pull Request Workflow

### PR Creation Requirements

1. **All tests passing**: 100% test success rate
2. **Quality gates met**: Pylint 10.00/10, MyPy clean, Black formatted
3. **CI/CD validated**: GitHub Actions passing via `act` CLI
4. **Documentation updated**: Relevant docs reflect changes
5. **Issue linked**: PR description references GitHub issue

### PR Template

```markdown
## Changes

Brief description of changes made.

## Related Issue

Closes #[issue-number]

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Test coverage maintained above 50%

## Quality Checklist

- [ ] Code follows PEP 8 standards
- [ ] Black formatting applied
- [ ] Pylint score 10.00/10
- [ ] MyPy validation clean
- [ ] No security vulnerabilities introduced

## Documentation

- [ ] README files updated if needed
- [ ] API documentation updated
- [ ] Architecture docs reflect changes
```

## CI/CD Integration

### GitHub Actions Validation

Before creating pull requests, validate locally:

```bash
# Ensure Docker is running for act CLI
docker info

# Run full CI/CD pipeline locally
act

# Run specific workflow jobs
act --job pytest
act --job lint-check
act --job security-scan
```

### Required Workflows

1. **Test Suite**: All tests must pass
2. **Linting**: Black, Pylint, MyPy validation
3. **Security**: Security vulnerability scanning
4. **Coverage**: Test coverage reporting
5. **Documentation**: Doc generation and validation

## Label Management

### Standard Labels

- **`type: feature`**: New functionality
- **`type: bug`**: Bug fixes
- **`type: refactor`**: Code refactoring
- **`type: docs`**: Documentation updates
- **`priority: high`**: Critical issues
- **`priority: medium`**: Standard priority
- **`priority: low`**: Nice-to-have improvements
- **`status: in-progress`**: Currently being worked on
- **`status: review`**: Ready for review
- **`phase: [number]`**: Phase tracking labels

### Phase-Specific Labels

Create labels for each project phase:
- **`phase-1: foundation`**
- **`phase-2: core-features`**
- **`phase-3: integration`**
- **`phase-4: optimization`**
- **`phase-5: deployment`**

## Automation Scripts

### Issue Creation from Roadmap

```bash
#!/bin/bash
# Script to create issues from roadmap phase

PHASE_NUMBER=$1
PROJECT_NAME=$2

# Extract deliverables from roadmap file
ROADMAP_FILE="my_docs/TEMP_${PROJECT_NAME}_ROADMAP.md"

# Create issues for each deliverable in phase
# (Implementation would parse markdown and create issues)
```

### Phase Completion Validation

```bash
#!/bin/bash
# Validate all phase milestones completed

PHASE_NUMBER=$1

# Check all issues in phase are closed
# Validate all tests still pass
# Confirm documentation updated
```

## Integration with Project Workflow

### Phase Activation Process

1. **Parse Roadmap**: Extract deliverables from current phase
2. **Create Issues**: One issue per deliverable with proper labels
3. **Set Milestones**: Create GitHub milestone for phase tracking
4. **Initialize Board**: Update project board with new issues

### Development Cycle Integration

Each development cycle follows the 12-step process:

1. **Branch Creation**: Feature branch from dev
2. **Test Preparation**: Write/update tests first
3. **Implementation**: Complete the work
4. **Quality Assurance**: Full quality pipeline
5. **PR Creation**: Submit for review
6. **Issue Closure**: Close upon merge

### Milestone Tracking

- **Phase Milestones**: Track phase completion criteria
- **Issue Milestones**: Group related issues
- **Release Milestones**: Major version releases

## Security Considerations

### Sensitive Information

- **No secrets in issues**: Use environment variables references
- **No credentials in PRs**: Sanitize all commit history
- **Access control**: Proper RBAC for repository access

### Review Requirements

- **Security review**: For changes affecting data handling
- **Architecture review**: For significant structural changes
- **Performance review**: For changes affecting pipeline efficiency

## Monitoring and Metrics

### Success Metrics

- **Issue cycle time**: Time from creation to closure
- **PR merge rate**: Percentage of PRs merged without revision
- **Quality score**: Pylint/MyPy compliance rate
- **Test coverage**: Maintained above 50%
- **CI/CD success rate**: Percentage of successful pipeline runs

### Quality Gates

All PRs must pass:
- **100% test success rate**
- **Pylint score 10.00/10**
- **MyPy validation clean**
- **Black formatting compliance**
- **Security scan clean**
- **Documentation updated**

## Emergency Procedures

### Hotfix Process

1. **Create hotfix branch** from main
2. **Minimal changes** to fix critical issue
3. **Expedited review** process
4. **Merge to main and dev**
5. **Tag release** immediately

### Rollback Process

1. **Identify problematic commit**
2. **Create revert PR**
3. **Validate in staging**
4. **Deploy revert**
5. **Create follow-up issue** for proper fix
