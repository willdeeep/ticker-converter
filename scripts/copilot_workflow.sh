#!/bin/bash
# GitHub Copilot Workflow Automation Scripts
# This script provides utilities for managing the GitHub Copilot workflow

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
MY_DOCS_DIR="$REPO_ROOT/my_docs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
GitHub Copilot Workflow Automation Scripts

Usage: $0 <command> [options]

Commands:
    create-roadmap <project_name>           Create a new project roadmap template
    list-phases <project_name>              List all phases in a project roadmap
    create-phase-issues <project_name> <phase_number>  Create GitHub issues for a phase
    validate-quality                        Run all quality checks
    validate-ci                            Run GitHub Actions locally with act
    development-cycle <issue_number>        Execute the 12-step development cycle
    help                                   Show this help message

Examples:
    $0 create-roadmap "API Enhancement"
    $0 create-phase-issues "API Enhancement" 2
    $0 validate-quality
    $0 development-cycle 42

Requirements:
    - GitHub CLI (gh) installed and authenticated
    - act CLI for local GitHub Actions testing
    - Docker running for act CLI
    - Development dependencies installed (pip install -e .[dev])
EOF
}

# Validate prerequisites
check_prerequisites() {
    local missing_tools=()
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        missing_tools+=("GitHub CLI (gh)")
    fi
    
    # Check act CLI
    if ! command -v act &> /dev/null; then
        missing_tools+=("act CLI")
    fi
    
    # Check Docker
    if ! docker info &> /dev/null; then
        missing_tools+=("Docker (not running)")
    fi
    
    # Check Python environment
    if ! command -v python &> /dev/null; then
        missing_tools+=("Python")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing prerequisites:"
        printf '%s\n' "${missing_tools[@]}" | sed 's/^/  - /'
        exit 1
    fi
}

# Create project roadmap template
create_roadmap() {
    local project_name="$1"
    if [[ -z "$project_name" ]]; then
        log_error "Project name is required"
        echo "Usage: $0 create-roadmap <project_name>"
        exit 1
    fi
    
    local roadmap_file="$MY_DOCS_DIR/TEMP_${project_name// /_}_ROADMAP.md"
    
    if [[ -f "$roadmap_file" ]]; then
        log_warning "Roadmap file already exists: $roadmap_file"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Roadmap creation cancelled"
            exit 0
        fi
    fi
    
    cat > "$roadmap_file" << EOF
# $project_name Development Roadmap

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
   - *Example*: \`pip install -e .[dev]\` and pytest configuration

2. **Define Data Models**
   - Create Pydantic models for core entities
   - Implement validation logic
   - Add comprehensive tests
   - *Reference*: \`my_docs/guides/python_refactoring_guide.md\`

**Phase Completion Milestones**:
- [ ] Development environment fully configured
- [ ] All tests passing with >50% coverage
- [ ] CI/CD pipeline operational
- [ ] Core data models validated

### Phase 2: Core Implementation (Weeks 3-5)
**Objective**: [Define phase 2 objectives]

**Deliverables**:
1. **[Deliverable 1 Name]**
   - [Specific functionality description]
   - [Implementation requirements]
   - [Testing requirements]
   - *Example*: [Code example or reference]

**Phase Completion Milestones**:
- [ ] [Milestone 1]
- [ ] [Milestone 2]

### Phase 3: Integration and Testing (Weeks 6-7)
**Objective**: [Define phase 3 objectives]

**Deliverables**:
1. **[Deliverable 1 Name]**
   - [Specific functionality description]
   - [Implementation requirements]
   - [Testing requirements]

**Phase Completion Milestones**:
- [ ] [Milestone 1]
- [ ] [Milestone 2]

## Dependencies and Constraints
- **External APIs**: [List required external services]
- **Database Requirements**: [Schema and performance needs]
- **Security Considerations**: [Authentication and authorization]
- **Performance Requirements**: [Response time and throughput needs]

## Risk Assessment
- **High Risk**: [Major risks and mitigation strategies]
- **Medium Risk**: [Moderate risks and monitoring approaches]
- **Low Risk**: [Minor risks requiring awareness]

## Success Metrics
- **Functional**: [Feature completeness and accuracy]
- **Performance**: [Speed and efficiency measurements]
- **Quality**: [Code quality and test coverage]
- **User Experience**: [Usability and satisfaction measures]
EOF

    log_success "Created roadmap template: $roadmap_file"
    log_info "Edit the file to customize for your specific project requirements"
}

# List phases in a roadmap
list_phases() {
    local project_name="$1"
    if [[ -z "$project_name" ]]; then
        log_error "Project name is required"
        echo "Usage: $0 list-phases <project_name>"
        exit 1
    fi
    
    local roadmap_file="$MY_DOCS_DIR/TEMP_${project_name// /_}_ROADMAP.md"
    
    if [[ ! -f "$roadmap_file" ]]; then
        log_error "Roadmap file not found: $roadmap_file"
        exit 1
    fi
    
    log_info "Phases in $project_name:"
    grep "^### Phase" "$roadmap_file" | sed 's/^### /  /'
}

# Create GitHub issues for a phase
create_phase_issues() {
    local project_name="$1"
    local phase_number="$2"
    
    if [[ -z "$project_name" || -z "$phase_number" ]]; then
        log_error "Project name and phase number are required"
        echo "Usage: $0 create-phase-issues <project_name> <phase_number>"
        exit 1
    fi
    
    local roadmap_file="$MY_DOCS_DIR/TEMP_${project_name// /_}_ROADMAP.md"
    
    if [[ ! -f "$roadmap_file" ]]; then
        log_error "Roadmap file not found: $roadmap_file"
        exit 1
    fi
    
    log_info "Creating GitHub issues for $project_name Phase $phase_number..."
    
    # Extract deliverables from the specific phase
    local in_phase=false
    local issue_count=0
    
    while IFS= read -r line; do
        if [[ $line =~ ^###\ Phase\ $phase_number: ]]; then
            in_phase=true
            continue
        elif [[ $line =~ ^###\ Phase\ [0-9]+: ]] && [[ $in_phase == true ]]; then
            break
        elif [[ $in_phase == true && $line =~ ^[0-9]+\.\ \*\*(.*)\*\* ]]; then
            local deliverable_title="${BASH_REMATCH[1]}"
            
            # Create GitHub issue
            local issue_body="## Deliverable: $deliverable_title

### Context
- **Project**: $project_name
- **Phase**: Phase $phase_number
- **Roadmap Reference**: \`my_docs/TEMP_${project_name// /_}_ROADMAP.md\`

### Acceptance Criteria
- [ ] [Define specific, testable criteria]
- [ ] [Implementation requirements]
- [ ] [Quality gates passed]

### Implementation Notes
- **Files to modify**: [List expected files]
- **Tests required**: [Test coverage expectations]
- **Documentation updates**: [Required doc changes]

### Definition of Done
- [ ] All tests pass (100% success rate)
- [ ] Pylint score maintained at 10.00/10
- [ ] MyPy validation clean
- [ ] Code coverage above 50%
- [ ] GitHub Actions CI/CD passes
- [ ] Pull request approved and merged"

            gh issue create \
                --title "$deliverable_title" \
                --body "$issue_body" \
                --label "phase-$phase_number,type:feature,priority:medium"
            
            ((issue_count++))
            log_success "Created issue: $deliverable_title"
        fi
    done < "$roadmap_file"
    
    if [[ $issue_count -eq 0 ]]; then
        log_warning "No deliverables found for Phase $phase_number"
    else
        log_success "Created $issue_count issues for Phase $phase_number"
    fi
}

# Validate code quality
validate_quality() {
    log_info "Running comprehensive quality validation..."
    
    local errors=0
    
    # Code formatting
    log_info "Checking code formatting with Black..."
    if ! black --check src/; then
        log_error "Code formatting issues found. Run: black src/"
        ((errors++))
    else
        log_success "Code formatting is correct"
    fi
    
    # Linting
    log_info "Running Pylint analysis..."
    if ! pylint src/ --fail-under=10; then
        log_error "Pylint issues found. Review and fix the reported issues."
        ((errors++))
    else
        log_success "Pylint validation passed (10.00/10)"
    fi
    
    # Type checking
    log_info "Running MyPy type checking..."
    if ! mypy src/; then
        log_error "MyPy type checking failed. Fix type annotation issues."
        ((errors++))
    else
        log_success "MyPy type checking passed"
    fi
    
    # Test execution
    log_info "Running test suite..."
    if ! pytest --cov=src --cov-fail-under=50 tests/; then
        log_error "Tests failed or coverage below 50%. Fix failing tests and improve coverage."
        ((errors++))
    else
        log_success "All tests passed with adequate coverage"
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "All quality checks passed!"
        return 0
    else
        log_error "$errors quality check(s) failed"
        return 1
    fi
}

# Validate CI/CD with act
validate_ci() {
    log_info "Running GitHub Actions locally with act..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Start Docker and try again."
        exit 1
    fi
    
    local errors=0
    
    # Run pytest job
    log_info "Running pytest job..."
    if ! act --job pytest; then
        log_error "pytest job failed"
        ((errors++))
    else
        log_success "pytest job passed"
    fi
    
    # Run lint-check job if it exists
    if act --list | grep -q "lint-check"; then
        log_info "Running lint-check job..."
        if ! act --job lint-check; then
            log_error "lint-check job failed"
            ((errors++))
        else
            log_success "lint-check job passed"
        fi
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "All CI/CD validations passed!"
        return 0
    else
        log_error "$errors CI/CD validation(s) failed"
        return 1
    fi
}

# Execute development cycle for an issue
development_cycle() {
    local issue_number="$1"
    
    if [[ -z "$issue_number" ]]; then
        log_error "Issue number is required"
        echo "Usage: $0 development-cycle <issue_number>"
        exit 1
    fi
    
    log_info "Starting development cycle for issue #$issue_number"
    
    # Get issue details
    local issue_title
    issue_title=$(gh issue view "$issue_number" --json title --jq '.title')
    
    if [[ -z "$issue_title" ]]; then
        log_error "Could not retrieve issue #$issue_number"
        exit 1
    fi
    
    log_info "Issue: $issue_title"
    
    # Create feature branch name
    local branch_name="feature/issue-$issue_number-$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g' | cut -c1-50)"
    
    log_info "Creating feature branch: $branch_name"
    
    # Step 1: Create feature branch
    git checkout dev
    git pull origin dev
    git checkout -b "$branch_name"
    git push -u origin "$branch_name"
    
    log_success "Feature branch created and pushed"
    
    # Remind user of the 12-step process
    cat << EOF

${GREEN}Development cycle initiated for issue #$issue_number${NC}

Follow the 12-step development process:

${YELLOW}Steps 1-3: Preparation and Implementation${NC}
1. ✓ Create Feature Branch (completed)
2. Prepare Tests - Build/update tests before implementation
3. Implement Solution - Complete work per GitHub issue requirements

${YELLOW}Steps 4-6: Initial Quality Assurance${NC}
4. Verify Functionality - Run tests to ensure completion
5. Initial Commit - Professional implementation commit
6. Code Refactoring - Apply refactoring guidelines

${YELLOW}Steps 7-9: Code Quality Enhancement${NC}
7. Refactoring Commit - Separate refactoring improvements commit
8. Linting and Style - Fix whitespace, imports, style issues
9. Static Analysis - Pylint and MyPy validation

${YELLOW}Steps 10-12: Final Validation and Integration${NC}
10. Quality Assurance - Full test suite execution
11. Quality Commit - Code quality improvements commit
12. CI/CD Validation and PR - GitHub Actions validation and pull request

${BLUE}Use these commands during development:${NC}
- Validate quality: $0 validate-quality
- Validate CI/CD: $0 validate-ci
- Create PR: gh pr create --title "$issue_title" --body "Closes #$issue_number"

EOF
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        "create-roadmap")
            check_prerequisites
            create_roadmap "$@"
            ;;
        "list-phases")
            list_phases "$@"
            ;;
        "create-phase-issues")
            check_prerequisites
            create_phase_issues "$@"
            ;;
        "validate-quality")
            check_prerequisites
            validate_quality
            ;;
        "validate-ci")
            check_prerequisites
            validate_ci
            ;;
        "development-cycle")
            check_prerequisites
            development_cycle "$@"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
