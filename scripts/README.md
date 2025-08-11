# Scripts Directory

This directory contains utility scripts for the ticker-converter project.

## Available Scripts

### `demo_capabilities.py`
**Purpose**: Demonstrates the complete Alpha Vantage API functionality

**Usage**:
```bash
python scripts/demo_capabilities.py
```

**Features**:
- Shows stock data retrieval (AAPL example)
- Demonstrates forex data (EUR/USD example)  
- Shows cryptocurrency data (BTC/USD example)
- Comprehensive market analysis across asset classes

**Requirements**: ALPHA_VANTAGE_API_KEY environment variable must be set

---

### `examine_stored_data.py`
**Purpose**: Examines locally stored data files without making API calls

**Usage**:
```bash
python scripts/examine_stored_data.py
```

**Features**:
- Analyzes JSON and Parquet files in `raw_data_output/`
- Shows file sizes, record counts, and data ranges
- Displays latest market values
- Zero API calls - uses only local files

**Note**: Run this after storing data to verify storage integrity

---

### `cleanup_data.py`  
**Purpose**: Manages stored data files by keeping only the latest version of each dataset

**Usage**:
```bash
python scripts/cleanup_data.py
```

**Features**:
- Groups files by symbol and data type
- Keeps only the most recent file for each combination
- Shows space savings and cleanup summary
- Helps maintain clean storage directory

**Note**: Use this periodically to prevent accumulation of old data files

## Best Practices

1. **Set API Key**: All scripts require `ALPHA_VANTAGE_API_KEY` environment variable
2. **Rate Limits**: Be mindful of Alpha Vantage's free tier limit (25 requests/day)
3. **Data Storage**: Scripts expect data in `raw_data_output/` directory structure
4. **Execution**: Run scripts from the project root directory for proper imports

## Integration with Main Application

These scripts complement the main application by providing:
- **Demonstration** of API capabilities
- **Maintenance** tools for data storage
- **Analysis** utilities for stored data

For testing functionality, use the integration tests in `tests/integration/` instead.
