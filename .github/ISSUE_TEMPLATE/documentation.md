---
name: Documentation Improvement
about: Suggest improvements or report issues with project documentation
title: '[DOCS] '
labels: documentation
assignees: ''
---

## Documentation Issue Type
- [ ] Missing documentation
- [ ] Incorrect/outdated information
- [ ] Unclear explanations
- [ ] Typos/grammar errors
- [ ] Formatting issues
- [ ] Missing examples
- [ ] Broken links
- [ ] Missing API documentation

## Affected Documentation
- [ ] README.md
- [ ] API documentation
- [ ] Installation guide
- [ ] Configuration guide
- [ ] SQL schema documentation
- [ ] Code comments/docstrings
- [ ] Issue templates
- [ ] Contributing guidelines
- [ ] Deployment guide
- [ ] Quick reference guide

## Location Details
**File(s):** `docs/example.md`, `README.md`
**Section:** API Endpoints
**Line number(s):** 45-52

## Current State
Describe what the documentation currently says or what's missing:

```markdown
Current documentation content that needs improvement
```

## Proposed Improvement
Describe what the documentation should say or include:

```markdown
Suggested improved documentation content
```

## Expected Outcome
Clear description of what users should be able to understand or accomplish after the documentation is improved.

## Use Case/Context
Explain the scenario where this documentation improvement would be helpful:
- New developer onboarding
- API integration
- Troubleshooting
- Configuration setup
- SQL query development

## Supporting Information

### Error Messages (if applicable)
If users encounter errors due to unclear documentation:
```
Error message or confusion that results from current documentation
```

### Related Code Examples
If requesting code examples or improvements to existing ones:
```python
# Example of what should be documented
from ticker_converter.models import MarketDataPoint
from ticker_converter.database import get_db_session

# This functionality needs better documentation
data_point = MarketDataPoint(
    symbol="AAPL",
    timestamp=datetime.now(),
    price=150.25,
    volume=1000
)
```

### SQL Examples (if applicable)
```sql
-- SQL queries that should be documented
SELECT 
    ds.symbol,
    fs.closing_price,
    fs.volume
FROM dim_stocks ds
JOIN fact_stock_prices fs ON ds.stock_id = fs.stock_id
WHERE fs.date_id = (SELECT MAX(date_id) FROM fact_stock_prices);
```

## Priority Level
- [ ] Critical: Blocks user adoption or causes significant confusion
- [ ] High: Important for user experience, should be addressed soon
- [ ] Medium: Helpful improvement, moderate impact
- [ ] Low: Nice to have, minor enhancement

## Audience Impact
Who would benefit from this documentation improvement?
- [ ] New contributors
- [ ] API users/integrators
- [ ] DevOps/deployment teams
- [ ] End users
- [ ] Data analysts
- [ ] Database administrators

## Research Done
- [ ] Searched existing documentation for similar content
- [ ] Checked other projects for documentation patterns
- [ ] Reviewed user feedback or questions
- [ ] Tested current instructions/examples

## Suggested Implementation
How should this be implemented?
- [ ] Add new documentation file
- [ ] Update existing file
- [ ] Add inline code comments
- [ ] Create tutorial/walkthrough
- [ ] Add FAQ section
- [ ] Improve existing examples
- [ ] Add troubleshooting section

## Additional Resources
Links to external resources, standards, or examples that could help:
- Documentation style guides
- Similar projects with good examples
- Relevant standards or best practices
- User feedback or support requests

## Visual Aids
If applicable, describe or include:
- Diagrams that would be helpful
- Screenshots of current vs. desired state
- Flowcharts or architecture diagrams
- Code formatting examples

## Related Issues
- Documentation for: #XXX
- Follows up on: #XXX
- Blocks: #XXX
- Related to: #XXX
