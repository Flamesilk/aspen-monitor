# A simple Telegram bot for checking grades and assignments from [Aspen CPS](https://aspen.cps.edu)

It's for private use for now. Aspen credentials are set as environment variables.

## Deployment

It's currently deployed on Railway.

To deploy on Vercel, need to set environment variables:

```
ENV=prod
SERVERLESS=true
```

## Webhook

### Set webhook

After deployment, set webhook to the deployed URL.

```bash
curl "https://api.telegram.org/bot<token>/setWebhook?url=https://aspen-monitor.up.railway.app/api/webhook"
```

### Get webhook info

```bash
curl "https://api.telegram.org/bot<token>/getWebhookInfo" | python3 -m json.tool
```

### Delete webhook

```bash
curl "https://api.telegram.org/bot<token>/deleteWebhook"
```
