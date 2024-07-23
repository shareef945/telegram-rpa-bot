# Telegram File Downloader Bot

This is a simple Telegram bot written in Python that listens for documents sent to it and downloads them to a specified directory.

## Features

- Downloads files sent to the bot.
- Skips already processed messages to avoid duplicates.
- Replies to the sender with the download progress and confirmation.
- Handles commands and document messages.

## Requirements

- Python 3.9 or higher.
- Telethon library.
- A Telegram API ID, API hash, and a bot token.

## Installation

1. Clone this repository or download the source code.
2. Install Python 3.9 or higher if not already installed.
3. Create a virtual environment (recommended).

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
3. Create a `.env` file in the root directory and add your `API_ID`, `API_HASH`, and `BOT_TOKEN`.

    ```dotenv
    API_ID=your_api_id
    API_HASH=your_api_hash
    BOT_TOKEN=your_bot_token
    ```

4. (Optional) Modify the `DOWNLOAD_DIR` in `bot.py` if you want to change the download directory.

## Usage

Run the bot with:

```sh
python bot.py