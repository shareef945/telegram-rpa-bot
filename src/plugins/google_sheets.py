from typing import List
from modules.google_sheets import GoogleSheetsModule
import logging
from functools import partial
import asyncio

logger = logging.getLogger(__name__)


class EnhancedGoogleSheetsModule(GoogleSheetsModule):
    async def get_values(self, workbook_id: str, range_name: str) -> List[List[str]]:
        """Fetch values from a specific range"""
        try:
            # Create the request
            request = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=workbook_id, range=range_name)
            )
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, request.execute)
            return result.get("values", [])
        except Exception as e:
            logger.error(f"Error fetching values: {str(e)}")
            raise

    async def append_sparse_row(self, workbook_id, worksheet_name, values_dict):
        """
        Append a row with values only in specific columns, preserving formulas in other columns.

        Args:
            workbook_id (str): The ID of the workbook
            worksheet_name (str): The name of the worksheet
            values_dict (dict): Dictionary mapping column indices to values
        """
        try:
            # Get the worksheet
            worksheet = await self.get_worksheet(workbook_id, worksheet_name)

            # Create the request body
            request_body = {"values": [[""]]}  # Start with an empty row

            # Create a range that specifies just the columns we want to update
            ranges = []
            for col_index, value in values_dict.items():
                col_letter = chr(
                    65 + col_index
                )  # Convert number to letter (0=A, 1=B, etc.)
                next_row = len(worksheet.get("values", [])) + 1
                cell_range = f"{worksheet_name}!{col_letter}{next_row}"

                # Update the specific cell
                await self.service.spreadsheets().values().update(
                    spreadsheetId=workbook_id,
                    range=cell_range,
                    valueInputOption="USER_ENTERED",
                    body={"values": [[value]]},
                ).execute()

            return True

        except Exception as e:
            logger.error(f"Error appending sparse row: {str(e)}")
            raise

    async def append_row(
        self, workbook_id: str, worksheet_name: str, values: List[str]
    ):
        """Append a row to a specific worksheet"""
        try:
            body = {"values": [values]}
            # Create the request
            request = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=workbook_id,
                    range=f"{worksheet_name}!A1",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
            )
            # Execute in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, request.execute)
            return result
        except Exception as e:
            logger.error(f"Error appending row: {str(e)}")
            raise

    async def calculate_days_late(self, product_id: str) -> int:
        """Calculate days late for a product"""
        # Implement your days late calculation logic here
        return 0  # Placeholder return


def setup():
    return EnhancedGoogleSheetsModule()
