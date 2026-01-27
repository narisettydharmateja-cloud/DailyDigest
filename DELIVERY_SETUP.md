# Phase 4: Delivery Setup Guide

## Email Delivery Setup

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or Other)
   - Copy the 16-character app password
3. **Update `.env` file**:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=true
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   ```

### Other Email Providers

**Outlook/Office365**:
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**Yahoo Mail**:
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Send Digest via Email

```bash
# Get the digest ID from list command
dailydigest-digest list

# Send digest via email
dailydigest-deliver email <digest-id> your-recipient@email.com
```

---

## Telegram Bot Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow prompts to name your bot (e.g., "DailyDigest Bot")
4. Copy the **bot token** (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

**Method 1: Using @userinfobot**
1. Search for **@userinfobot** in Telegram
2. Start the bot and it will show your Chat ID

**Method 2: Using @get_id_bot**
1. Search for **@get_id_bot** in Telegram
2. Start the bot to get your Chat ID

**Method 3: Manual**
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the JSON response under `message.chat.id`

### 3. Configure Telegram in `.env`

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_DEFAULT_CHAT_ID=your-chat-id
```

### 4. Send Digest via Telegram

```bash
# Get the digest ID from list command
dailydigest-digest list

# Send digest via Telegram
dailydigest-deliver telegram <digest-id> <chat-id>

# Or use the default chat ID from .env
# (requires code update to use default)
```

---

## Complete Workflow Example

```bash
# 1. Scrape news
dailydigest-scrape run

# 2. Process with AI (embeddings + scoring)
dailydigest-process process

# 3. Generate digest
dailydigest-digest generate --persona genai --min-score 0.7

# 4. Get digest ID
dailydigest-digest list

# 5. Deliver via email
dailydigest-deliver email a196f021-b513-4120-9233-b67eccc6e47b your@email.com

# 6. Or deliver via Telegram
dailydigest-deliver telegram a196f021-b513-4120-9233-b67eccc6e47b 123456789

# 7. Or deliver via both channels
dailydigest-deliver both a196f021-b513-4120-9233-b67eccc6e47b \
  --email your@email.com \
  --chat-id 123456789
```

---

## Automation with Task Scheduler (Windows)

### Create a Daily Digest Task

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Task** (not "Create Basic Task")
3. **General Tab**:
   - Name: "Daily Digest - GenAI News"
   - Description: "Fetch, process, and deliver GenAI news digest"
   - Check "Run whether user is logged on or not"
4. **Triggers Tab**:
   - Click "New"
   - Begin task: "On a schedule"
   - Daily, at 8:00 AM
   - Check "Enabled"
5. **Actions Tab**:
   - Click "New"
   - Action: "Start a program"
   - Program: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
   - Arguments:
     ```powershell
     -File "C:\Users\YourName\Desktop\DailyDigest\scripts\run_daily.ps1"
     ```
6. **Conditions Tab**:
   - Uncheck "Start the task only if the computer is on AC power"
7. Click **OK** and enter your Windows password

### Create PowerShell Script

Create `scripts/run_daily.ps1`:

```powershell
# DailyDigest automation script
Set-Location "C:\Users\YourName\Desktop\DailyDigest"

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Run the pipeline
Write-Host "🔄 Scraping news..."
dailydigest-scrape run

Write-Host "🤖 Processing with AI..."
dailydigest-process process

Write-Host "📝 Generating GenAI digest..."
$digest_output = dailydigest-digest generate --persona genai --min-score 0.7
$digest_id = ($digest_output | Select-String -Pattern '([a-f0-9-]{36})').Matches.Value

if ($digest_id) {
    Write-Host "📧 Delivering digest $digest_id..."
    dailydigest-deliver email $digest_id "your@email.com"
    Write-Host "✅ Done!"
} else {
    Write-Host "❌ No digest generated"
}
```

Make it executable and test:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\scripts\run_daily.ps1
```

---

## Troubleshooting

### Email Issues

**"Authentication failed"**
- For Gmail: Make sure you're using an App Password, not your regular password
- Check that SMTP credentials are correct in `.env`

**"Connection timeout"**
- Verify SMTP_HOST and SMTP_PORT are correct
- Check firewall/antivirus isn't blocking port 587
- Try SMTP_PORT=465 with SMTP_USE_TLS=false (SSL instead of TLS)

### Telegram Issues

**"Unauthorized"**
- Verify bot token is correct in `.env`
- Make sure you've started your bot (send `/start` in Telegram)

**"Chat not found"**
- Verify chat ID is correct
- Send a message to your bot first
- Chat ID should be a number, not a username

**Message too long**
- The service automatically splits long messages
- If still failing, reduce the number of articles in digest

---

## Next Steps

Once delivery is working, you can:

1. **Schedule multiple personas**:
   - Create separate tasks for GenAI and Product digests
   - Run at different times or with different frequencies

2. **Add more delivery channels**:
   - Discord webhooks
   - Slack integration
   - Push notifications

3. **Enhance automation**:
   - Only send digest if there are new high-quality articles
   - Add retry logic for failed deliveries
   - Log delivery status to database

4. **Monitoring & Observability**:
   - Track delivery success/failure rates
   - Alert on pipeline failures
   - Monitor article quality trends
