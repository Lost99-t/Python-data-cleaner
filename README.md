# Python Data Cleaner

**Genesis Skills Lab — Python Skills Sprint 001**

A reusable CSV-cleaning prototype built with Python and pandas. It demonstrates data standardisation, selected numeric and currency conversion, duplicate removal, basic validation, missing-value handling, and CSV quality reporting.

## Features

- Reads CSV files with pandas.
- Trims whitespace and treats blank strings as missing values.
- Standardises selected text columns using title case.
- Converts selected numeric columns, including explicitly supplied currency symbols and correctly grouped thousands separators.
- Rejects malformed comma grouping rather than silently interpreting it as a number.
- Removes duplicate rows after standardisation and conversion.
- Fills missing numeric values with the column median and missing text values with `Unknown`.
- Flags basic email-format, numeric-value, and non-negative-value validation issues.
- Exports cleaned data, validation issues, and a quality report.

## Project structure

```text
Python-Data-Cleaner/
├── data_cleaner.py
├── Python_Data_Cleaner.ipynb
├── README.md
├── requirements.txt
├── .gitignore
├── sample_data/
│   ├── sample_customers.csv
│   └── currency_test.csv
└── test_evidence/
    ├── sample_cleaner_output.csv
    ├── sample_cleaner_output_validation_issues.csv
    ├── sample_cleaner_output_quality_report.csv
    ├── currency_test_results.csv
    ├── currency_test_results_validation_issues.csv
    └── currency_test_results_quality_report.csv
```

## Requirements and setup

- Python 3
- pandas

Install the dependency:

```bash
python -m pip install -r requirements.txt
```

## Quick start

Place your input CSV in the project folder (or provide its path), then run:

```python
from data_cleaner import run_data_cleaner

result = run_data_cleaner(
    "customers.csv",
    email_column="Email",
    numeric_columns=["Purchase"],
    non_negative_columns=["Purchase"],
    normalize_columns=["City"],
    currency_symbols=["₦"],
    output_prefix="customers_cleaned"
)

if result is not None:
    cleaned, issues, report = result
```

The runner creates:

- `customers_cleaned.csv`
- `customers_cleaned_validation_issues.csv`
- `customers_cleaned_quality_report.csv`

Column names are case-sensitive and must match the CSV headers. Only include currency symbols that actually appear in the selected numeric columns.

## Notebook

Open `Python_Data_Cleaner.ipynb` in Jupyter or Google Colab. Run the cells from top to bottom. The notebook builds sample regression and currency datasets and demonstrates the pipeline. If using your own CSV, update the filename and column names in the run cell.

## Test evidence

The `test_evidence/` directory contains representative outputs from the included sample regression and currency examples.

The regression example has 5 input records, 1 duplicate removed, 4 final records, and 2 records flagged for review.

The currency example demonstrates conversion of plain numbers, comma-grouped values, and the explicitly supplied naira symbol. It has 5 input records, 5 final records, and 2 records flagged for review.

## Limitations and safe use

- Email validation checks basic format only; it does not verify deliverability.
- Numeric missing values are median-imputed. Review flagged issues and retain the original file.
- Only selected columns are converted to numeric values.
- Only explicitly supplied currency symbols are removed.
- Title-casing can change acronyms and intentional name casing.
- The duplicate count in the report assumes duplicate removal is the only operation that removes rows.
- The runner prints an error and returns `None` when processing fails; check the return value before unpacking it.
- This prototype is intended for learning and demonstration. It is not a production-certified data-quality system.

## Project status

Completed working prototype for **Python Skills Sprint 001**. The module and notebook were tested locally during the sprint. The included sample outputs are retained as illustrative test evidence; users should rerun the notebook or module in their own environment before relying on results.
