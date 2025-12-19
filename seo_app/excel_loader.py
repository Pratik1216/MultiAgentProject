import pandas as pd

def load_screaming_frog(file_path: str) -> dict:
    """
    Loads all sheets into memory as DataFrames.
    """
    xls = pd.ExcelFile(file_path)
    sheets = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        sheets[sheet.lower()] = df

    return sheets
