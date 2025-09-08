# GitHub Workflow Instructions

These instructions guide GitHub Copilot in managing GitHub-specific workflows, issue creation, and CI/CD processes for this repository.

## Makefile Modernization Project (Issue #62) - ✅ COMPLETED

### Cross-Platform Development Support - ✅ PRODUCTION READY

The modular Makefile system is fully implemented with comprehensive cross-platform compatibility:

1. ✅ **Platform Detection**: Automatic OS detection with conditional logic for macOS/Linux/Windows
2. ✅ **Tool Availability**: Graceful degradation when optional tools are missing
3. ✅ **Path Handling**: Cross-platform path separators and file operations
4. ✅ **Package Managers**: Multi-platform support (Homebrew, APT, Chocolatey)

### Modular Makefile Structure - ✅ FULLY IMPLEMENTED

The project has successfully implemented a modular Makefile structure with **3,308 lines** of cross-platform build automation and **complete main Makefile integration**:

```
make/
├── Makefile.platform     # OS detection and platform configurations (288 lines)
├── Makefile.env          # Environment setup and validation (280 lines)
├── Makefile.install      # Installation and dependency management (372 lines)
├── Makefile.database     # PostgreSQL and database operations (383 lines)
├── Makefile.airflow      # Airflow orchestration and management (331 lines)
├── Makefile.testing      # Test execution and coverage (413 lines)
├── Makefile.quality      # Code quality, linting, and validation (446 lines)
├── Makefile.cleanup      # Cleaning and teardown operations (398 lines)
└── help.sh               # Enhanced help system (397 lines)
```

**Completed Features:**
- ✅ Cross-platform support (macOS, Linux, Windows)
- ✅ Comprehensive environment management
- ✅ Database lifecycle automation
- ✅ Airflow orchestration integration
- ✅ Complete testing and coverage pipeline
- ✅ Code quality and security validation
- ✅ Intelligent cleanup operations
- ✅ Enhanced help and documentation system
- ✅ Main Makefile integration with backward compatibility
- ✅ Comprehensive validation and migration system

### Implementation Status - ✅ PRODUCTION COMPLETE

The Makefile modernization project is fully complete and production-ready:

1. ✅ **Backward Compatibility**: All existing commands work seamlessly
2. ✅ **Testing Strategy**: Validated on macOS arm64, ready for Linux/Windows testing
3. ✅ **Documentation**: Complete platform-specific setup instructions
4. ✅ **Performance**: Zero performance regression, improved maintainability
5. ✅ **Migration**: Comprehensive validation system ensures smooth transition

## Airflow 3.x CLI Command Reference

**CRITICAL**: This project uses **Apache Airflow 3.0.6**. The CLI syntax has changed significantly from Airflow 2.x.

### Environment Setup Requirements

**ALWAYS** run these exports before any Airflow CLI command:
```bash
source .venv/bin/activate
source .env
export AIRFLOW_HOME=/Users/willhuntleyclarke/repos/interests/ticker-converter/airflow
export AIRFLOW__CORE__DAGS_FOLDER=/Users/willhuntleyclarke/repos/interests/ticker-converter/dags
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////Users/willhuntleyclarke/repos/interests/ticker-converter/airflow/airflow.db
export PYTHONPATH=/Users/willhuntleyclarke/repos/interests/ticker-converter:/Users/willhuntleyclarke/repos/interests/ticker-converter/dags:/Users/willhuntleyclarke/repos/interests/ticker-converter/src
```

### Airflow 3.x CLI Commands (DO NOT USE --output json)

**✅ CORRECT Airflow 3.x Commands:**
```bash
# List DAGs
airflow dags list

# Check DAG import errors
airflow dags list-import-errors

# Trigger DAG
airflow dags trigger <dag_id>

# Get DAG state (NO --output json flag!)
airflow dags state <dag_id>

# List DAG runs
airflow dags list-runs <dag_id>

# Get task states for DAG run
airflow tasks states-for-dag-run <dag_id> <run_id>

# Clear/stop running or failed tasks
airflow tasks clear <dag_id> -r -y  # Clear only running tasks
airflow tasks clear <dag_id> -f -y  # Clear only failed tasks
airflow tasks clear <dag_id> -t <task_regex> -y  # Clear specific tasks by regex

# Test task execution
airflow tasks test <dag_id> <task_id> <execution_date>

# Pause/Unpause DAGs
airflow dags pause <dag_id>
airflow dags unpause <dag_id>

# List connections
airflow connections list

# Add connection
airflow connections add <conn_id> --conn-uri <uri>

# Test connection (may be disabled)
airflow connections test <conn_id>

# Check health
curl http://localhost:8080/api/v2/monitor/health
```

**❌ INCORRECT Airflow 2.x Commands (DO NOT USE):**
```bash
# These will fail in Airflow 3.x:
airflow dags state <dag_id> --output json     # --output flag removed
airflow dags list --output json               # --output flag removed
airflow connections list --output json        # --output flag removed
```

### Common Troubleshooting

**Problem**: CLI commands fail but web UI works
**Solution**: Ensure all environment variables are exported (see Environment Setup above)

**Problem**: "unrecognized arguments: --output"
**Solution**: Remove `--output json` flags - not supported in Airflow 3.x

**Problem**: DAGs not visible in CLI
**Solution**: Check AIRFLOW__CORE__DAGS_FOLDER and PYTHONPATH exports

### Health Check Endpoints

**Airflow 3.x Health Check:**
```bash
# NEW endpoint in Airflow 3.x
curl http://localhost:8080/api/v2/monitor/health
```

**❌ Old endpoint (will redirect):**
```bash
curl http://localhost:8080/health  # Returns redirect message
```

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
