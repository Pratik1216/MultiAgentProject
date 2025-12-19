from seo_app.schema_resolver import *

def apply_filters(df, filters):
    for f in filters:
        col = f["column"]
        op = f["operator"]
        val = f["value"]

        if op == "==":
            df = df[df[col] == val]
        elif op == ">":
            df = df[df[col] > val]
        elif op == "contains":
            df = df[df[col].astype(str).str.contains(val, na=False)]

    return df


def execute_intent(sheets, schema, intent):
    df = sheets[intent["sheet"]]

    resolved_filters = []
    for f in intent["filters"]:
        physical = resolve_field(schema, intent["sheet"], f["field"])
        resolved_filters.append({**f, "column": physical})

    df = apply_filters(df, resolved_filters)

    if intent["groupby"]:
        df = df.groupby(intent["groupby"]).agg(intent["aggregations"]).reset_index()

    return df
