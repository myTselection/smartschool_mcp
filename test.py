import sys
import os
import logging
from datetime import date, timedelta

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

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
    SmartschoolMomentInfos, # Added for completeness
    MessageHeaders,
    Message,
    Attachments,
    BoxType,
    SortField,
    SortOrder,
    StudentSupportLinks,
    SmartSchoolException, # Corrected casing
    # Import other necessary components if needed
)
from smartschool.logger import setup_logger

# --- Configuration ---
# Set to True to enable detailed debug logging
ENABLE_DEBUG_LOGGING = True
# Set the date for fetching lessons (e.g., today)
LESSON_DATE = date.today()
# Limit the number of results/messages to fetch/print to avoid excessive output
MAX_RESULTS_TO_PRINT = 5
MAX_MESSAGES_TO_PRINT = 5
# --- End Configuration ---

if ENABLE_DEBUG_LOGGING:
    setup_logger(logging.DEBUG)
else:
    # Basic logging if debug is off
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# Store test results
test_results_summary = []

def run_feature_test(feature_name, test_func):
    """Helper function to run a test, catch exceptions, and record the result."""
    global test_results_summary
    print(f"\n--- Testing: {feature_name} ---")
    success = False
    try:
        test_func()
        print(f"--- Finished: {feature_name} ---")
        success = True
    except SmartSchoolException as e: # Corrected casing
        logger.error(f"SmartSchool Error testing {feature_name}: {e}", exc_info=ENABLE_DEBUG_LOGGING)
        print(f"!!! SmartSchool Error testing {feature_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error testing {feature_name}: {e}", exc_info=ENABLE_DEBUG_LOGGING)
        print(f"!!! Unexpected Error testing {feature_name}: {e}")
    finally:
        test_results_summary.append({"name": feature_name, "status": "PASSED" if success else "FAILED"})
        return success # Return status for conditional execution if needed

# --- Test Functions ---

def test_courses():
    courses = list(Courses())
    print(f"Found {len(courses)} courses:")
    for i, course in enumerate(courses):
        print(f"- {course.name} (ID: {course.id}, Teachers: {', '.join(t.name.startingWithLastName for t in course.teachers)})")
        if i >= MAX_RESULTS_TO_PRINT - 1:
            print("... (truncated)")
            break

def test_topnav_courses():
    topnav_courses = list(TopNavCourses())
    print(f"Found {len(topnav_courses)} top-nav courses/links:")
    for i, course in enumerate(topnav_courses):
        print(f"- {course.name} (Teacher: {course.teacher}, URL: {course.url})")
        if i >= MAX_RESULTS_TO_PRINT - 1:
            print("... (truncated)")
            break

def test_results():
    results = list(Results())
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        course_names = ', '.join(c.name for c in result.courses)
        graphic_desc = result.graphic.description if result.graphic else 'N/A'
        print(f"- {result.name} (Course: {course_names}, Date: {result.date}, Result: {graphic_desc}, ID: {result.identifier})")
        if i >= MAX_RESULTS_TO_PRINT - 1:
            print("... (truncated)")
            break

def test_periods():
    periods = Periods()
    print(f"Found {len(list(periods))} periods:")
    for period in periods:
        # Corrected attribute access for date range
        print(f"- {period.name} (ID: {period.id}, Start: {period.skoreWorkYear.dateRange.start}, End: {period.skoreWorkYear.dateRange.end})")

def test_future_tasks():
    future_tasks_data = FutureTasks()
    print(f"Found {len(future_tasks_data.days)} days with future tasks:")
    days_printed = 0
    for day in future_tasks_data.days:
        print(f"  Date: {day.pretty_date} ({day.date})")
        for course_task in day.courses:
            print(f"    Course: {course_task.course_title}")
            for task in course_task.items.tasks:
                print(f"      Task: {task.label} - {task.description} (ID: {task.assignmentID})")
            if course_task.items.materials:
                 print(f"      Materials: {', '.join(course_task.items.materials)}") # Assuming materials is a list of strings
        days_printed += 1
        if days_printed >= MAX_RESULTS_TO_PRINT:
             print("... (truncated days)")
             break


def test_lessons():
    print(f"Fetching lessons for the week of: {LESSON_DATE}")
    lessons = SmartschoolLessons(LESSON_DATE)
    lessons_list = list(lessons) # Consume the iterator
    print(f"Found {len(lessons_list)} lessons for the week.")
    moment_ids_to_test = []
    lessons_printed = 0
    for lesson in lessons_list:
        print(f"- Date: {lesson.date}, Hour: {lesson.hourValue} ({lesson.hour}), Course: {lesson.courseTitle}, Subject: {lesson.subject or '[No Subject]'}, MomentID: {lesson.momentID}")
        if lesson.momentID and lessons_printed < MAX_RESULTS_TO_PRINT : # Collect some moment IDs for the next test
             moment_ids_to_test.append(lesson.momentID)
        lessons_printed += 1
        if lessons_printed >= MAX_RESULTS_TO_PRINT * 2: # Print a bit more for lessons
             print("... (truncated lessons)")
             break
    return moment_ids_to_test # Return moment IDs for the MomentInfo test

def test_moment_infos(moment_ids):
    if not moment_ids:
        print("No moment IDs found from lessons to test MomentInfos.")
        return
    print(f"Fetching moment info for {len(moment_ids)} moments...")
    moment_infos = SmartschoolMomentInfos(moment_ids)
    moment_infos_list = list(moment_infos)
    print(f"Found info for {len(moment_infos_list)} moments:")
    for i, info in enumerate(moment_infos_list):
        # Accessing attributes safely
        class_name = getattr(info, 'className', 'N/A')
        subject = getattr(info, 'subject', 'N/A')
        moment_id = getattr(info, 'momentID', 'N/A')
        assignments = getattr(info, 'assignments', [])
        materials = getattr(info, 'materials', [])

        print(f"- MomentID: {moment_id}, Class: {class_name}, Subject: {subject}")
        if assignments:
             # Ensure assignments is iterable and handle potential single object case
             assign_list = assignments if isinstance(assignments, list) else [assignments]
             # Check if the list itself contains assignment objects or is nested
             if assign_list and hasattr(assign_list[0], 'assignment'):
                 actual_assignments = assign_list[0].assignment # Access nested assignment(s)
                 actual_assignments = actual_assignments if isinstance(actual_assignments, list) else [actual_assignments]
                 for assign in actual_assignments:
                     assign_desc = getattr(assign, 'description', 'N/A')
                     assign_deadline = getattr(assign, 'assignmentDeadline', 'N/A')
                     print(f"    Assignment: {assign_desc} (Deadline: {assign_deadline})")
             elif assign_list: # Handle case where assignments might be directly in the list
                 for assign in assign_list:
                     # Check if 'assign' itself is the assignment object
                     if hasattr(assign, 'description'):
                         assign_desc = getattr(assign, 'description', 'N/A')
                         assign_deadline = getattr(assign, 'assignmentDeadline', 'N/A')
                         print(f"    Assignment: {assign_desc} (Deadline: {assign_deadline})")
                     # Or if it's nested under 'assignment' key
                     elif hasattr(assign, 'assignment'):
                         nested_assign = assign.assignment
                         nested_assign = nested_assign if isinstance(nested_assign, list) else [nested_assign]
                         for na in nested_assign:
                             assign_desc = getattr(na, 'description', 'N/A')
                             assign_deadline = getattr(na, 'assignmentDeadline', 'N/A')
                             print(f"    Assignment: {assign_desc} (Deadline: {assign_deadline})")


        # Materials might need specific handling depending on structure
        if hasattr(materials, 'material') and materials.material:
             mat_list = materials.material if isinstance(materials.material, list) else [materials.material]
             for mat in mat_list:
                 mat_desc = getattr(mat, 'description', 'N/A')
                 print(f"    Material: {mat_desc}")
        elif materials and not hasattr(materials, 'hidden'): # Avoid printing simple {'hidden': '0'}
             print(f"    Materials data: {materials}") # Fallback

        if i >= MAX_RESULTS_TO_PRINT - 1:
            print("... (truncated moment infos)")
            break


def test_hours():
    hours = AgendaHours()
    print(f"Found {len(list(hours))} defined hours:")
    for hour in hours:
        # Corrected attribute access from hour.name to hour.title
        print(f"- {hour.title}: {hour.value} (ID: {hour.id})")

def test_message_headers():
    print("Fetching latest 5 messages from INBOX...")
    # Corrected keyword argument from box to box_type
    headers = list(MessageHeaders(box_type=BoxType.INBOX, sortfield=SortField.DATE, sortorder=SortOrder.DESC))
    message_ids = []
    for i, header in enumerate(headers):
        if i >= 5:
            break
        print(
            f"- Subject: {header.subject}\n"
            f"  From: {header.sender.name} ({header.sender.id})\n"
            f"  To: {[(recipient.name, recipient.id) for recipient in header.recipients]}\n"
            f"  Date: {header.date}\n"
            f"  Unread: {header.unread}\n"
            f"  Has Attachments: {header.has_attachments}\n"
            f"  ID: {header.id}"
        )
        message_ids.append(header.id)
    return message_ids

def test_single_message(message_id):
    print(f"Fetching full message content for ID: {message_id}")
    msg = Message(message_id)
    sender = msg.jFrom[0].name if msg.jFrom else 'N/A'
    recipients = ', '.join(to.name for to in msg.jTo) if msg.jTo else 'N/A'
    print(f"  From: {sender}")
    print(f"  To: {recipients}")
    print(f"  Subject: {msg.subject}")
    print(f"  Date: {msg.date}")
    print(f"  Body (first 200 chars): {msg.body[:200]}...")

def test_attachments(message_id):
    print(f"Fetching attachments for message ID: {message_id}")
    attachments = list(Attachments(message_id))
    if not attachments:
        print("  No attachments found.")
        return
    print(f"  Found {len(attachments)} attachments:")
    for att in attachments:
        print(f"  - Name: {att.name}, Size: {att.size}, Type: {att.mime} (FileID: {att.fileID})")
        # Note: Downloading requires session.get(f"/?module=Messages&file=download&fileID={att.fileID}&target=0")

def test_student_support_links():
    links = list(StudentSupportLinks())
    print(f"Found {len(links)} student support links:")
    for link in links:
        print(f"- {link.name}: {link.description} (Link: {link.cleanLink}, ID: {link.id})")


# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Smartschool API test script...")
    moment_ids_for_info_test = []
    message_ids_for_detail_test = []
    # Clear previous results if script is run multiple times in one session
    test_results_summary.clear()

    try:
        # --- Authentication ---
        print("--- Initializing Session --- ")
        creds = PathCredentials() # Assumes credentials.yml exists
        session = Smartschool.start(creds)
        logger.info("Authentication successful.")
        print("--- Authentication Successful ---")

        # --- Run Tests ---
        run_feature_test("Courses", test_courses)
        run_feature_test("TopNav Courses", test_topnav_courses)
        run_feature_test("Results/Skore", test_results)
        run_feature_test("Periods", test_periods)
        run_feature_test("Future Tasks", test_future_tasks)
        # Corrected call to test_hours
        run_feature_test("Agenda Hours", test_hours) # Removed AgendaHours() instantiation here

        # Run lesson test and get moment IDs
        # Use a lambda that calls test_lessons and updates the global variable
        run_feature_test("Agenda Lessons", lambda: globals().update(moment_ids_for_info_test=test_lessons()))

        # Run moment info test if we got IDs
        if moment_ids_for_info_test:
             run_feature_test("Agenda Moment Infos", lambda: test_moment_infos(moment_ids_for_info_test))
        else:
             print("\n--- Skipping: Agenda Moment Infos (No Moment IDs from Lessons) ---")
             test_results_summary.append({"name": "Agenda Moment Infos", "status": "SKIPPED"})


        # Run message header test and get message IDs
        # Use a lambda that calls test_message_headers and updates the global variable
        run_feature_test("Message Headers (INBOX)", lambda: globals().update(message_ids_for_detail_test=test_message_headers()))

        # Run single message and attachment tests if we got IDs
        if message_ids_for_detail_test:
            # Keep track if any sub-tests fail
            all_message_tests_passed = True
            for msg_id in message_ids_for_detail_test:
                 # Capture success/failure of each sub-test
                 msg_success = run_feature_test(f"Single Message (ID: {msg_id})", lambda msg_id=msg_id: test_single_message(msg_id))
                 att_success = run_feature_test(f"Attachments (ID: {msg_id})", lambda msg_id=msg_id: test_attachments(msg_id))
                 if not msg_success or not att_success:
                     all_message_tests_passed = False
            # Optionally add a summary status for the group
            # test_results_summary.append({"name": "Single Message & Attachments", "status": "PASSED" if all_message_tests_passed else "FAILED"})
        else:
             print("\n--- Skipping: Single Message & Attachments (No Message IDs from Headers) ---")
             test_results_summary.append({"name": "Single Message Details", "status": "SKIPPED"})
             test_results_summary.append({"name": "Message Attachments", "status": "SKIPPED"})


        run_feature_test("Student Support Links", test_student_support_links)

        # Add calls to other test functions here if needed
        # e.g., run_feature_test("Other Feature", test_other_feature)

    except SmartSchoolException as e: # Corrected casing
        logger.critical(f"Failed to initialize Smartschool session or critical error: {e}", exc_info=ENABLE_DEBUG_LOGGING)
        print(f"\n!!! CRITICAL ERROR: {e}")
    except FileNotFoundError:
        logger.critical("Could not find credentials.yml. Please create it from credentials.yml.example.")
        print("\n!!! CRITICAL ERROR: Could not find credentials.yml. Please create it from credentials.yml.example.")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=ENABLE_DEBUG_LOGGING)
        print(f"\n!!! UNEXPECTED CRITICAL ERROR: {e}")
        # Mark any tests not yet run as FAILED due to critical error? Or just stop?
        # For simplicity, we'll just print the summary of what ran.

    # --- Print Summary ---
    print("\n--- Test Summary ---")
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    if not test_results_summary:
        print("No tests were executed.")
    else:
        for result in test_results_summary:
            print(f"- {result['name']}: {result['status']}")
            if result['status'] == "PASSED":
                passed_count += 1
            elif result['status'] == "FAILED":
                failed_count += 1
            elif result['status'] == "SKIPPED":
                skipped_count += 1
        print(f"\nTotal PASSED: {passed_count}, FAILED: {failed_count}, SKIPPED: {skipped_count}")


    logger.info("Smartschool API test script finished.")
    print("\n--- Test Script Finished --- ")

