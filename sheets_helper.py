from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file(
    "config/service_account.json", scopes=SCOPES
)

def read_sheet(sheet_name):
    service = build("sheets", "v4", credentials=CREDS)
    sheet_id = "<YOUR_GOOGLE_SHEET_ID>"
    
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=sheet_name)
        .execute()
    )

    values = result.get("values", [])
    if not values:
        return pd.DataFrame()

    df = pd.DataFrame(values[1:], columns=values[0])
    return df


def write_sheet(sheet_name, row_index, data_dict):
    service = build("sheets", "v4", credentials=CREDS)
    sheet_id =  "1KxTGp_dw6dFZwekks-JkVeaTqOWyuqjuz6dafEzk4R8"

    for col_name, new_value in data_dict.items():
        col_number = find_column_index(sheet_name, col_name)
        cell = chr(col_number + 65) + str(row_index + 2)

        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{cell}",
            valueInputOption="RAW",
            body={"values": [[new_value]]},
        ).execute()


def find_column_index(sheet_name, col_name):
    df = read_sheet(sheet_name)
    return list(df.columns).index(col_name)
