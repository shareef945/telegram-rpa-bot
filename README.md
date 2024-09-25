# Multi-Purpose Telegram Bot

This is a versatile Telegram bot written in Python that offers various functionalities including file downloading, Zoho Books integration, and custom API interactions.

## Features

- File Downloads: Downloads files sent to the bot and organizes them based on content type (TV shows, movies).
- Zoho Books Integration: Allows authorized users to interact with Zoho Books (create invoices, list customers).
- Role-based Access Control: Implements user roles (guest, user, admin) to manage command access.
- Custom API Interactions: (Add description of your custom APIs)
- Message Deduplication: Skips already processed messages to avoid duplicates.
- Progress Tracking: Replies to the sender with download progress and confirmation.

## Requirements

- Python 3.9 or higher
- Telethon library
- python-magic library
- python-dotenv
- A Telegram API ID, API hash, and a bot token
- Zoho Books API credentials (for Zoho integration)

## Installation

1. Clone this repository or download the source code.
2. Install Python 3.9 or higher if not already installed.
3. Create a virtual environment (recommended):

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. Obtain your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Create a new bot with the Telegram BotFather and get the `BOT_TOKEN`.
3. If using Zoho integration, obtain your Zoho Books API credentials.
4. Create a `.env` file in the root directory and add your credentials:

    ```dotenv
    API_ID=your_api_id
    API_HASH=your_api_hash
    BOT_TOKEN=your_bot_token
    ZOHO_CLIENT_ID=your_zoho_client_id
    ZOHO_CLIENT_SECRET=your_zoho_client_secret
    ZOHO_ORGANIZATION_ID=your_zoho_organization_id
    USER_ROLES=user_id1:role1,user_id2:role2
    ```

5. Modify the `DOWNLOAD_DIR` in `config.py` if you want to change the download directory.

## Usage

Run the bot with:

```sh
python src/main.py
```

Or using Docker:

```sh
docker-compose up
```

## Available Commands

- `/start`: Start the bot and see an overview of its capabilities
- `/help`: Show all available commands
- `/zoho_auth`: Authorize the bot to use Zoho Books (admin only)
- `/create_invoice`: Create a new invoice in Zoho Books (admin only)
- `/list_customers`: List customers from Zoho Books (admin only)
- `/my_role`: Show your current role

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.