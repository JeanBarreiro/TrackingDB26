from pathlib import Path

import pandas as pd

from transform import transform


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


for file_path in sorted(DATA_DIR.glob("*.parquet")):

    # E - Extract
    df = pd.read_parquet(file_path)

    # El nombre del archivo sin ".parquet"
    table_name = file_path.stem

    print(f"Procesando {table_name}...")

    # T - Transform / Validate
    df = transform(df, table_name)

    print(
        f"  OK - {len(df)} filas validadas."
    )


print("\nExtract y Transform completados correctamente.")