import sys
import os
import logging # Add import for logging

# Add the src directory to the Python path to ensure the local library is used
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from smartschool import Smartschool, PathCredentials, Courses
from smartschool.logger import setup_logger # Import setup_logger

# Set up the logger with DEBUG level
setup_logger(logging.DEBUG)

Smartschool.start(PathCredentials())
for course in Courses():
    print(course.name)