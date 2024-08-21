from config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET
import requests
import logging
import json

logger = logging.getLogger(__name__)


class ZohoInvoicing:
    def __init__(self):
        self.client_id = ZOHO_CLIENT_ID
        self.client_secret = ZOHO_CLIENT_SECRET
        self.redirect_uri = "https://example.com/oauth/callback"
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://books.zoho.com/api/v3"
        self.load_tokens()

    def generate_auth_url(self):
        return (
            f"https://accounts.zoho.com/oauth/v2/auth?"
            f"scope=ZohoBooks.fullaccess.all&"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"access_type=offline"
        )

    def save_tokens(self):
        logger.info(
            f"Saving tokens: access_token={self.access_token}, refresh_token={self.refresh_token}"
        )
        with open("zoho_tokens.json", "w") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                },
                f,
            )

    def load_tokens(self):
        try:
            with open("zoho_tokens.json", "r") as f:
                tokens = json.load(f)
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            if self.access_token and self.refresh_token:
                logger.info(
                    f"Loaded tokens: access_token={self.access_token}, refresh_token={self.refresh_token}"
                )
            else:
                logger.warning("Token file exists but doesn't contain valid tokens.")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Token file not found or empty. Proceeding without tokens.")
            self.access_token = None
            self.refresh_token = None

    async def get_tokens(self, authorization_code):
        url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "code": authorization_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            self.save_tokens()
            return True
        else:
            logger.error(f"Failed to get tokens: {response.text}")
            return False

    async def refresh_access_token(self):
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False

        url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            self.save_tokens()
            return True
        else:
            logger.error(f"Failed to refresh access token: {response.text}")
            return False

    async def ensure_valid_token(self):
        if not self.access_token:
            return await self.refresh_access_token()
        return True

    async def create_invoice(self, customer_id, items):
        if not await self.ensure_valid_token():
            return None

        try:
            url = f"{self.base_url}/invoices"
            headers = {
                "Authorization": f"Zoho-oauthtoken {self.access_token}",
                "Content-Type": "application/json",
            }
            data = {"customer_id": customer_id, "line_items": items}
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Error creating invoice: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return None

    async def get_customers(self):
        if not await self.ensure_valid_token():
            return None

        try:
            url = f"{self.base_url}/contacts?contact_type=customer"
            headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("contacts", [])
            else:
                logger.error(f"Error fetching customers: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching customers: {str(e)}")
            return None
