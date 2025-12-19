COLUMN_ALIASES = {
    "url": ["address", "url"],
    "https": ["https"],
    "title_length": ["title_1_length", "title_length"],
    "indexability": ["indexability", "index_status"],
    "status_code": ["status_code"],
    "meta_description_length": ["meta_description_length"],
    "h1_count": ["h1-1", "h1_count"],
}


def resolve_column(df, logical_name: str):
    for col in COLUMN_ALIASES.get(logical_name, []):
        if col in df.columns:
            return col
    raise KeyError(f"Column not found: {logical_name}")
