#!/usr/bin/env python3
"""
Local Testing Script for Aspen Grade Monitor

This script helps test the multi-user functionality locally.
Run this after starting the bot to test various features.
"""

import asyncio
import sys
import os
from database import Database
from bot.scraper import AspenScraper

def test_database():
    """Test database functionality."""
    print("🧪 Testing Database...")

    try:
        # Initialize database
        db = Database()
        print("✅ Database initialized successfully")

        # Test adding a user
        test_telegram_id = 123456789
        test_username = "test_user"
        test_password = "test_password"

        success = db.add_user(
            telegram_id=test_telegram_id,
            aspen_username=test_username,
            aspen_password=test_password
        )

        if success:
            print("✅ User added successfully")
        else:
            print("❌ Failed to add user")
            return False

        # Test getting user
        user = db.get_user(test_telegram_id)
        if user:
            print("✅ User retrieved successfully")
            print(f"   Username: {user['aspen_username']}")
            print(f"   Notification: {user['notification_method']}")
        else:
            print("❌ Failed to retrieve user")
            return False

        # Test getting all users
        users = db.get_all_active_users()
        print(f"✅ Found {len(users)} active users")

        # Clean up test user
        db.delete_user(test_telegram_id)
        print("✅ Test user cleaned up")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_scraper():
    """Test Aspen scraper functionality."""
    print("\n🧪 Testing Aspen Scraper...")

    try:
        # Test scraper initialization
        scraper = AspenScraper()
        print("✅ Scraper initialized successfully")

        # Note: We don't test actual login here as it requires real credentials
        print("ℹ️  Skipping login test (requires real Aspen credentials)")
        print("   To test login, use /register in the bot with real credentials")

        return True

    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def test_environment():
    """Test environment configuration."""
    print("\n🧪 Testing Environment...")

    try:
        import config

        # Check required variables
        if not config.TELEGRAM_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not set")
            return False
        else:
            print("✅ TELEGRAM_BOT_TOKEN is set")

        if config.ENV:
            print(f"ℹ️  Running in production mode (ENV={config.ENV})")
            if not config.WEBHOOK_URL:
                print("⚠️  WEBHOOK_URL not set for production mode")
        else:
            print("ℹ️  Running in local mode (polling)")

        if config.DONATION_URL:
            print(f"✅ DONATION_URL is set: {config.DONATION_URL}")
        else:
            print("ℹ️  DONATION_URL not set (donation command will show generic message)")

        print(f"ℹ️  Timezone: {config.TIMEZONE}")
        print(f"ℹ️  Port: {config.PORT}")

        return True

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n🧪 Testing File Structure...")

    required_files = [
        "main.py",
        "database.py",
        "config.py",
        "requirements.txt",
        "bot/handlers.py",
        "bot/scraper.py",
        "bot/scheduler.py",
        "bot/ptb.py",
        "bot/email_service.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def main():
    """Run all tests."""
    print("🚀 Aspen Grade Monitor - Local Testing")
    print("=" * 50)

    tests = [
        ("File Structure", test_file_structure),
        ("Environment", test_environment),
        ("Database", test_database),
        ("Scraper", test_scraper)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! You're ready to run the bot.")
        print("\n🚀 Next steps:")
        print("1. Run: python main.py")
        print("2. Open Telegram and find your bot")
        print("3. Send /start to begin testing")
        print("4. Send /register to set up your account")
        print("5. Send /grades to test grade fetching")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the bot.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
