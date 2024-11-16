# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import Flow
# from googleapiclient.discovery import build
# import os
# import json
# from aiohttp import web
# import asyncio

# SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# class GoogleSheetsModule:
#     def __init__(self):
#         self.creds = None
#         self.service = None
#         self.credentials_path = "/app/credentials.json"
#         self.redirect_uri = "http://localhost:8080/oauth2callback"

#     def load_credentials(self):
#         if os.path.exists("token.json"):
#             self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

#         if not self.creds or not self.creds.valid:
#             if self.creds and self.creds.expired and self.creds.refresh_token:
#                 self.creds.refresh(Request())
#             else:
#                 return False

#             with open("token.json", "w") as token:
#                 token.write(self.creds.to_json())

#         self.service = build("sheets", "v4", credentials=self.creds)
#         return True

#     def generate_auth_url(self):
#         flow = Flow.from_client_secrets_file(
#             self.credentials_path, SCOPES, redirect_uri=self.redirect_uri
#         )
#         auth_url, _ = flow.authorization_url(prompt="consent")
#         return auth_url

#     async def handle_oauth_callback(self, request):
#         flow = Flow.from_client_secrets_file(
#             self.credentials_path, SCOPES, redirect_uri=self.redirect_uri
#         )
#         flow.fetch_token(code=request.query["code"])
#         self.creds = flow.credentials
#         with open("token.json", "w") as token:
#             token.write(self.creds.to_json())
#         self.service = build("sheets", "v4", credentials=self.creds)
#         return web.Response(text="Authorization successful! You can close this window.")

#     async def start_oauth_server(self):
#         app = web.Application()
#         app.router.add_get("/oauth2callback", self.handle_oauth_callback)
#         runner = web.AppRunner(app)
#         await runner.setup()
#         site = web.TCPSite(runner, "0.0.0.0", 8080)
#         await site.start()
#         print("OAuth server started on http://0.0.0.0:8080")

#     async def list_workbooks(self):
#         results = self.service.spreadsheets().list().execute()
#         workbooks = results.get("files", [])
#         return workbooks

#     async def list_worksheets(self, spreadsheet_id):
#         sheet_metadata = (
#             self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
#         )
#         sheets = sheet_metadata.get("sheets", [])
#         return [sheet["properties"]["title"] for sheet in sheets]

#     async def get_headers(self, spreadsheet_id, sheet_name):
#         range_name = f"{sheet_name}!1:1"
#         result = (
#             self.service.spreadsheets()
#             .values()
#             .get(spreadsheetId=spreadsheet_id, range=range_name)
#             .execute()
#         )
#         return result.get("values", [[]])[0]

#     async def add_row(self, spreadsheet_id, sheet_name, values):
#         range_name = f"{sheet_name}"
#         body = {"values": [values]}
#         result = (
#             self.service.spreadsheets()
#             .values()
#             .append(
#                 spreadsheetId=spreadsheet_id,
#                 range=range_name,
#                 valueInputOption="USER_ENTERED",
#                 body=body,
#             )
#             .execute()
#         )
#         return result
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
SERVICE_ACCOUNT_FILE = "service-account.json"


class GoogleSheetsModule:
    def __init__(self):
        self.service = None
        self.drive_service = None
        self.current_workbook = None
        self.current_worksheet = None
        self.credentials = None
        self.setup_service()

    def setup_service(self):
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            # Try to initialize both services
            try:
                self.service = build("sheets", "v4", credentials=self.credentials)
                logger.info("Sheets API service initialized successfully")
            except HttpError as e:
                logger.error(f"Failed to initialize Sheets API: {str(e)}")

            try:
                self.drive_service = build("drive", "v3", credentials=self.credentials)
                logger.info("Drive API service initialized successfully")
            except HttpError as e:
                logger.error(f"Failed to initialize Drive API: {str(e)}")

            return True
        except Exception as e:
            logger.error(f"Failed to setup Google services: {str(e)}")
            return False

    async def list_workbooks(self):
        try:
            if not self.drive_service:
                error_msg = (
                    "Drive API service not available. Please ensure the Google Drive API "
                    "is enabled in your Google Cloud Console: "
                    "https://console.cloud.google.com/apis/library/drive.googleapis.com"
                )
                logger.error(error_msg)
                raise Exception(error_msg)

            results = (
                self.drive_service.files()
                .list(
                    q="mimeType='application/vnd.google-apps.spreadsheet'",
                    fields="files(id, name)",
                    pageSize=50,
                )
                .execute()
            )

            files = results.get("files", [])
            logger.info(f"Found {len(files)} workbooks")
            return files

        except HttpError as e:
            if "accessNotConfigured" in str(e):
                error_msg = (
                    "Google Drive API is not enabled. Please visit "
                    "https://console.cloud.google.com/apis/library/drive.googleapis.com "
                    "to enable it and try again in a few minutes."
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            logger.error(f"HTTP error while listing workbooks: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error listing workbooks: {str(e)}")
            raise

    async def list_worksheets(self, spreadsheet_id):
        try:
            if not self.service:
                logger.error("Sheets service not initialized")
                return []

            sheet_metadata = (
                self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            )

            sheets = sheet_metadata.get("sheets", [])
            return [sheet["properties"]["title"] for sheet in sheets]

        except HttpError as e:
            logger.error(f"HTTP error while listing worksheets: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while listing worksheets: {str(e)}")
            return []

    async def get_headers(self, spreadsheet_id, sheet_name):
        try:
            range_name = f"{sheet_name}!1:1"
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            headers = result.get("values", [[]])[0]
            logger.info(f"Retrieved headers: {headers}")
            return headers

        except Exception as e:
            logger.error(f"Error getting headers: {str(e)}")
            return []

    async def add_row(self, spreadsheet_id, sheet_name, values):
        try:
            if not self.service:
                raise Exception("Sheets service not initialized")

            range_name = f"{sheet_name}!A:A"
            body = {"values": [values]}

            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

            logger.info(f"Successfully added row to {sheet_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to add row: {str(e)}")
            raise
