# /eda

---
name: eda
description: Run exploratory data analysis on project data
---

Run exploratory data analysis on data files.

## Usage

```
/eda                          # Analyze all files in data/
/eda data/sales.csv           # Analyze specific file
/eda --correlations           # Focus on correlations
/eda --distributions          # Focus on distributions
/eda --quality                # Focus on data quality issues
```

## What EDA Produces

1. **Data Profile**
   - Shape (rows x columns)
   - Memory usage
   - Column types (numeric, categorical, datetime)

2. **Column Details**
   - Non-null counts
   - Unique values
   - For numeric: mean, median, std, min, max, quartiles
   - For categorical: top values, value counts

3. **Data Quality**
   - Missing values (total and by column)
   - Duplicate rows
   - High-null columns (>30% missing)
   - Constant columns (single value)
   - High-cardinality columns (>90% unique)

4. **Correlations**
   - Correlation matrix for numeric columns
   - Top correlated pairs

5. **Analysis Suggestions**
   - Recommended next steps based on data characteristics

## Auto-EDA

When data is added to `data/`, KIE automatically:
1. Detects new files
2. Runs quick profile
3. Displays summary

To disable: set `auto_eda: false` in spec.yaml

## Output

- Console: Formatted report
- File: `outputs/eda_profile.yaml` (structured data)

## Example Output

```
============================================================
EXPLORATORY DATA ANALYSIS REPORT
============================================================

Dataset: 800 rows x 5 columns (0.07 MB)

Column Types:
  Numeric: 4
  Categorical: 1
  Datetime: 0

Data Quality:
  Missing values: 0.0%
  Duplicate rows: 0 (0.0%)

------------------------------------------------------------
COLUMN DETAILS
------------------------------------------------------------

revenue (float64)
  Non-null: 800 | Null: 0 (0.0%)
  Unique: 722 (90.2%)
  Range: 500.00 - 4,998.00
  Mean: 2,769.15 | Median: 2,764.00 | Std: 1,259.54

channel (object)
  Non-null: 800 | Null: 0 (0.0%)
  Unique: 4 (0.5%)
  Top values: ['email marketing', 'referral', 'paid advertising', 'social media']

------------------------------------------------------------
CORRELATIONS (top pairs)
------------------------------------------------------------
  cost <-> conversion_rate: -0.537
  conversion_rate <-> revenue: -0.050

------------------------------------------------------------
SUGGESTED ANALYSES
------------------------------------------------------------
  1. Correlation analysis between 4 numeric columns
  2. Group-by analysis: channel vs revenue
  3. Distribution analysis for 'channel' (4 categories)

============================================================
```

## Next Steps

After EDA:
```
/analyze   # Generate insights from data
/build     # Create deliverables
```
