import pandas as pd

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Минимальная безопасная подготовка:
    - копия
    - создание organization_branch_name (если есть organization_name и branch_name)
    - удаление score == 0
    - преобразование created_at в datetime (если есть)
    """
    df = df.copy()

    # Создаём organization_branch_name, если возможно
    if {"organization_name", "branch_name"}.issubset(df.columns):
        df["organization_branch_name"] = df["organization_name"].astype(str) + ": " + df["branch_name"].astype(str)

    # Преобразуем score в числовой и убираем нули/NaN
    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce")
        df = df[df["score"].notna() & (df["score"] != 0)]

    # Преобразуем created_at, если есть
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    return df