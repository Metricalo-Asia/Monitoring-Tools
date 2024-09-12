import os

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to send a message with an attachment to a Telegram group
def send_telegram_notification(file_path, message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    with open(file_path, 'rb') as file:
        files = {'document': file}
        data = {'chat_id': chat_id, 'caption': message}

        response = requests.post(url, data=data, files=files)

    if response.status_code != 200:
        print(f"Error sending message: {response.text}")
    else:
        print("Notification sent successfully!")


def list_chat_ids():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)

    if response.status_code == 200:
        updates = response.json()
        print(updates)
        # Check if the response is OK
        if updates.get("ok"):
            chat_ids = set()  # To store unique chat IDs
            for result in updates.get("result", []):
                message = result.get("message")
                if message:
                    chat = message.get("chat")
                    chat_id = chat.get("id")
                    chat_title = chat.get("title", "Private Chat")
                    chat_type = chat.get("type", "private")

                    # Store the chat id with its title or "Private Chat" for individual users
                    chat_ids.add((chat_id, chat_title, chat_type))

            # List all unique chat IDs
            if chat_ids:
                print("List of chat IDs:")
                for chat_id, chat_title, chat_type in chat_ids:
                    print(f"Chat ID: {chat_id}, Title: {chat_title}, Type: {chat_type}")
            else:
                print("No chat IDs found.")
        else:
            print("Error fetching updates from Telegram API.")
    else:
        print(f"Failed to connect to Telegram API. Status code: {response.status_code}")