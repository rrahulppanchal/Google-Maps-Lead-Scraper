import io

import pandas as pd


COLUMNS = ["firstName", "email", "phone", "address", "company", "status", "notes"]


def to_dataframe(enriched_data: list[dict]) -> pd.DataFrame:
    """Convert enriched business data to a DataFrame with the standard columns."""
    df = pd.DataFrame(enriched_data, columns=COLUMNS)
    df = df.fillna("")
    return df


def to_csv_bytes(enriched_data: list[dict]) -> bytes:
    """Export enriched data as CSV bytes for download."""
    df = to_dataframe(enriched_data)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    return buffer.getvalue()
