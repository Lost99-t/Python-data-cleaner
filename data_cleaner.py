import pandas as pd

def convert_numeric_values(series, currency_symbols=None):
    values = series.astype("string").str.strip()

    # Remove only currency symbols explicitly supplied by the user.
    for symbol in currency_symbols or []:
        values = values.str.replace(symbol, "", regex=False).str.strip()

    # Accept ordinary numbers and correctly grouped thousands separators.
    valid_number_format = values.str.match(
        r"^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$",
        na=False
    )
    has_comma = values.str.contains(",", na=False)

    # Reject malformed comma grouping instead of silently misreading it.
    values = values.where(~has_comma | valid_number_format)
    values = values.str.replace(",", "", regex=False)

    return pd.to_numeric(values, errors="coerce")

def clean_data(
    dataframe,
    normalize_columns=None,
    numeric_columns=None,
    currency_symbols=None
):
    dataframe = dataframe.copy()
    unresolved_columns = []

    requested_columns = (
        (normalize_columns or []) +
        (numeric_columns or [])
    )

    for column in requested_columns:
        if column not in dataframe.columns:
            raise ValueError(f"Column not found: {column}")

    # 1. Trim whitespace and convert blank strings to missing values
    text_columns = dataframe.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        dataframe[column] = dataframe[column].apply(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )
        dataframe[column] = dataframe[column].replace("", pd.NA)

    # 2. Standardise selected text columns
    for column in normalize_columns or []:
        dataframe[column] = dataframe[column].apply(
            lambda value: value.title()
            if isinstance(value, str)
            else value
        )

    # 3. Convert selected numeric columns using shared parser
    for column in numeric_columns or []:
        dataframe[column] = convert_numeric_values(
            dataframe[column],
            currency_symbols=currency_symbols
        )

    # 4. Remove duplicates after standardisation
    dataframe = dataframe.drop_duplicates().copy()

    detected_numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns

    text_columns = dataframe.select_dtypes(
        include=["object", "string"]
    ).columns

    # 5. Handle missing numeric values
    for column in detected_numeric_columns:
        if dataframe[column].notna().any():
            dataframe[column] = dataframe[column].fillna(
                dataframe[column].median()
            )
        else:
            unresolved_columns.append(column)

    # 6. Handle missing text values
    for column in text_columns:
        if dataframe[column].isna().all():
            unresolved_columns.append(column)
        else:
            dataframe[column] = dataframe[column].fillna("Unknown")

    dataframe = dataframe.reset_index(drop=True)

    return dataframe, unresolved_columns

def validate_data(
    dataframe,
    email_column=None,
    non_negative_columns=None,
    numeric_columns=None,
    currency_symbols=None
):
    issues = pd.DataFrame(index=dataframe.index)
    issues["Issues"] = ""

    if email_column is not None:
        if email_column not in dataframe.columns:
            raise ValueError("Email column not found")

        emails = dataframe[email_column].astype("string")

        missing = (
            emails.isna() | emails.str.strip().eq("")
        ).fillna(False)

        invalid = (
            ~emails.str.match(
                r"^[\w.+-]+@[\w-]+\.[\w.-]+$",
                na=False
            ) & ~missing
        )

        issues.loc[missing, "Issues"] += "Missing email; "
        issues.loc[invalid, "Issues"] += "Invalid email; "

    for column in numeric_columns or []:
        if column not in dataframe.columns:
            raise ValueError(f"Column not found: {column}")

        raw = dataframe[column].astype("string")
        missing = (
            raw.isna() | raw.str.strip().eq("")
        ).fillna(False)

        converted = convert_numeric_values(
            dataframe[column],
            currency_symbols=currency_symbols
        )

        invalid = ~missing & converted.isna()

        issues.loc[missing, "Issues"] += (
            f"Missing value in {column}; "
        )
        issues.loc[invalid, "Issues"] += (
            f"Non-numeric value in {column}; "
        )

    for column in non_negative_columns or []:
        if column not in dataframe.columns:
            raise ValueError(f"Column not found: {column}")

        converted = convert_numeric_values(
            dataframe[column],
            currency_symbols=currency_symbols
        )

        issues.loc[converted < 0, "Issues"] += (
            f"Negative value in {column}; "
        )

    flagged = issues[issues["Issues"] != ""].copy()
    flagged.insert(0, "Original row", flagged.index)

    return flagged

def process_dataset(
    dataframe,
    email_column=None,
    non_negative_columns=None,
    normalize_columns=None,
    numeric_columns=None,
    currency_symbols=None
):
    validation_results = validate_data(
        dataframe,
        email_column=email_column,
        non_negative_columns=non_negative_columns,
        numeric_columns=numeric_columns,
        currency_symbols=currency_symbols
    )

    cleaned_data, unresolved_columns = clean_data(
        dataframe,
        normalize_columns=normalize_columns,
        numeric_columns=numeric_columns,
        currency_symbols=currency_symbols
    )

    return cleaned_data, validation_results, unresolved_columns

def generate_quality_report(
    original_df,
    cleaned_df,
    validation_results,
    unresolved_columns
):
    original_rows = len(original_df)
    final_rows = len(cleaned_df)

    # This cleaner removes records only through deduplication
    duplicates_removed = original_rows - final_rows

    missing_values = original_df.isna().sum().sum()
    remaining_missing = cleaned_df.isna().sum().sum()

    missing_by_column = original_df.isna().sum()
    columns_with_missing = missing_by_column[
        missing_by_column > 0
    ]

    if len(columns_with_missing) > 0:
        missing_details = "; ".join(
            f"{column}: {count}"
            for column, count in columns_with_missing.items()
        )
    else:
        missing_details = "None"

    issue_counts = {}

    for issue_text in validation_results["Issues"]:
        for issue in str(issue_text).split(";"):
            issue = issue.strip()
            if issue:
                issue_counts[issue] = (
                    issue_counts.get(issue, 0) + 1
                )

    report_data = {
        "Metric": [
            "Original records",
            "Duplicates removed",
            "Missing values found",
            "Columns with missing values",
            "Final records",
            "Records flagged for review",
            "Unresolved columns",
            "Missing values remaining"
        ],
        "Value": [
            original_rows,
            duplicates_removed,
            missing_values,
            missing_details,
            final_rows,
            len(validation_results),
            ", ".join(unresolved_columns)
            if unresolved_columns else "None",
            remaining_missing
        ]
    }

    report_df = pd.DataFrame(report_data)

    if issue_counts:
        validation_summary = pd.DataFrame({
            "Metric": [
                f"Validation issue: {issue}"
                for issue in issue_counts
            ],
            "Value": list(issue_counts.values())
        })
    else:
        validation_summary = pd.DataFrame({
            "Metric": ["Validation issues"],
            "Value": ["None"]
        })

    return pd.concat(
        [report_df, validation_summary],
        ignore_index=True
    )

def run_data_cleaner(
    input_file,
    email_column=None,
    non_negative_columns=None,
    normalize_columns=None,
    numeric_columns=None,
    currency_symbols=None,
    output_prefix="cleaned_data"
):
    try:
        if not output_prefix or not output_prefix.strip():
            raise ValueError("Output name cannot be empty.")

        original_df = pd.read_csv(input_file)

        if original_df.empty:
            raise ValueError("The CSV file contains no records.")

        cleaned_df, validation_results, unresolved_columns = (
            process_dataset(
                original_df,
                email_column=email_column,
                non_negative_columns=non_negative_columns,
                normalize_columns=normalize_columns,
                numeric_columns=numeric_columns,
                currency_symbols=currency_symbols
            )
        )

        quality_report = generate_quality_report(
            original_df,
            cleaned_df,
            validation_results,
            unresolved_columns
        )

        cleaned_file = f"{output_prefix}.csv"
        validation_file = f"{output_prefix}_validation_issues.csv"
        report_file = f"{output_prefix}_quality_report.csv"

        cleaned_df.to_csv(cleaned_file, index=False)
        validation_results.to_csv(validation_file, index=False)
        quality_report.to_csv(report_file, index=False)

        print("DATA CLEANING COMPLETED")
        print("------------------------")
        print("Original records:", len(original_df))
        print("Cleaned records:", len(cleaned_df))
        print("Records flagged:", len(validation_results))
        print("Unresolved columns:", unresolved_columns)

        print("\nEXPORTED FILES")
        print(cleaned_file)
        print(validation_file)
        print(report_file)

        return cleaned_df, validation_results, quality_report

    except FileNotFoundError:
        print("ERROR: The input CSV file could not be found.")
    except pd.errors.EmptyDataError:
        print("ERROR: The CSV file is empty.")
    except ValueError as error:
        print("ERROR:", error)
    except Exception as error:
        print("UNEXPECTED ERROR:", error)
