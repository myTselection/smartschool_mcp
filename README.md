# Smartschool parser

[![codecov](https://codecov.io/gh/svaningelgem/smartschool/graph/badge.svg?token=U0A3H3K4L0)](https://codecov.io/gh/svaningelgem/smartschool)

Unofficial interpreter to interface against smartschool's website.

**Status:** Actively developed, but some features might be unstable due to changes on the Smartschool platform. Authentication and basic course listing are currently confirmed working.

## How to use?

1.  **Credentials:**
    *   Copy `credentials.yml.example` to `credentials.yml` and fill in your details (username, password, school URL, birth date).
2.  **Initialization:** Start the session using your credentials.
3.  **Access Features:** Use the imported classes to interact with Smartschool data.

```python
import logging
from datetime import date # Added for lesson example
from smartschool import (
    Smartschool,
    PathCredentials,
    Courses,
    TopNavCourses,
    Results,
    Periods,
    FutureTasks,
    SmartschoolLessons,
    SmartschoolHours,
    MessageHeaders,
    BoxType,
    StudentSupportLinks,
    # ... import other needed classes
)
from smartschool.logger import setup_logger

# Optional: Enable detailed logging
setup_logger(logging.DEBUG)

# Load credentials from credentials.yml (or specified path)
creds = PathCredentials()
# creds = PathCredentials("path/to/your/credentials.yml")

# Start the session (handles login)
session = Smartschool.start(creds)

# Example: List courses
print("Fetching courses...")
try:
    for course in Courses():
        print(f"- {course.name}")
except Exception as e:
    print(f"Error fetching courses: {e}")

# ... add calls to other features as needed ...

print("\nDone.")
```

## Available Features (Status as of 2025-04-30)

This section details the main classes and functionalities provided by the library.

### Core & Authentication

*   **`Smartschool`**: The main session class. Use `Smartschool.start(credentials)` to initialize and authenticate. Handles login, cookie management, and provides `get`, `post`, `json` methods for making authenticated requests.
    *   **Status:** **Working** (Core authentication flow confirmed).
*   **`PathCredentials`**: Class to load user credentials (username, password, URL, birth date) from a YAML file (`credentials.yml` by default).
    *   **Status:** **Working**.
*   **`logger` / `setup_logger`**: Configures logging for the library. Useful for debugging.
    *   **Status:** **Working**.

### Courses

*   **`Courses`**: Retrieves the main list of courses associated with the user, typically shown in the "Results" or "Skore" section.
    *   **Status:** **Working**.
    *   **Example:** `for course in Courses(): print(course.name)`
*   **`TopNavCourses`**: Retrieves the list of courses/links shown in the top navigation bar (often includes non-academic links like "library"). Returns `CourseCondensed` objects.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `for course in TopNavCourses(): print(course.name)`

### Results / Skore

*   **`Results`**: Fetches evaluation results (grades, scores) from the "Skore" module. Returns `Result` objects, which can contain detailed information.
    *   **Status:** Believed Working (Based on tests and structure).
    *   **Example:** `for result in Results(): print(result.name, result.graphic.description)`
*   **`ResultDetail`**: Potentially used for fetching more details about a specific result (needs verification).
    *   **Status:** Untested / Unconfirmed.
*   **`Periods`**: Retrieves the defined academic periods (e.g., semesters, trimesters) used in the "Skore" module.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `for period in Periods(): print(period.name)`

### Agenda & Tasks

*   **`FutureTasks`**: Fetches upcoming tasks (tests, assignments) from the agenda. Organizes them by day and course.
    *   **Status:** Believed Working (Based on tests and structure).
    *   **Example:** See "How to use?" section.
*   **`SmartschoolLessons`**: Retrieves lesson details from the agenda for a specific week. Requires date input.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `from datetime import date; lessons = SmartschoolLessons(date(2024, 5, 1)); for lesson in lessons: print(lesson.subject)`
*   **`SmartschoolHours`**: Retrieves the schedule/timetable hours definition.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `for hour in SmartschoolHours(): print(hour.name, hour.value)`
*   **`SmartschoolMomentInfos`**: Fetches detailed information about specific moments (lessons) in the agenda, often used for tooltips. Requires moment IDs.
    *   **Status:** Believed Working (Based on tests).

### Messages

*   **`MessageHeaders`**: Lists messages in a specified mailbox folder (`BoxType`), with options for sorting (`SortField`, `SortOrder`).
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `from smartschool import BoxType; for header in MessageHeaders(BoxType.INBOX): print(header.subject)`
*   **`Message`**: Fetches the full content of a specific message by its ID.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `msg = Message(message_id); print(msg.body)`
*   **`Attachments`**: Lists attachments associated with a message.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `attachments = Attachments(message_id); for att in attachments: print(att.name)`
    *   **Note:** Downloading attachments might require separate handling (see `tests/requests/get/module%3DMessages%26file%3Ddownload...`).
*   **`MarkMessageUnread`**: Marks a message as unread.
    *   **Status:** Believed Working (Based on tests).
*   **`AdjustMessageLabel`**: Adds or removes labels (`MessageLabel`) from messages.
    *   **Status:** Believed Working (Based on tests).
*   **`MessageMoveToArchive` / `MessageMoveToTrash`**: Moves messages to the archive or trash folder.
    *   **Status:** Believed Working (Based on tests).
*   **`BoxType`, `SortField`, `SortOrder`, `MessageLabel`**: Enums/helper classes for message operations.
    *   **Status:** **Working**.

### Other

*   **`StudentSupportLinks`**: Fetches links related to student support services configured by the school.
    *   **Status:** Believed Working (Based on tests).
    *   **Example:** `for link in StudentSupportLinks(): print(link.name)`

### Exceptions

*   **`SmartSchoolException`**: Base exception for library-specific errors.
*   **`SmartschoolAuthenticationError`**: Raised specifically for login/authentication failures.
*   **`SmartSchoolDownloadError`**: Potentially raised during file download operations.

## Authentication

This library now supports Smartschool's two-factor authentication which requires a birth date verification. You must provide your birth date in YYYY-MM-DD format when setting up credentials.

### YAML Configuration (`credentials.yml`)

Create a file named `credentials.yml` (or copy `credentials.yml.example`) in your project directory or specify its path:

```yaml
username: your_username
password: your_password
main_url: your_school.smartschool.be
birth_date: YYYY-MM-DD  # Your birth date

# Optional: For email reporting scripts
# email_from: ...
# email_to:
#  - ...
```

### Usage Example

```python
from smartschool import Smartschool, PathCredentials

# Load from default credentials.yml
creds = PathCredentials()

# Or specify a path
# creds = PathCredentials("path/to/your/config.yml")

session = Smartschool.start(creds)
```

## Contributing?
To get started (I always use mamba/conda to create an environment)
```bash
git clone https://github.com/svaningelgem/smartschool.git
cd smartschool
mamba create -n smartschool python=3.11
mamba activate smartschool
pip install poetry
poetry install
```
Now you can start contributing.

To run the test suite:
```bash
poetry run pytest
```
