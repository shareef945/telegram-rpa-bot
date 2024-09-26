from config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORGANIZATION_ID
import requests
import logging
import json
import os

logger = logging.getLogger(__name__)


class ZohoInvoicing:
    def __init__(self):
        self.client_id = ZOHO_CLIENT_ID
        self.client_secret = ZOHO_CLIENT_SECRET
        self.redirect_uri = "https://example.com/oauth/callback"
        self.access_token = None
        self.refresh_token = None
        self.organization_id = ZOHO_ORGANIZATION_ID
        self.base_url = "https://www.zohoapis.com/books/v3"
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
        logger.info(f"Saving tokens..")
        tokens = {"access_token": self.access_token}
        if self.refresh_token:
            tokens["refresh_token"] = self.refresh_token
        with open("zoho_tokens.json", "w") as f:
            json.dump(tokens, f)

    def load_tokens(self):
        token_file = "zoho_tokens.json"
        if not os.path.exists(token_file):
            logger.warning(
                f"Token file {token_file} not found. Proceeding without tokens."
            )
            self.access_token = None
            self.refresh_token = None
            return

        try:
            with open(token_file, "r") as f:
                tokens = json.load(f)
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            if self.access_token and self.refresh_token:
                logger.info(
                    f"Loaded tokens: access_token={self.access_token}, refresh_token={self.refresh_token}"
                )
            elif self.access_token:
                logger.info(f"Loaded access token: {self.access_token}")
            else:
                logger.warning("Token file exists but doesn't contain valid tokens.")
        except FileNotFoundError:
            logger.warning(
                f"Token file {token_file} not found. Proceeding without tokens."
            )
            self.access_token = None
            self.refresh_token = None
        except json.JSONDecodeError:
            logger.warning("Token file is empty or invalid. Proceeding without tokens.")
            self.access_token = None
            self.refresh_token = None
        except Exception as e:
            logger.error(f"Unexpected error loading tokens: {str(e)}")
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
            self.refresh_token = tokens.get("refresh_token")  # Use get() method
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
        if not self.tokens_available():
            logger.error("No tokens available.")
            return False
        if not self.access_token:
            logger.info("Access token not available, attempting to refresh.")
            if not await self.refresh_access_token():
                logger.error("Failed to refresh access token.")
                return False
        logger.info("Access token is available and valid.")
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

    async def get_customers(self, **kwargs):
        if not await self.ensure_valid_token():
            logger.error("Failed to ensure valid token.")
            return None

        try:
            base_url = f"{self.base_url}/contacts"
            params = {
                "organization_id": self.organization_id,
            }

            valid_params = [
                "contact_name",
                "company_name",
                "first_name",
                "last_name",
                "address",
                "email",
                "phone",
                "filter_by",
                "search_text",
                "sort_column",
                "zcrm_contact_id",
                "zcrm_account_id",
            ]

            for param in valid_params:
                if param in kwargs:
                    params[param] = kwargs[param]

            variant_params = [
                "contact_name",
                "company_name",
                "first_name",
                "last_name",
                "address",
                "email",
                "phone",
            ]

            for param in variant_params:
                if f"{param}_startswith" in kwargs:
                    params[f"{param}_startswith"] = kwargs[f"{param}_startswith"]
                if f"{param}_contains" in kwargs:
                    params[f"{param}_contains"] = kwargs[f"{param}_contains"]

            headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
            response = requests.get(base_url, headers=headers, params=params)
            logging.info(f"API response: {response}")  # Log the raw API response

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Successfully fetched {len(data.get('contacts', []))} customers"
                )
                return data.get("contacts", [])
            else:
                logger.error(f"Error fetching customers: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching customers: {str(e)}")
            return None

    def tokens_available(self):
        return self.access_token is not None and self.refresh_token is not None
