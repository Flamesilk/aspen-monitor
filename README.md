# Aspen Monitor: A Telegram Bot for Grade and Assignment Tracking

This repository hosts a lightweight Telegram bot for quickly checking grades and assignments from [Aspen CPS](https://aspen.cps.edu), the student information system used by **Chicago Public Schools (CPS)**.

### Key Features:
- **Fast grade queries**: Get your grades or assignments instantly via Telegram.
- **Daily updates**: Configure the bot to push daily grade summaries.
- **Multi-user support**: Each user registers with their own Aspen credentials.
- **Secure credential storage**: User credentials are encrypted and stored safely.

The bot supports multiple users, each with their own Aspen credentials. It can be deployed on Railway or Vercel.

## Features
- Real-time grade and assignment updates via Telegram.
- Multi-user support with individual credential management.
- Secure credential encryption and storage.
- Easy deployment on Railway or Vercel.

## Setup Instructions

### Prerequisites
1. Create a Telegram bot and get its token (obtained from [BotFather](https://core.telegram.org/bots#botfather)).
2. Aspen CPS credentials (username and password) - each user will register their own.

### Deployment

The following process uses Railway as example.

1. Fork this repo and link it to your new project on the deployment platform.

2. Set up environment variables

```env
ENV=production
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-app.railway.app/api/webhook
```

**Note**: No global Aspen credentials needed - each user will register their own credentials through the bot.

3. Webhook configuration

The webhook is automatically configured when your bot starts up! No manual setup required.

**How it works:**
- When `ENV=production` and `WEBHOOK_URL` are set, the bot automatically registers the webhook
- Telegram will send updates to your bot's `/api/webhook` endpoint
- The bot processes updates and responds automatically

**Optional: Check webhook status**

To verify the webhook is working:

```bash
curl "https://api.telegram.org/bot<your_bot_token>/getWebhookInfo" | python3 -m json.tool
```

4. User Registration

After deployment, users can start using the bot:

1. **Start the bot**: Send `/start` to your Telegram bot
2. **Register credentials**: Use `/register` to set up your Aspen username and password
3. **Get grades**: Use `/grades` to fetch your current grades
4. **Set notifications**: Use `/settings` to configure daily grade updates

**Security**: Each user's credentials are encrypted and stored securely. No shared credentials are used.

Remember to re-deploy after you have modified the environment variables.
