from pymongo import MongoClient
import config
from typing import Any, List, Optional, Tuple, Dict
from telegram import Update
from datetime import datetime
import logging
import pytz

logger = logging.getLogger(__name__)

class MongoService:

    def __init__(self, update: Optional[Update] = None) -> None:
        client = MongoClient(config.MONGODB_URI)
        db = client[config.MONGODB_NAME]
        self.users = db.users
        self.habits = db.habits


    def create_user(self, update: Update) -> None:
        user = update.effective_user

        # Store user info in MongoDB
        self.users.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "language_code": user.language_code,
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow(),
                    "timezone": "UTC"  # Default timezone
                }
            },
            upsert=True
        )

    def get_user_timezone(self, update: Update) -> str:
        """Get user's timezone."""
        user = update.effective_user
        user_data = self.users.find_one({"user_id": user.id})
        return user_data.get("timezone", "UTC") if user_data else "UTC"

    def set_user_timezone(self, update: Update, timezone: str) -> Tuple[bool, str]:
        """Set user's timezone."""
        try:
            # Validate timezone
            if timezone not in pytz.all_timezones:
                return False, "Invalid timezone"

            user = update.effective_user
            self.users.update_one(
                {"user_id": user.id},
                {"$set": {"timezone": timezone}}
            )
            return True, f"Timezone set to {timezone}"
        except Exception as e:
            logger.error(f"Error setting timezone for user {user.id}: {e}")
            return False, "Failed to set timezone"

    def add_habit(self, update: Update, habit_name: str, icon: str = "📌") -> Tuple[bool, str]:
        user = update.effective_user

        # Check if habit already exists
        existing = self.habits.find_one({
            "user_id": user.id,
            "name": habit_name
        })

        if existing:
            return False, "You're already tracking this habit"

        # Create new habit
        self.habits.insert_one({
            "user_id": user.id,
            "name": habit_name,
            "icon": icon,
            "created_at": datetime.utcnow(),
            "check_ins": []
        })
        return True, f"Started tracking habit: {habit_name}"


    def get_user_habits(self, update: Update) -> List[Dict[str, Any]]:
        try:
            user = update.effective_user
            # Convert cursor to list using list() for pymongo
            habits = list(self.habits.find({"user_id": user.id}))
            logger.debug(f"Found {len(habits)} habits for user {user.id}")
            return habits
        except Exception as e:
            logger.error(f"Error getting habits for user {user.id}: {e}")
            return []


    def check_in_habit(self, update: Update, habit_name: str, count: int = 1) -> Tuple[bool, str]:
        """Record a check-in for a habit."""
        try:
            user = update.effective_user
            user_tz = pytz.timezone(self.get_user_timezone(update))
            date = datetime.now(user_tz)

            # Find the habit
            habit = self.habits.find_one({
                "user_id": user.id,
                "name": habit_name
            })

            if not habit:
                return False, "Habit not found."

            # For negative adjustments, check current count and adjust if needed
            if count < 0:
                today_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

                today_checkin = next(
                    (checkin for checkin in habit['check_ins']
                    if today_start.replace(tzinfo=None) <= checkin['date'].replace(tzinfo=None) <= today_end.replace(tzinfo=None)),
                    None
                )

                if not today_checkin:
                    logger.debug(f"No check-in found today for habit '{habit_name}'")
                    return False, "No check-ins today to adjust"

                current_count = today_checkin['count']
                logger.debug(f"Current count for today: {current_count}, attempting to adjust by {count}")

                if current_count + count < 0:
                    # Instead of failing, set count to bring total to 0
                    count = -current_count
                    logger.debug(f"Adjusted count to {count} to avoid negative total")

            # Update check-in directly in MongoDB
            today_query = {
                "_id": habit["_id"],
                "check_ins": {
                    "$elemMatch": {
                        "date": {
                            "$gte": date.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None),
                            "$lt": date.replace(hour=23, minute=59, second=59, microsecond=999999).replace(tzinfo=None)
                        }
                    }
                }
            }

            result = self.habits.update_one(
                today_query,
                {"$inc": {"check_ins.$.count": count}}
            )

            logger.debug(f"Update result: matched={result.matched_count}, modified={result.modified_count}")

            if result.modified_count == 0:
                # Only allow positive counts for new check-ins
                if count <= 0:
                    return False, "Cannot create new check-in with zero or negative count"

                # No existing check-in found, create new one
                self.habits.update_one(
                    {"_id": habit["_id"]},
                    {
                        "$push": {
                            "check_ins": {
                                "date": date.replace(tzinfo=None),
                                "count": count
                            }
                        }
                    }
                )
                logger.info(f"Added new check-in for habit '{habit_name}' on {date.date()}")
            else:
                logger.info(f"Updated check-in for habit '{habit_name}' on {date.date()}")

            return True, "Check-in successful!"

        except Exception as e:
            logger.error(f"Error checking in habit '{habit_name}' for user {user.id}: {e}")
            return False, "Failed to record check-in. Please try again."


    def get_habit_data(self, update: Update, habit_name: str) -> Dict[str, Any]:
        user = update.effective_user
        habit = self.habits.find_one({
            "user_id": user.id,
            "name": habit_name
        })
        return habit

    def delete_habit(self, update: Update, habit_name: str) -> Tuple[bool, str]:
        """Delete a habit for a user."""
        try:
            user = update.effective_user
            result = self.habits.delete_one({
                "user_id": user.id,
                "name": habit_name
            })

            if result.deleted_count > 0:
                return True, f"Successfully deleted habit: {habit_name}"
            else:
                return False, "Habit not found"
        except Exception as e:
            logger.error(f"Error deleting habit '{habit_name}' for user {user.id}: {e}")
            return False, "Failed to delete habit. Please try again."
