import zipfile
import shutil
import os
import pandas as pd


def unzip_file(zip_path: str, extract_to: str):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def zip_file(file_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(file_path, os.path.basename(file_path))


def cleanup(path: str):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

def sanitize_excel_values(df: pd.DataFrame):
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: f"'{x}" if isinstance(x, str) and x.strip().startswith('=') else x
        )
    return df

