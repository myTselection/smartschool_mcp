from __future__ import annotations

from functools import cached_property
import logging # Added import
import re
from typing import Iterator, Union, Literal
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, Field, computed_field

from .objects import Course, CourseCondensed
from .session import session
from .exceptions import SmartSchoolException, SmartschoolParsingError # Ensure casing matches definition

# Define data models for folders and files
# ... (rest of the models FolderItem, FileItem etc. should be here)

__all__ = ["Courses", "TopNavCourses", "CourseDocuments", "FolderItem", "FileItem", "DocumentOrFolderItem"]


class TopNavCourses:
    """
    Retrieves a list of the courses which are available from the top navigation bar.

    This structure is different from the `Courses` results.

    Example:
    -------
    >>> for course in TopNavCourses():
    >>>     print(course.name)
    Aardrijkskunde_3_LOP_2023-2024
    bibliotheek

    """

    @cached_property
    def _list(self) -> list[CourseCondensed]:
        return [CourseCondensed(**course) for course in session.json("/Topnav/getCourseConfig", method="post")["own"]]

    def __iter__(self) -> Iterator[CourseCondensed]:
        yield from self._list


class Courses:
    """
    Retrieves a list of the courses.

    This structure is different from the `TopNavCourses` results.

    To reproduce: go to "Results", one of the XHR calls is this one

    Example:
    -------
    >>> for course in Courses():
    >>>     print(course.name)
    Aardrijkskunde
    Biologie

    """

    @cached_property
    def _list(self) -> list[Course]:
        return [Course(**course) for course in session.json("/results/api/v1/courses/")]

    def __iter__(self) -> Iterator[Course]:
        yield from self._list


class CourseDocuments:
    """
    Fetches the HTML representation of the document folder structure for a specific course.

    Requires a course ID to initialize. The `get_folder_html` method can optionally
    take a folder ID (`ssID`) to fetch a specific subfolder's structure.

    Example:
    -------
    >>> course_docs = CourseDocuments(course_id=4128)
    >>> root_html = course_docs.get_folder_html() # Get root folder HTML
    >>> subfolder_html = course_docs.get_folder_html(folder_id=65) # Get specific folder HTML
    """
    def __init__(self, course_id: int):
        if not isinstance(course_id, int) or course_id <= 0:
            raise ValueError("course_id must be a positive integer.")
        self.course_id = course_id
        self._base_path = f"/Documents/Index/Index/courseID/{self.course_id}"

    def get_folder_html(self, folder_id: int | None = None) -> str:
        """
        Fetches the HTML content for a specific folder within the course documents.

        Args:
            folder_id: The specific folder ID (`ssID`) to fetch. If None, fetches the
                       root document folder for the course.

        Returns:
            The raw HTML content of the folder page as a string.

        Raises:
            SmartSchoolException: If the request fails or returns an error status.
        """
        target_path = self._base_path
        if folder_id is not None:
            if not isinstance(folder_id, int) or folder_id <= 0:
                raise ValueError("folder_id must be a positive integer if provided.")
            target_path += f"/ssID/{folder_id}"

        # Define headers - minimal set, session handles cookies
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Referer": session.create_url("/") # Referer might be important
        }

        try:
            response = session.get(target_path, headers=headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.text
        except Exception as e:
            # Wrap specific request errors or re-raise generic ones
            raise SmartSchoolException(f"Failed to fetch document folder HTML for course {self.course_id}, folder {folder_id}: {e}") from e # Ensure casing matches definition
