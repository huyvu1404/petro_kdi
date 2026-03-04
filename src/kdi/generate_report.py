import os
import uuid
import zipfile
import pandas as pd

from src.kdi.process_data import process_excel
from src.kdi.reports.daily_report import create_daily_report, negative_excel
from src.kdi.reports.weekly_report import create_weekly_report
from src.kdi.export import export_to_excel
from src.utils import unzip_file, sanitize_excel_values


def _process_daily(excel_files: list[str], output_dir: str):
    if not excel_files:
        raise ValueError("No Excel files found for daily report")

    # Process data for HTML report (with fill=True)
    all_data_html = process_excel(excel_files, True)
    
    # Process data for Excel export (with fill=False to keep Title and Description)
    all_data_excel = process_excel(excel_files, False)
    all_data_excel = sanitize_excel_values(all_data_excel)

    # Apply labels only for "La Tien Villa" topic
    if "Topic" in all_data_excel.columns:
        la_tien_mask = all_data_excel["Topic"] == "La Tien Villa"
        if la_tien_mask.any():
            all_data_excel.loc[la_tien_mask] = _apply_labels_to_dataframe(
                all_data_excel[la_tien_mask]
            )
    
    # Get date range for filename
    all_data_excel['PublishedDate'] = pd.to_datetime(all_data_excel['PublishedDate'])
    start_date = all_data_excel['PublishedDate'].min().strftime('%d.%m')
    end_date = all_data_excel['PublishedDate'].max().strftime('%d.%m.%Y')
    
    # Get unique topics
    topics = all_data_excel['Topic'].dropna().unique()
    
    # Create separate Excel files for each topic
    for topic in topics:
        topic_data = all_data_excel[all_data_excel['Topic'] == topic].copy()
        
        # Use topic name for filename
        safe_topic = topic.replace('/', '_').replace('\\', '_')
        
        # Create _Daily data file (raw data without formatting)
        filename = f"{safe_topic}_Daily data_{start_date}_{end_date}.xlsx"
        output_path = os.path.join(output_dir, filename)
        
        # Remove New Channel and Channel Group columns before export
        daily_data = topic_data.copy()
        columns_to_drop = ['New Channel', 'Channel Group']
        daily_data = daily_data.drop(columns=[col for col in columns_to_drop if col in daily_data.columns])
        
        # Export raw data to Excel without formatting
        daily_data.to_excel(output_path, index=False)
        
        # Create _negative file (negative data only with formatting)
        negative_file, _ = negative_excel(topic_data)
        if negative_file:
            filename = f"{safe_topic}_negative.xlsx"
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(negative_file.getvalue())

    # Create HTML report with all topics
    html_bytes = create_daily_report(all_data_html)

    with open(os.path.join(output_dir, "report.html"), "wb") as f:
        f.write(html_bytes)

def _process_weekly(current_files: list[str],
    output_dir: str,
    last_week_files: list[str]
):

    if not current_files or not last_week_files:
        raise ValueError("Missing Excel files for weekly report")

    # Process data for HTML report (with fill=True to merge Title/Description into Content)
    current_data_html = process_excel(current_files, True)
    last_week_data_html = process_excel(last_week_files, True)
    
    # Process data for Excel export (with fill=False to keep Title and Description columns)
    current_data_excel = process_excel(current_files, False)
    
    # Apply labels only for "La Tien Villa" topic
    if "Topic" in current_data_excel.columns:
        la_tien_mask = current_data_excel["Topic"] == "La Tien Villa"
        if la_tien_mask.any():
            current_data_excel.loc[la_tien_mask] = _apply_labels_to_dataframe(
                current_data_excel[la_tien_mask]
            )
    
    # Get unique topics from current week
    topics = current_data_excel['Topic'].dropna().unique()
    
    # Create separate Excel file for each topic
    for topic in topics:
        topic_data = current_data_excel[current_data_excel['Topic'] == topic]
        
        converted_file, _ = export_to_excel(topic_data)
        if converted_file is None:
            continue
            
        # Use topic name for filename
        safe_topic = topic.replace('/', '_').replace('\\', '_')
        filename = f"{safe_topic}_Weekly.xlsx"

        with open(os.path.join(output_dir, filename), "wb") as f:
            f.write(converted_file.getvalue())

    # Create HTML report with all topics (using filled data)
    html_bytes = create_weekly_report(current_data_html, last_week_data_html)
    with open(os.path.join(output_dir, "report.html"), "wb") as f:
        f.write(html_bytes)

def _list_excel_files(dir_path: str) -> list[str]:
    return [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.endswith(".xlsx")
    ]

def _assign_label(text):
    if not text or pd.isna(text):
        return " "
    
    text = str(text).lower()
    label_map = {
        "Somerset Nha Trang": ["somerset nha trang", "somerset"],
        "La Tien Villa": ["la tien villa", "la tiên villa", "la tiên", "la tien"],
        "Masterise Homes": ["masterise homes", "mesterise"],
        "Gran Melia Nha Trang": ["gran melia", "gran melia nha trang", "gran meliá"],
        "Flex Home": ["flex home"],
        "Paramount": ["paramount"],
        "San Home": ["san home"],
        "Villa Le Corail": ["villa le corail", "le corail", "corail"]
    }

    for label, keywords in label_map.items():
        for keyword in keywords:
            if keyword in text or keyword.replace(" ", "") in text:
                return label
    return " "


def _apply_labels_to_dataframe(df):
    """Apply labels to dataframe based on Type and content fields"""
    def assign_row_label(row):
        # Check if Type contains 'topic'
        type_val = str(row.get("Type", "")).lower()
        
        if "topic" in type_val:
            # Check Title, Content, Description
            combined_text = " ".join([
                str(row.get("Title", "")),
                str(row.get("Content", "")),
                str(row.get("Description", ""))
            ]).lower()
        else:
            # Check Title and Content only
            combined_text = " ".join([
                str(row.get("Title", "")),
                str(row.get("Content", ""))
            ]).lower()
        
        return _assign_label(combined_text)
    
    # Apply label assignment
    df["Labels1"] = df.apply(assign_row_label, axis=1)
    return df



def generate_kdi_report(
    zip_path: str,
    work_dir: str,
    report_type: str,
    last_week_zip: str | None = None
) -> tuple[str, str]:
    """
    Returns:
        zip_output_path: path to result zip
        work_dir: temp working directory (for cleanup)
    """

    input_dir = os.path.join(work_dir, "input", "current")
    output_dir = os.path.join(work_dir, "output")

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    zip_output_path = os.path.join(work_dir, "result.zip")

    # ===== Unzip current =====
    unzip_file(zip_path, input_dir)

    current_files = _list_excel_files(input_dir)

    if not current_files:
        raise ValueError("No Excel files found in current zip")

    # ===== Daily =====
    if report_type == "daily":
        _process_daily(current_files, output_dir)

    # ===== Weekly =====
    elif report_type == "weekly":
        last_week_files = None

        if last_week_zip:
            last_week_dir = os.path.join(work_dir, "input", "last_week")
            os.makedirs(last_week_dir, exist_ok=True)
            unzip_file(last_week_zip, last_week_dir)

            last_week_files = _list_excel_files(last_week_dir)

            if not last_week_files:
                raise ValueError("No Excel files found in last_week zip")

        _process_weekly(
            current_files=current_files,
            last_week_files=last_week_files,
            output_dir=output_dir
        )

    else:
        raise ValueError("Invalid report_type")

    # ===== Zip output =====
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, output_dir)
                zipf.write(full_path, arcname)

    return zip_output_path, work_dir
