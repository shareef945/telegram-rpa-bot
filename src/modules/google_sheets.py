from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
from aiohttp import web
import asyncio

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsModule:
    def __init__(self):
        self.creds = None
        self.service = None
        self.credentials_path = "/app/credentials.json"
        self.redirect_uri = "http://192.168.100.79:8080/oauth2callback"

    def load_credentials(self):
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                return False

            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        self.service = build("sheets", "v4", credentials=self.creds)
        return True

    def generate_auth_url(self):
        flow = Flow.from_client_secrets_file(
            self.credentials_path, SCOPES, redirect_uri=self.redirect_uri
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        return auth_url

    async def handle_oauth_callback(self, request):
        flow = Flow.from_client_secrets_file(
            self.credentials_path, SCOPES, redirect_uri=self.redirect_uri
        )
        flow.fetch_token(code=request.query["code"])
        self.creds = flow.credentials
        with open("token.json", "w") as token:
            token.write(self.creds.to_json())
        self.service = build("sheets", "v4", credentials=self.creds)
        return web.Response(text="Authorization successful! You can close this window.")

    async def start_oauth_server(self):
        app = web.Application()
        app.router.add_get("/oauth2callback", self.handle_oauth_callback)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
        print("OAuth server started on http://0.0.0.0:8080")

    async def list_workbooks(self):
        results = self.service.spreadsheets().list().execute()
        workbooks = results.get("files", [])
        return workbooks

    async def list_worksheets(self, spreadsheet_id):
        sheet_metadata = (
            self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", [])
        return [sheet["properties"]["title"] for sheet in sheets]

    async def get_headers(self, spreadsheet_id, sheet_name):
        range_name = f"{sheet_name}!1:1"
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [[]])[0]

    async def add_row(self, spreadsheet_id, sheet_name, values):
        range_name = f"{sheet_name}"
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
        return result
