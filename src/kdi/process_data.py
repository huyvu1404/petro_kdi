
import pandas as pd

def fill_content_column(row):
    if pd.notna(row["Title"]) and row["Title"] != "":
        return row["Title"]
    elif pd.notna(row["Description"]) and row["Description"] != "":
        return row["Description"]
    elif pd.notna(row["Content"]) and row["Content"] != "":
        return row["Content"]
    else:
        return ""

def create_new_channel_group(row):
    if row["Channel"] and (row["Channel"] == "Threads" or row["Channel"] == "Linkedln"):
        return "Social"
    else:
        return row["Channel"]
    
def create_new_channel(row):
    facebook_sub_channels_mapping = {
        "fbGroup": "Facebook Group",
        "fbPage": "Facebook Page",
        "fbUser": "Facebook User"
    }
    if row["Channel"] and row["Channel"] == "Facebook":
        if row["Type"]:
            for sub_channel, sub_channel_name in facebook_sub_channels_mapping.items():
                if sub_channel in row["Type"]:
                    return sub_channel_name
        return "Facebook"
    else:
        return row["Channel"]
    

def process_excel(file_path, fill=False):
    try:
        file_path = file_path if isinstance(file_path, list) else [file_path]
        all_data = pd.DataFrame()
        for path in file_path:
            xls = pd.ExcelFile(path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                all_data = pd.concat([all_data, df], ignore_index=True)
        if 'Channel' in all_data.columns:
            all_data["New Channel"] = all_data.apply(create_new_channel, axis=1)
            all_data["Channel Group"] = all_data.apply(create_new_channel_group, axis=1)
        if fill:
            if all(col in all_data.columns for col in ['Content', 'Title', 'Description']):
                all_data['Content'] = all_data.apply(fill_content_column, axis=1)
                all_data.drop(columns=['Title', 'Description'], inplace=True)
    except Exception as e:
        print("Error processing Excel file:", e)
    return all_data
