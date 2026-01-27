import httpx

r = httpx.get('https://api.telegram.org/bot7988195313:AAEzuAUJIFfNkaaWXppRd1YEfByS-DqXsgA/getUpdates')
data = r.json()

if data['result']:
    for update in data['result']:
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            print(f"✅ Found Chat ID: {chat_id}")
else:
    print("❌ No messages found. Please send a message to @dharma_teja_dailydigest_bot")
