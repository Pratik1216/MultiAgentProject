from seo_app.schema_registry import COLUMN_ALIASES

def resolve_field(schema, sheet, logical_field):
    for candidate in COLUMN_ALIASES.get(logical_field, []):
        if candidate in schema[sheet]:
            return candidate
    raise KeyError(f"Field not found: {logical_field}")
