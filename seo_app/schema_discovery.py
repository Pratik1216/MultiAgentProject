def discover_schema(sheets: dict) -> dict:
    return {name: set(df.columns) for name, df in sheets.items()}
