

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDS = Credentials.from_service_account_file(
    "config/service_account.json", scopes=SCOPES
)

def create_folder(folder_name):
    service = build("drive", "v3", credentials=CREDS)

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }

    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]


def upload_file(path, folder_id):
    service = build("drive", "v3", credentials=CREDS)

    file_metadata = {"name": path.split("/")[-1], "parents": [folder_id]}
    media = MediaFileUpload(path, resumable=True)

    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    return f"https://drive.google.com/file/d/{uploaded['id']}/view"


