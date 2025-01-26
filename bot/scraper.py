import requests
from bs4 import BeautifulSoup
import time
import json

from config import ASPEN_USERNAME, ASPEN_PASSWORD

class AspenScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://aspen.cps.edu/aspen"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-store,no-cache',
            'Pragma': 'no-cache'
        }
        self.student_id = None

    @staticmethod
    def format_score(score_text, percentage=None):
        """Helper function to format score with emoji indicators"""
        try:
            if percentage is not None:
                score = float(percentage)
                if score >= 90:
                    return f'👏 {score_text}'  # Green checkmark for good scores
                elif score >= 80:
                    return f'⚠️ {score_text}'  # Warning symbol for scores between 80 and 89
                else:
                    return f'‼️ {score_text}'  # Red cross for scores below 80
        except (ValueError, TypeError):
            pass
        return score_text

    def format_grades_message(self, class_list, title="📚 Current Grades"):
        """Format grades and assignments into a consistent message format"""
        messages = []
        current_message = title

        if hasattr(self, 'student_name') and self.student_name:
            current_message += f" for {self.student_name}"
        current_message += ":\n\n"

        has_content = False

        for class_info in class_list:
            course_name = class_info.get('courseName', '')
            grade = class_info.get('sectionTermAverage', '')
            percentage = class_info.get('percentageValue')
            teacher = class_info.get('teacherName', '')

            # Skip if no grade and no assignments
            if not grade and not class_info.get('percentageValue'):
                continue

            has_content = True
            class_message = f"📘 <b>{course_name}</b>\n"
            class_message += "------------------------------\n"
            class_message += f"Grade: {self.format_score(grade or 'No grade', percentage)}\n"
            class_message += f"Teacher: {teacher}\n"

            # Get assignments if available
            if class_info.get('percentageValue'):
                schedule_oid = class_info.get('studentScheduleOid')
                if schedule_oid:
                    assignments = self.get_grade_details(schedule_oid)
                    if assignments:
                        # Sort assignments by date (most recent first)
                        sorted_assignments = sorted(
                            assignments,
                            key=lambda x: x.get('dueDate', 0),
                            reverse=True
                        )

                        class_message += "\nRecent Assignments:\n"
                        # Show only the 3 most recent assignments
                        for assignment in sorted_assignments[:3]:
                            name = assignment.get('name', '')
                            category = assignment.get('category', '')
                            due_date = assignment.get('dueDate')

                            # Format date
                            date_str = ''
                            if due_date:
                                date_str = time.strftime('%Y-%m-%d', time.localtime(due_date/1000))

                            # Get score
                            score_elements = assignment.get('scoreElements', [])
                            score = "Not graded"
                            score_percentage = None
                            if score_elements:
                                score_info = score_elements[0]
                                if score_info.get('score') is not None:
                                    score = f"{score_info.get('score')}"
                                    score_percentage = score_info.get('scorePercent')

                            class_message += f"• {name}\n"
                            class_message += f"  📅 Due: {date_str}\n"
                            class_message += f"  📝 {category}: {self.format_score(score, score_percentage)}\n"

            class_message += "\n"

            # If adding this class would make the message too long, start a new message
            if len(current_message + class_message) > 3000:
                messages.append(current_message)
                current_message = class_message
            else:
                current_message += class_message

        # Add the last message if it has content
        if current_message and has_content:
            messages.append(current_message)
        elif not has_content:
            messages.append("No grades or assignments found for the current term.")

        return messages

    def fetch_formatted_grades(self, title="📚 Current Grades"):
        """Fetch grades and return formatted messages"""
        if not self.login():
            return ["❌ Failed to login to Aspen. Please check credentials."]

        class_list = self.get_class_list()
        if not class_list:
            return ["❌ Failed to fetch classes."]

        return self.format_grades_message(class_list, title)

    def login(self):
        # Get CSRF token
        login_page = self.session.get(f"{self.base_url}/logon.do")
        soup = BeautifulSoup(login_page.text, 'html.parser')
        token = soup.find('input', {'name': 'org.apache.struts.taglib.html.TOKEN'})['value']

        # Login
        login_payload = {
            'org.apache.struts.taglib.html.TOKEN': token,
            'userEvent': '930',
            'userParam': '',
            'operationId': '',
            'deploymentId': 'aspen',
            'scrollX': '0',
            'scrollY': '0',
            'formFocusField': 'username',
            'mobile': 'false',
            'SSOLoginDone': '',
            'username': ASPEN_USERNAME,
            'password': ASPEN_PASSWORD,
            'submit': 'Log On'
        }

        # First login request
        response = self.session.post(
            f"{self.base_url}/logon.do",
            data=login_payload,
            headers=self.headers
        )

        print(f"Login response status: {response.status_code}")

        # After login, try to access the home page
        home_response = self.session.get(f"{self.base_url}/home.do", headers=self.headers)

        # Parse the home page response
        soup = BeautifulSoup(home_response.text, 'html.parser')

        # Look for elements that indicate successful login
        login_indicators = [
            "userPreferenceMenu",  # User preferences menu
            "Log Off",            # Logout link
            "confirmLogout"       # Logout confirmation function
        ]

        page_text = home_response.text
        if any(indicator in page_text for indicator in login_indicators):
            print("Login successful - Found authenticated page elements")

            # Get student ID from API instead of hardcoding
            if self.get_student_id():
                return True
            else:
                print("Failed to get student ID")
                return False
        else:
            print("Login failed - Could not find authenticated page elements")
            if "Invalid login" in page_text:
                print("Reason: Invalid credentials")
            elif "Log On" in page_text:
                print("Reason: Still seeing login page")
            return False

    def get_student_id(self):
        """Get the student ID from the users/students API"""
        if not self.student_id:
            url = f"{self.base_url}/rest/users/students"
            response = self.session.get(url, headers=self.headers)

            if response.status_code == 200:
                try:
                    students_data = response.json()
                    if students_data and len(students_data) > 0:
                        student = students_data[0]  # Get first student
                        self.student_id = student.get('studentOid')
                        self.student_name = student.get('name')
                        print(f"Found student: {self.student_name}")
                        print(f"Student ID: {self.student_id}")
                    else:
                        print("No student data found in response")
                except json.JSONDecodeError as e:
                    print(f"Failed to parse student data JSON response: {e}")
                    print("Response content:")
                    print(response.text)
            else:
                print(f"Failed to get student data. Status code: {response.status_code}")

        return self.student_id

    def get_class_list(self):
        """Get the list of all classes"""
        student_id = self.get_student_id()
        url = f"{self.base_url}/rest/students/{student_id}/academicClasses"
        params = {
            'gradeTerm': 'current',
            'year': 'current'
        }

        print(f"Requesting classes from: {url}")
        response = self.session.get(url, params=params, headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            try:
                classes_data = response.json()
                print("Class list retrieved successfully")
                print(f"Number of classes found: {len(classes_data)}")
                return classes_data
            except json.JSONDecodeError as e:
                print(f"Failed to parse class list JSON response: {e}")
                print("Response content:")
                print(response.text)
                return None
        else:
            print(f"Failed to get class list. Status code: {response.status_code}")
            return None

    def get_grade_details(self, schedule_oid):
        """Get details for a specific course's assignments"""
        url = f"{self.base_url}/rest/studentSchedule/{schedule_oid}/assignments"
        params = {
            'gradeTerm': 'current',
            'year': 'current'
        }

        print(f"Requesting assignments for course: {url}")
        response = self.session.get(url, params=params, headers=self.headers)

        if response.status_code == 200:
            try:
                details_data = response.json()
                print(f"Assignment details retrieved successfully")
                return details_data
            except json.JSONDecodeError as e:
                print(f"Failed to parse assignments JSON response: {e}")
                print("Response content:")
                print(response.text)
                return None
        else:
            print(f"Failed to get assignments. Status code: {response.status_code}")
            return None

def main():
    scraper = AspenScraper()
    if scraper.login():
        print("Login successful!")

        # Get all classes
        class_list = scraper.get_class_list()
        if class_list:
            print("\nClasses List:")
            for class_info in class_list:
                course_name = class_info.get('courseName', '')
                grade = class_info.get('sectionTermAverage', 'No grade')
                teacher = class_info.get('teacherName', '')

                print(f"\nCourse: {course_name}")
                print(f"Current Grade: {grade}")
                print(f"Teacher: {teacher}")

                # Only get details if there's a grade
                if class_info.get('percentageValue'):
                    schedule_oid = class_info.get('studentScheduleOid')
                    if schedule_oid:
                        assignments = scraper.get_grade_details(schedule_oid)
                        if assignments:
                            print("\nAssignments:")
                            for assignment in assignments:
                                name = assignment.get('name', '')
                                due_date = assignment.get('dueDate')
                                category = assignment.get('category', '')

                                # Get the score from scoreElements
                                score_elements = assignment.get('scoreElements', [])
                                score = "Not graded"
                                if score_elements:
                                    score_info = score_elements[0]
                                    score = f"{score_info.get('score', 'No score')}"

                                # Convert timestamp to readable date
                                if due_date:
                                    due_date = time.strftime('%Y-%m-%d', time.localtime(due_date/1000))

                                print(f"\n  Assignment: {name}")
                                print(f"  Category: {category}")
                                print(f"  Due Date: {due_date}")
                                print(f"  Score: {score}")
                            print("-" * 50)
    else:
        print("Login failed!")

if __name__ == "__main__":
    main()
