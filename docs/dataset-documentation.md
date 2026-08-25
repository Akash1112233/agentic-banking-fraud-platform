# Dataset documentation

## Dataset

IBM Transactions for Anti-Money Laundering (AML), downloaded from Kaggle.

## Files

- `HI-Small_Trans.csv`: transaction-level records and the `Is Laundering` target field
- `HI-Small_accounts.csv`: bank and account/entity information
- `HI-Small_Patterns.txt`: predefined laundering attempts and patterns such as fan-out, cycle, and gather-scatter

## Handling rules

- Keep identifiers as strings.
- Do not use Excel to save or convert the CSV files.
- Do not commit raw data or credentials to GitHub.
- Verify schemas and labels with Python before modeling.
