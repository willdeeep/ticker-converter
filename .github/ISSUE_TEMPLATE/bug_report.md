---
name: Bug Report
about: Create a report to help us improve the ticker-converter project
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
Clear and concise description of what the bug is.

## Expected Behavior
Describe what you expected to happen.

## Actual Behavior
Describe what actually happened. Include any error messages or unexpected outputs.

## Steps to Reproduce
1. Navigate to '...'
2. Execute command '...'
3. Input data '...'
4. See error

## Environment Information

### System Environment
- OS: [e.g., Ubuntu 20.04, macOS 12.0, Windows 11]
- Python Version: [e.g., 3.9.7, 3.10.2, 3.11.1]
- Virtual Environment: [e.g., venv, conda, pipenv]

### Application Environment
- Project Version: [e.g., v1.2.3, main branch, commit hash]
- Database: [e.g., SQLite 3.36, PostgreSQL 13.8]
- API Dependencies: [e.g., Alpha Vantage, Currency API]

### Browser/Client (if applicable)
- Browser: [e.g., Chrome 105, Firefox 104, Safari 15]
- API Client: [e.g., curl, Postman, Python requests]

## Error Messages and Logs

### Error Output
```
Paste any error messages, stack traces, or relevant log output here
```

### API Response (if applicable)
```json
{
  "error": "Error message from API",
  "details": "Additional error details"
}
```

### Database Logs (if applicable)
```
Paste relevant database error logs or query outputs
```

## Configuration Files
If relevant, include sanitized configuration details:

### Environment Variables
```bash
# Remove any sensitive information like API keys
DATABASE_URL=sqlite:///./data/stocks.db
API_TIMEOUT=30
```

### SQL Queries (if applicable)
```sql
-- Include the problematic query that causes the issue
SELECT * FROM fact_stock_prices WHERE date_id = ?;
```

## Screenshots/Visual Evidence
If applicable, add screenshots to help explain the problem.

## Minimal Reproducible Example
Provide a minimal code example that reproduces the issue:

```python
# Minimal example demonstrating the bug
from ticker_converter.api_clients import AlphaVantageClient

client = AlphaVantageClient()
# This call causes the error
result = client.get_daily_data("INVALID_SYMBOL")
```

## Impact Assessment
- [ ] Critical: System completely unusable
- [ ] High: Major feature broken, workaround difficult
- [ ] Medium: Feature partially broken, workaround available
- [ ] Low: Minor issue, cosmetic problem

## Affected Components
- [ ] API endpoints
- [ ] Database operations
- [ ] ETL pipeline
- [ ] Data validation
- [ ] Authentication
- [ ] Performance
- [ ] Documentation

## Possible Solution
If you have ideas on how to fix the issue, describe them here.

## Workaround
If you've found a temporary workaround, describe it here.

## Additional Context
Add any other context about the problem here. This might include:
- When the issue first appeared
- Frequency of occurrence
- Related issues or PRs
- External factors that might contribute

## Investigation Steps Taken
- [ ] Checked application logs
- [ ] Verified database connectivity
- [ ] Tested with different inputs
- [ ] Reproduced in different environments
- [ ] Searched existing issues for duplicates

## Related Issues
- Similar to: #XXX
- Blocks: #XXX  
- Blocked by: #XXX
