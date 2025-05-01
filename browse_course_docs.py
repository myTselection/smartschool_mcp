\
import sys
import os
import logging
from pathlib import Path
import traceback # For detailed error printing

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from smartschool import (
        Smartschool,
        PathCredentials,
        Courses,
        CourseDocuments,
        FolderItem,
        FileItem,
        DocumentOrFolderItem,
        download_document,
        SmartSchoolException, # Corrected casing
        SmartschoolParsingError,
        SmartschoolAuthenticationError
    )
    from smartschool.logger import setup_logger
except ImportError as e:
    print(f"Error importing smartschool modules: {e}")
    print("Ensure the 'src' directory is correctly added to sys.path and all dependencies are installed.")
    sys.exit(1)

# --- Configuration ---
DOWNLOAD_DIR = Path("./course_downloads") # Directory to save downloaded files
ENABLE_DEBUG_LOGGING = False # Set to True for detailed logs
# --- End Configuration ---

if ENABLE_DEBUG_LOGGING:
    setup_logger(logging.DEBUG)
else:
    # Basic logging if debug is off
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def display_items(items: list[DocumentOrFolderItem]):
    """Displays folders and files with numbers."""
    if not items:
        print("  Folder is empty.")
        return
    for i, item in enumerate(items):
        item_type = "Folder" if isinstance(item, FolderItem) else "File"
        print(f"  [{i+1}] {item_type}: {item.name}")

def get_user_choice(prompt: str, max_value: int) -> str | int | None:
    """Gets validated user input (number, 'u', 'q')."""
    while True:
        try:
            choice = input(prompt).strip().lower()
            if choice == 'q':
                return 'q'
            if choice == 'u':
                return 'u'
            if choice.isdigit():
                num_choice = int(choice)
                if 1 <= num_choice <= max_value:
                    return num_choice
                else:
                    print(f"  Invalid number. Please enter a number between 1 and {max_value}.")
            else:
                print("  Invalid input. Please enter a number, 'u', or 'q'.")
        except ValueError:
            print("  Invalid input. Please enter a number, 'u', or 'q'.")
        except EOFError: # Handle Ctrl+D or similar
             print("\\nExiting.")
             return 'q'

def browse_documents(course_docs: CourseDocuments):
    """Main loop for browsing folders and downloading files."""
    current_path_items: list[FolderItem] = [] # Stores the FolderItems representing the path
    current_folder_id: int | None = None # None represents the root
    parent_id: int | None = None # Keep track of parent for navigation

    while True:
        current_path_str = " / ".join([item.name for item in current_path_items]) if current_path_items else "(Root)"
        print(f"\\nCurrent Location: {current_path_str}")

        try:
            # Fetch items. Pass current folder_id and parent_id.
            # Note: SmartSchool's parentID logic might need adjustment.
            # For root (current_folder_id=None), parent_id is likely irrelevant.
            # For subfolders, the parent_id is the ssID of the folder *containing* the current one.
            items = list(course_docs.list_folder_contents(folder_id=current_folder_id, parent_id=parent_id))
            items.sort(key=lambda x: (0 if isinstance(x, FolderItem) else 1, x.name)) # Folders first, then alphabetical
        except SmartschoolParsingError as e:
            print(f"  Error parsing folder contents: {e}")
            items = []
        except SmartschoolException as e:
            print(f"  Error fetching folder contents: {e}")
            # Option to retry or go back? For now, just show empty.
            items = []

        display_items(items)

        prompt = f"Enter number to open/download, 'u' to go up, 'q' to quit: "
        choice = get_user_choice(prompt, len(items))

        if choice == 'q':
            break
        elif choice == 'u':
            if current_path_items:
                current_path_items.pop() # Remove last folder from path
                if current_path_items:
                    current_folder_id = current_path_items[-1].id
                    # Determine the new parent_id (parent of the folder we just navigated up *to*)
                    parent_id = current_path_items[-2].id if len(current_path_items) > 1 else None
                else:
                    current_folder_id = None # Back to root
                    parent_id = None
            else:
                print("  Already at the root folder.")
        elif isinstance(choice, int):
            selected_item = items[choice - 1]
            if isinstance(selected_item, FolderItem):
                # Navigate into folder
                parent_id = current_folder_id # The current folder becomes the parent
                current_folder_id = selected_item.id
                current_path_items.append(selected_item)
            elif isinstance(selected_item, FileItem):
                # Download file
                print(f"  Selected file: {selected_item.name}")
                DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
                # Construct target path within the download dir, preserving original name
                target_file = DOWNLOAD_DIR / selected_item.name
                print(f"  Attempting to download to: {target_file}")
                try:
                    download_document(
                        course_id=selected_item.course_id,
                        doc_id=selected_item.id,
                        ss_id=selected_item.folder_id, # ssID is the folder *containing* the file
                        target_path=target_file,
                        overwrite=False # Set to True or prompt user if needed
                    )
                    print(f"  Successfully downloaded '{selected_item.name}'.")
                except FileExistsError:
                     print(f"  Download failed: File already exists at '{target_file}'. Use overwrite=True or delete the existing file.")
                except SmartschoolException as e:
                    print(f"  Download failed: {e}")
                except Exception as e:
                    print(f"  An unexpected error occurred during download: {e}")
                    logger.error(f"Download error details: {traceback.format_exc()}")


def main():
    logger.info("Starting Smartschool Course Document Browser...")
    try:
        print("--- Initializing Session --- ")
        creds = PathCredentials() # Assumes credentials.yml exists
        session = Smartschool.start(creds)
        logger.info("Authentication successful.")
        print("--- Authentication Successful ---")

        # --- Select Course ---
        print("\\n--- Fetching Courses ---")
        try:
            all_courses = list(Courses())
            if not all_courses:
                print("No courses found.")
                return
            print("Available Courses:")
            for i, course in enumerate(all_courses):
                 # Displaying teachers might be helpful for disambiguation
                 teacher_names = ', '.join(t.name.startingWithLastName for t in course.teachers)
                 print(f"  [{i+1}] {course.name} (Teachers: {teacher_names}, ID: {course.id})")

            choice = get_user_choice("Select a course number: ", len(all_courses))
            if not isinstance(choice, int): # Handle 'q' or invalid input
                 print("Exiting.")
                 return

            selected_course = all_courses[choice - 1]
            print(f"\\nSelected Course: {selected_course.name} (ID: {selected_course.id})")

        except SmartschoolException as e:
            print(f"Error fetching courses: {e}")
            return

        # --- Browse Documents ---
        course_docs = CourseDocuments(course_id=selected_course.id)
        browse_documents(course_docs)

    except (SmartschoolAuthenticationError, FileNotFoundError) as e:
        logger.critical(f"Initialization failed: {e}")
        print(f"\\n!!! CRITICAL ERROR: {e}")
        if isinstance(e, FileNotFoundError):
            print("Ensure credentials.yml exists and is configured correctly.")
    except SmartschoolException as e:
        logger.error(f"A Smartschool API error occurred: {e}")
        print(f"\\n!!! API ERROR: {e}")
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=ENABLE_DEBUG_LOGGING)
        print(f"\\n!!! UNEXPECTED CRITICAL ERROR: {e}")
        print("--- Error Details ---")
        traceback.print_exc() # Print full traceback for unexpected errors
        print("---------------------")


    logger.info("Smartschool Course Document Browser finished.")
    print("\\n--- Script Finished --- ")

if __name__ == "__main__":
    main()
