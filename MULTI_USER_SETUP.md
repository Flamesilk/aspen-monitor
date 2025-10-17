# Multi-User Aspen Grade Monitor Setup

This document explains how to set up and deploy the multi-user version of the Aspen Grade Monitor.

## 🚀 New Features

### Multi-User Support
- ✅ **User Registration**: Users can register with their own Aspen credentials
- ✅ **Secure Storage**: Credentials are encrypted and stored in SQLite database
- ✅ **Telegram Notifications**: All users receive notifications via Telegram
- ✅ **Account Management**: Users can update credentials and manage settings
- ✅ **Scheduled Updates**: Daily grade checks for all registered users
- ✅ **Donation Support**: Built-in donation command to support development

### New Commands
- `/register` - Set up your Aspen account
- `/grades` - Check your current grades
- `/settings` - Manage your account settings
- `/status` - Check your account status
- `/donate` - Support the developer
- `/help` - Get help and instructions

## 🛠️ Setup Instructions

### 1. Railway Volume Configuration

The app now uses SQLite with Railway Volumes for data persistence:

1. **Add Volume to Railway Project**:
   - Go to your Railway project dashboard
   - Click "Add Service" → "Volume"
   - Name: `data`
   - Mount Path: `/data`

2. **Alternative: Use Railway CLI**:
   ```bash
   railway volume create data
   railway volume mount data /data
   ```

### 2. Environment Variables

Add these new environment variables to your Railway project:

#### Required Variables:
```bash
# Existing variables (keep these)
TELEGRAM_BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://your-app.railway.app/api/webhook
ENV=production

# Optional donation support
DONATION_URL=https://ko-fi.com/herrkaeferdev
```

### 3. Deploy to Railway

1. **Push your changes**:
   ```bash
   git add .
   git commit -m "Add multi-user support"
   git push origin main
   ```

2. **Railway will automatically deploy** with the new volume configuration

### 4. Test the Bot

1. **Start a conversation** with your bot
2. **Use `/register`** to set up your account
3. **Test `/grades`** to fetch your grades
4. **Use `/settings`** to manage your account

## 📊 Database Schema

The SQLite database stores user data securely:

### Users Table:
```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    aspen_username TEXT,           -- Encrypted
    aspen_password TEXT,           -- Encrypted
    notification_method TEXT,      -- 'telegram' (only option)
    is_active BOOLEAN,            -- Account status
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);
```

### Security Features:
- ✅ **Encrypted Credentials**: All Aspen credentials are encrypted using Fernet
- ✅ **Secure Key Storage**: Encryption key stored in Railway volume
- ✅ **No Plain Text**: Passwords never stored in plain text

## 🔧 User Flow

### New User Registration:
1. User sends `/register`
2. Bot asks for Aspen username
3. Bot asks for Aspen password
4. Account created with Telegram notifications
5. Ready to use immediately

### Existing User:
1. User sends `/grades` → Bot fetches grades using their credentials
2. User sends `/settings` → Bot shows account management options
3. User can update credentials, delete account, etc.

### Daily Scheduled Updates:
1. Bot runs daily at 3 PM (configurable)
2. Fetches grades for all active users
3. Sends notifications via Telegram

## 💰 Cost Analysis

### SQLite + Railway Volume:
- **Volume Storage**: $0.15/GB/month
- **Estimated Usage**: < 1GB for 1000+ users
- **Monthly Cost**: ~$0.15

### vs MongoDB Options:
- **MongoDB Atlas M0**: Free (512MB limit)
- **MongoDB Atlas M2**: $9/month
- **MongoDB on Railway**: $10-31/month

**SQLite is 60x cheaper than MongoDB!**

## 🚨 Important Notes

### 1. Remove Old Authorization
The old `AUTHORIZED_CHAT_IDS` system is no longer used. All users can register.

### 2. Backup Strategy
- Database is automatically backed up in `/data/` volume
- Railway volumes persist across deployments
- Consider setting up automated backups

### 3. Rate Limiting
- Aspen may have rate limits for multiple users
- Consider adding delays between user requests
- Monitor for rate limit errors

### 4. Error Handling
- Users with invalid credentials will get error messages
- Failed logins are logged but don't crash the system
- Users can update credentials via `/settings`

## 🔍 Monitoring

### Logs to Watch:
- User registration attempts
- Grade fetch successes/failures
- Email delivery status
- Database operations

### Key Metrics:
- Number of registered users
- Daily active users
- Grade fetch success rate
- Email delivery rate

## 🆘 Troubleshooting

### Common Issues:

1. **Database not persisting**:
   - Check Railway volume is mounted at `/data`
   - Verify volume is attached to your service

2. **Email not working**:
   - Check SMTP credentials
   - Verify Gmail app password
   - Check firewall/security settings

3. **User can't register**:
   - Check database permissions
   - Verify encryption key generation
   - Check logs for errors

4. **Grades not fetching**:
   - Verify Aspen credentials
   - Check for rate limiting
   - Monitor scraper logs

## 🎯 Next Steps

### Potential Enhancements:
1. **User Analytics**: Track usage patterns
2. **Grade Change Alerts**: Notify on grade changes
3. **Assignment Reminders**: Due date notifications
4. **Grade Trends**: Historical grade tracking
5. **Admin Panel**: User management interface

### Scaling Considerations:
1. **Database Optimization**: Index frequently queried fields
2. **Rate Limiting**: Implement user-level rate limits
3. **Caching**: Cache grade data to reduce Aspen requests
4. **Monitoring**: Set up alerts for failures

## 📞 Support

If you encounter issues:
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Test database connectivity
4. Check volume mount status

The multi-user system is now ready for production use! 🎉
