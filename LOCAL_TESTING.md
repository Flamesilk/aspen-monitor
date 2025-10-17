# Local Testing Guide for Aspen Grade Monitor

This guide explains how to test the multi-user Aspen Grade Monitor locally before deploying to Railway.

## 🚀 Quick Start

### 1. **Environment Setup**

Create a `.env` file in your project root:

```bash
# Copy the example file
cp env.example .env
```

Edit `.env` with your values:

```bash
# Required for local testing
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Local development settings
ENV=  # Leave empty for local development
# Don't set WEBHOOK_URL for local testing

# Optional
DONATION_URL=https://ko-fi.com/herrkaeferdev
TIMEZONE=America/Chicago
PORT=8000
```

### 2. **Install Dependencies**

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. **Database Setup**

For local testing, the SQLite database will be created automatically in the project directory:

```bash
# The database will be created at: ./users.db
# Encryption key will be created at: ./encryption.key
```

**Note**: In production (Railway), these files are stored in the `/data` volume.

### 4. **Run the Bot**

```bash
# Start the bot in local mode
python main.py
```

You should see output like:
```
INFO - Running in local mode
INFO - Scheduled daily grade check for 3:00 PM America/Chicago
```

## 🧪 Testing Scenarios

### **Test 1: Basic Bot Functionality**

1. **Start the bot** (as above)
2. **Open Telegram** and find your bot
3. **Send `/start`** - Should show welcome message
4. **Send `/help`** - Should show all available commands

### **Test 2: User Registration**

1. **Send `/register`** to start registration
2. **Enter your Aspen username** when prompted
3. **Enter your Aspen password** when prompted
4. **Verify registration success** - Should show "Registration Complete!"

### **Test 3: Grade Fetching**

1. **Send `/grades`** - Should fetch and display your grades
2. **Check the output** - Should show formatted grade information
3. **Verify it works** with your actual Aspen credentials

### **Test 4: Account Management**

1. **Send `/status`** - Should show your account information
2. **Send `/settings`** - Should show settings options
3. **Test credential update** - Use the "Update Credentials" button
4. **Test account deletion** - Use the "Delete Account" button

### **Test 5: Donation Command**

1. **Send `/donate`** - Should show donation information
2. **Verify the link** works (if DONATION_URL is set)

## 🔧 Development Tips

### **Database Inspection**

You can inspect the SQLite database directly:

```bash
# Install sqlite3 if not available
# On macOS: brew install sqlite3
# On Ubuntu: sudo apt-get install sqlite3

# Open the database
sqlite3 users.db

# View users table
.tables
.schema users
SELECT * FROM users;

# Exit
.quit
```

### **Logging and Debugging**

The bot logs important information. Watch for:

```bash
# User registration
INFO - User 123456789 added/updated successfully

# Grade fetching
INFO - Processing user 123456789 (username)

# Errors
ERROR - Error fetching grades for user 123456789: [error details]
```

### **Testing Multiple Users**

To test multi-user functionality:

1. **Register multiple accounts** using different Telegram accounts
2. **Check the database** to see all registered users
3. **Test scheduled updates** (see below)

## ⏰ Testing Scheduled Updates

### **Manual Testing**

You can manually trigger the scheduled update:

```python
# Create a test script: test_scheduler.py
import asyncio
from bot.scheduler import fetch_and_notify_all_users
from bot.ptb import ptb

async def test_scheduled_update():
    # Initialize the bot
    async with ptb:
        # Create a mock context
        class MockContext:
            def __init__(self):
                self.bot = ptb.bot

        context = MockContext()
        await fetch_and_notify_all_users(context)

# Run the test
if __name__ == "__main__":
    asyncio.run(test_scheduled_update())
```

Run it:
```bash
python test_scheduler.py
```

### **Scheduled Testing**

The bot runs scheduled updates daily at 3 PM. To test this:

1. **Register a test user**
2. **Wait for 3 PM** (or modify the time in `bot/scheduler.py`)
3. **Check if you receive** the scheduled grade update

## 🐛 Common Issues and Solutions

### **Issue 1: "Database not found"**

**Solution**: The database is created automatically. If you see this error, check file permissions.

### **Issue 2: "Encryption key not found"**

**Solution**: The encryption key is created automatically. If you see this error, check file permissions.

### **Issue 3: "Telegram bot not responding"**

**Solutions**:
- Check your `TELEGRAM_BOT_TOKEN` is correct
- Ensure the bot is running (`python main.py`)
- Check your internet connection
- Verify the bot is not already running elsewhere

### **Issue 4: "Aspen login failed"**

**Solutions**:
- Verify your Aspen credentials are correct
- Check if Aspen is accessible from your network
- Try logging into Aspen manually first

### **Issue 5: "No users found"**

**Solution**: Register a user first with `/register` command.

## 📊 Testing Checklist

### **Basic Functionality**
- [ ] Bot starts without errors
- [ ] `/start` command works
- [ ] `/help` command works
- [ ] `/donate` command works (if URL set)

### **User Management**
- [ ] `/register` works end-to-end
- [ ] `/grades` fetches actual grades
- [ ] `/status` shows user information
- [ ] `/settings` shows management options
- [ ] Account deletion works

### **Database Operations**
- [ ] User registration creates database entry
- [ ] Credentials are encrypted
- [ ] User data persists between restarts
- [ ] Multiple users can be registered

### **Error Handling**
- [ ] Invalid credentials show appropriate error
- [ ] Unregistered users get helpful messages
- [ ] Network errors are handled gracefully
- [ ] Database errors are logged

## 🚀 Production Deployment

Once local testing is complete:

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add multi-user support"
   git push origin main
   ```

2. **Deploy to Railway**:
   - Railway will automatically deploy
   - Add a Volume named "data" mounted at "/data"
   - Set environment variables in Railway dashboard

3. **Test production**:
   - Use the production webhook URL
   - Test with real users
   - Monitor logs for any issues

## 💡 Pro Tips

### **Development Workflow**
1. **Test locally first** - Always test changes locally
2. **Use git branches** - Create feature branches for new features
3. **Test edge cases** - Try invalid inputs, network failures, etc.
4. **Monitor logs** - Watch for errors and warnings

### **Database Management**
- **Backup regularly** - Copy `users.db` and `encryption.key`
- **Test migrations** - If you change the database schema
- **Clean test data** - Delete test users before production

### **Security Testing**
- **Test encryption** - Verify credentials are encrypted
- **Test access control** - Ensure users can only access their own data
- **Test input validation** - Try malicious inputs

## 🎯 Next Steps

After successful local testing:

1. **Deploy to Railway** with volume configuration
2. **Set up monitoring** for production logs
3. **Test with real users** in a controlled environment
4. **Monitor performance** and user feedback

Happy testing! 🚀
