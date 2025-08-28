# GitHub Copilot Workflow Template

This document provides a comprehensive template for using GitHub Copilot to manage structured project development, from initial scoping through to completion.

## Overview

The GitHub Copilot Workflow Template establishes a systematic approach to project management that transforms user requests into structured roadmaps, measurable phases, GitHub issues, and automated development cycles.

## Table of Contents

1. [Workflow Components](#workflow-components)
2. [Project Lifecycle](#project-lifecycle)
3. [Implementation Process](#implementation-process)
4. [Quality Assurance](#quality-assurance)
5. [Automation Scripts](#automation-scripts)
6. [Success Metrics](#success-metrics)
7. [Troubleshooting](#troubleshooting)

## Workflow Components

### Repository Instructions Structure

The workflow uses a hierarchical instruction system following [GitHub's repository instructions guidelines](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions#enabling-prompt-files):

```
Repository Root/
├── .copilot-instructions.md          # Main repository development guidelines
├── .github/
│   ├── README.md                     # GitHub directory usage explanation
│   ├── copilot-instructions.md       # GitHub-specific workflow procedures
│   ├── ISSUE_TEMPLATE/               # GitHub issue templates
│   └── workflows/                    # GitHub Actions CI/CD workflows
├── src/.copilot-instructions.md      # Source code development guidelines
├── tests/.copilot-instructions.md    # Testing framework instructions
├── docs/.copilot-instructions.md     # Documentation standards
└── my_docs/guides/                   # Workflow implementation guides
```

### Instruction File Hierarchy

1. **Root `.copilot-instructions.md`**: General repository development guidelines
2. **`.github/copilot-instructions.md`**: GitHub-specific workflow procedures
3. **Directory-specific instructions**: Context-sensitive guidance for major directories
4. **Project guides**: Detailed implementation procedures in `my_docs/guides/`

## Project Lifecycle

### Phase 1: Project Scoping

When a user requests significant new work, GitHub Copilot will:

#### 1.1 Requirements Analysis
- **Parse user prompt** for project objectives and constraints
- **Review referenced materials** in `my_docs/` directory
- **Analyze uploaded guides** and external documentation links
- **Identify stakeholders** and success criteria

#### 1.2 Roadmap Creation
Create `my_docs/TEMP_[PROJECT_NAME]_ROADMAP.md` containing:

```markdown
# [Project Name] Development Roadmap

## Project Overview
**Objective**: [Clear statement of project goals]
**Timeline**: [Estimated duration]
**Success Criteria**: [Measurable outcomes]

## User Stories
- As a [user type], I want [functionality] so that [benefit]
- As a [user type], I want [functionality] so that [benefit]

## Project Phases

### Phase 1: Foundation (Weeks 1-2)
**Objective**: Establish project foundation and core infrastructure

**Deliverables**:
1. **Setup Development Environment**
   - Configure build tools and dependencies
   - Establish testing framework
   - Set up CI/CD pipeline
   - *Example*: `pip install -e .[dev]` and pytest configuration

2. **Define Data Models**
   - Create Pydantic models for core entities
   - Implement validation logic
   - Add comprehensive tests
   - *Reference*: `my_docs/guides/python_refactoring_guide.md`

**Phase Completion Milestones**:
- [ ] Development environment fully configured
- [ ] All tests passing with >69% coverage
- [ ] CI/CD pipeline operational
- [ ] Core data models validated

### Phase 2: Core Implementation (Weeks 3-5)
[Similar structure for subsequent phases]

## Dependencies and Constraints
- **External APIs**: [List required external services]
- **Database Requirements**: [Schema and performance needs]
- **Security Considerations**: [Authentication and authorization]
```

#### 1.3 Phase Structure Requirements
- **3-7 phases** per project (larger projects up to 7 phases)
- **Clear deliverables** sized for single commits
- **Measurable milestones** for phase completion
- **Dependencies** clearly identified between phases

### Phase 2: Phase Breakdown and Issue Creation

#### 2.1 Phase Activation
When user agrees to begin a phase:

1. **Review existing GitHub labels**:
   ```bash
   gh issue list --label "in-progress"
   gh label list
   ```

2. **Extract deliverables** from roadmap phase
3. **Create GitHub issues** for each deliverable
4. **Set appropriate labels** and milestones

#### 2.2 Issue Creation Template
```bash
gh issue create \
  --title "Implement currency validation logic" \
  --body "$(cat issue_template.md)" \
  --label "type:feature,phase-2,priority:medium"
```

Issue content structure:
```markdown
## Deliverable: Implement Currency Validation Logic

### Context
- **Project**: Currency Converter Enhancement
- **Phase**: Phase 2 - Core Implementation
- **Roadmap Reference**: `my_docs/TEMP_CURRENCY_CONVERTER_ROADMAP.md`

### Acceptance Criteria
- [ ] Validate currency codes against ISO 4217 standard
- [ ] Handle invalid currency codes with descriptive errors
- [ ] Implement caching for currency validation lookups
- [ ] Add comprehensive unit tests with >90% coverage

### Implementation Notes
- **Files to modify**: 
  - `src/ticker_converter/data_models/currency.py`
  - `tests/unit/data_models/test_currency.py`
- **Reference documentation**: `my_docs/guides/python_refactoring_guide.md`
- **External API**: ISO currency code service integration

### Phase 2 Milestones Status
- [ ] Currency validation implemented
- [ ] Exchange rate fetching optimized
- [x] Database schema updated
- [ ] API endpoints enhanced

### Definition of Done
- [ ] All tests pass (100% success rate)
- [ ] Pylint score maintained at 10.00/10
- [ ] MyPy validation clean
- [ ] Code coverage above 50%
- [ ] GitHub Actions CI/CD passes
- [ ] Pull request approved and merged
```

## Implementation Process

### Development Cycle (12-Step Process)

For each GitHub issue, follow this systematic development cycle:

#### Steps 1-3: Preparation and Implementation
1. **Create Feature Branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/issue-42-currency-validation
   git push -u origin feature/issue-42-currency-validation
   ```

2. **Prepare Tests**
   - Build or update tests before implementation
   - Follow test-driven development principles
   - Ensure tests align with acceptance criteria

3. **Implement Solution**
   - Complete work per GitHub issue requirements
   - Follow established coding standards
   - Include comprehensive error handling

#### Steps 4-6: Initial Quality Assurance
4. **Verify Functionality**
   ```bash
   pytest tests/unit/data_models/test_currency.py -v
   ```

5. **Initial Commit**
   ```bash
   git add .
   git commit -m "feat: implement currency validation logic

   - Add ISO 4217 currency code validation
   - Implement caching for validation lookups
   - Add comprehensive error handling
   - Include unit tests with >90% coverage

   Closes #42"
   ```

6. **Code Refactoring**
   - Apply guidelines from `my_docs/guides/python_refactoring_guide.md`
   - Extract common functionality
   - Improve code structure and readability

#### Steps 7-9: Code Quality Enhancement
7. **Refactoring Commit**
   ```bash
   git add .
   git commit -m "refactor: improve currency validation structure

   - Extract common validation logic to base class
   - Simplify error handling patterns
   - Improve function naming and documentation"
   ```

8. **Linting and Style**
   ```bash
   black src/
   # Fix any import ordering, whitespace issues
   ```

9. **Static Analysis**
   ```bash
   pylint src/ticker_converter/data_models/currency.py
   mypy src/ticker_converter/data_models/currency.py
   # Diagnose and fix all issues
   ```

#### Steps 10-12: Final Validation and Integration
10. **Quality Assurance**
    ```bash
    pytest --cov=src tests/
    # Ensure all tests pass and coverage maintained
    ```

11. **Quality Commit**
    ```bash
    git add .
    git commit -m "style: fix linting and type issues in currency module

    - Resolve all pylint warnings
    - Fix mypy type checking issues
    - Optimize import statements"
    ```

12. **CI/CD Validation and PR**
    ```bash
    # Validate with act CLI
    act --job pytest
    act --job lint-check

    # Create pull request
    gh pr create \
      --title "Implement currency validation logic" \
      --body "Implements currency validation as specified in issue #42"
    ```

## Quality Assurance

### Quality Gates

Every development cycle must pass these quality gates:

#### Testing Requirements
- **100% test pass rate** before any commit
- **Test coverage above 50%** (maintain current 54.27%)
- **Integration tests** for database and API operations
- **Unit tests** for all new functionality

#### Code Quality Standards
```bash
# Required tools and thresholds
black src/                    # Code formatting
pylint src/ --fail-under=10   # Must maintain 10.00/10 score
mypy src/ --strict           # Type checking with strict mode
pytest --cov=src --cov-fail-under=69  # Coverage threshold
```

#### Security Validation
- **No secrets in code** (use environment variables)
- **Parameterized queries** for all database operations
- **Input sanitization** for external data
- **Dependency vulnerability scanning**

### Commit Standards

#### Implementation Commits
```bash
git commit -m "feat: implement [feature description]

- [Specific functionality added]
- [Key implementation details]
- [Test coverage information]

Closes #[issue-number]"
```

#### Refactoring Commits
```bash
git commit -m "refactor: improve [component] structure and clarity

- [Structural improvements made]
- [Code organization changes]
- [Performance optimizations]"
```

#### Quality Commits
```bash
git commit -m "style: fix linting and type issues

- [Pylint warnings resolved]
- [MyPy type issues fixed]
- [Import optimization]"
```

## Automation Scripts

### GitHub CLI Integration

#### Issue Management
```bash
#!/bin/bash
# create_phase_issues.sh

PROJECT_NAME=$1
PHASE_NUMBER=$2
ROADMAP_FILE="my_docs/TEMP_${PROJECT_NAME}_ROADMAP.md"

# Extract deliverables from roadmap
grep -A 10 "Phase ${PHASE_NUMBER}" "$ROADMAP_FILE" | \
  grep "^[0-9]\." | \
  while IFS= read -r deliverable; do
    title=$(echo "$deliverable" | sed 's/^[0-9]*\. \*\*\(.*\)\*\*/\1/')

    gh issue create \
      --title "$title" \
      --label "phase-${PHASE_NUMBER},type:feature" \
      --body "Generated from $ROADMAP_FILE Phase $PHASE_NUMBER"
  done
```

#### Quality Validation
```bash
#!/bin/bash
# validate_quality.sh

echo "Running quality checks..."

# Code formatting
black --check src/ || exit 1

# Linting
pylint src/ --fail-under=10 || exit 1

# Type checking
mypy src/ || exit 1

# Test execution
pytest --cov=src --cov-fail-under=69 || exit 1

echo "All quality checks passed!"
```

### Local CI/CD Validation

#### Act CLI Integration
```bash
#!/bin/bash
# validate_ci.sh

# Ensure Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Run GitHub Actions locally
echo "Running CI/CD pipeline locally..."
act --job pytest
act --job lint-check
act --job security-scan

echo "CI/CD validation complete!"
```

## Success Metrics

### Project-Level Metrics

#### Completion Tracking
- **Phase milestone achievement**: All milestones completed per phase
- **Delivery timeline**: Phases completed within estimated timeframes
- **Scope adherence**: Features delivered match roadmap specifications
- **Quality maintenance**: No regression in code quality scores

#### Documentation Quality
- **Roadmap accuracy**: Deliverables match implementation
- **Documentation updates**: All docs reflect implemented changes
- **User guide completeness**: End-user documentation comprehensive
- **Architecture alignment**: Implementation matches design documents

### Code Quality Metrics

#### Testing Standards
- **Test pass rate**: 100% test success maintained
- **Coverage threshold**: Above 50% code coverage maintained
- **Test execution time**: Reasonable performance for development workflow
- **Integration test stability**: Reliable database and API testing

#### Static Analysis Results
- **Pylint scores**: Consistent 10.00/10 across all modules
- **MyPy validation**: Clean type checking with no errors
- **Security scanning**: Zero vulnerabilities in dependencies
- **Code formatting**: 100% Black compliance

### Process Efficiency

#### Development Velocity
- **Issue cycle time**: Time from creation to closure
- **Commit frequency**: Regular, meaningful commits per issue
- **PR merge rate**: High percentage of PRs merged without extensive revision
- **Rework percentage**: Minimal need for significant rework

#### Automation Effectiveness
- **CI/CD success rate**: High percentage of successful pipeline runs
- **Quality gate automation**: Automated enforcement of standards
- **Issue tracking accuracy**: GitHub issues reflect actual work completed
- **Documentation synchronization**: Automated doc updates where possible

## Troubleshooting

### Common Issues and Solutions

#### Development Environment Problems

**Issue**: Tests failing in CI but passing locally
```bash
# Solution: Validate environment consistency
python --version  # Check Python version matches CI
pip list          # Compare package versions
act --job pytest  # Run CI locally to reproduce
```

**Issue**: Pylint score dropping below 10.00/10
```bash
# Solution: Systematic quality improvement
pylint src/ --reports=y  # Get detailed report
pylint src/ --disable=all --enable=W  # Check warnings only
# Address issues incrementally by category
```

#### GitHub Integration Issues

**Issue**: GitHub CLI authentication problems
```bash
# Solution: Re-authenticate and verify permissions
gh auth logout
gh auth login --web
gh auth status
```

**Issue**: Issue creation automation failing
```bash
# Solution: Verify roadmap file format and GitHub permissions
# Check roadmap file exists and has correct format
ls -la my_docs/TEMP_*_ROADMAP.md
# Verify GitHub CLI can create issues
gh issue create --title "Test" --body "Test issue"
```

#### Quality Gate Failures

**Issue**: MyPy type checking failures
```bash
# Solution: Systematic type annotation improvement
mypy src/ --show-error-codes  # Get specific error codes
mypy src/ --ignore-missing-imports  # Temporary workaround
# Add type stubs for third-party packages
```

**Issue**: Test coverage dropping below threshold
```bash
# Solution: Identify and address uncovered code
pytest --cov=src --cov-report=html tests/
# Open htmlcov/index.html to see uncovered lines
# Add tests for uncovered functionality
```

### Escalation Procedures

#### Code Quality Issues
1. **Immediate**: Run local quality validation scripts
2. **Short-term**: Review and apply refactoring guidelines
3. **Medium-term**: Update quality standards documentation
4. **Long-term**: Enhance automated quality enforcement

#### Process Issues
1. **Document the problem** in GitHub issue
2. **Review workflow documentation** for guidance
3. **Update procedures** based on lessons learned
4. **Share improvements** with team through documentation updates

### Recovery Procedures

#### Failed Development Cycle
```bash
# 1. Assess current state
git status
git log --oneline -5

# 2. Backup current work
git stash push -m "Work in progress backup"

# 3. Reset to known good state
git checkout dev
git pull origin dev

# 4. Restart development cycle
git checkout -b feature/issue-X-retry
git stash pop  # If preserving work
```

#### Quality Gate Failures
```bash
# 1. Identify specific failures
pytest --tb=short  # Get test failure details
pylint src/ --output-format=parseable  # Get linting issues

# 2. Fix issues systematically
# Address test failures first
# Fix linting issues by category
# Resolve type checking problems

# 3. Validate fixes
./scripts/validate_quality.sh
```

## Integration with Existing Tools

### GitHub Actions Workflow

The workflow integrates with existing `.github/workflows/ci.yml`:

```yaml
name: Continuous Integration

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11.12'

    - name: Install dependencies
      run: |
        pip install -e .[dev]

    - name: Code formatting check
      run: black --check src/

    - name: Linting
      run: pylint src/ --fail-under=10

    - name: Type checking
      run: mypy src/

    - name: Run tests
      run: pytest --cov=src --cov-fail-under=69 tests/
```

### Makefile Integration

Enhance existing `Makefile` with workflow commands:

```makefile
# Quality assurance targets
.PHONY: quality
quality: format lint typecheck test

.PHONY: format
format:
	black src/

.PHONY: lint
lint:
	pylint src/ --fail-under=10

.PHONY: typecheck
typecheck:
	mypy src/

.PHONY: test
test:
	pytest --cov=src --cov-fail-under=69 tests/

# Workflow automation targets
.PHONY: validate-ci
validate-ci:
	act --job pytest
	act --job lint-check

.PHONY: create-phase-issues
create-phase-issues:
	./scripts/create_phase_issues.sh $(PROJECT) $(PHASE)
```

This comprehensive workflow template provides GitHub Copilot with all necessary procedures to systematically manage project development from initial scoping through to successful completion, maintaining high quality standards throughout the process.
