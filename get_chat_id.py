"""Quick script to get your Telegram Chat ID"""
import httpx
import time

BOT_TOKEN = "7988195313:AAEzuAUJIFfNkaaWXppRd1YEfByS-DqXsgA"

print("=" * 60)
print("TELEGRAM CHAT ID FINDER")
print("=" * 60)
print()
print("📱 Instructions:")
print("1. Open Telegram on your phone/desktop")
print("2. Find your bot and click START (or send /start)")
print("3. Send ANY message to your bot (e.g., 'hello')")
print("4. Come back here and press ENTER")
print()
input("Press ENTER after you've sent a message to your bot...")
print()
print("🔍 Checking for messages...")

response = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates")
data = response.json()

if data['ok'] and data['result']:
    for update in data['result']:
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            username = update['message']['chat'].get('username', 'N/A')
            first_name = update['message']['chat'].get('first_name', 'N/A')
            
            print("✅ Found your chat!")
            print(f"   Chat ID: {chat_id}")
            print(f"   Name: {first_name}")
            print(f"   Username: @{username}")
            print()
            print(f"👉 Update your .env file with:")
            print(f"   TELEGRAM_DEFAULT_CHAT_ID={chat_id}")
            break
else:
    print("❌ No messages found!")
    print("   Make sure you:")
    print("   1. Started the bot (click START button)")
    print("   2. Sent at least one message")
    print("   3. Are using the correct bot")
