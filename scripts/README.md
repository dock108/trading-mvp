# Scripts Directory

Utility scripts and tools for the Trading MVP platform.

## 📁 Contents

### `summary_report.py`
Generates comprehensive analysis reports from trade execution logs.

**Usage:**
```bash
python scripts/summary_report.py
```

**Features:**
- Parses CSV trade logs
- Calculates performance metrics
- Generates human-readable reports
- Tracks portfolio allocation over time

**Output:**
- Weekly allocation tracking
- Strategy performance comparison
- Trade execution summaries
- P&L analysis

## 🛠️ Development Scripts

This directory contains various utility scripts for:
- **Data Analysis**: Performance reporting and trade analysis
- **Maintenance**: Database cleanup and optimization
- **Testing**: Integration testing and data validation
- **Deployment**: Build and deployment utilities

## 📊 Usage Examples

### Generate Performance Report
```bash
# Generate report from latest trades
python scripts/summary_report.py

# Analyze specific date range
python scripts/summary_report.py --start-date 2023-01-01 --end-date 2023-12-31
```

### Batch Operations
```bash
# Run multiple analysis scripts
./scripts/run_analysis.sh

# Generate all reports
./scripts/generate_reports.sh
```

---

These scripts complement the main platform by providing additional analysis and maintenance capabilities.