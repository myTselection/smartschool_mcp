from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import SmartSchoolException
from .session import session

if TYPE_CHECKING: # pragma: no cover
    pass

logger = logging.getLogger(__name__)

__all__ = ["\download_document"]

def download_document(
    course_id: int,
    doc_id: int,
    ss_id: int,
    target_path: str | Path,
    overwrite: bool = False
) -> Path:
    """
    Downloads a specific document from a course's document section.

    Args:
        course_id: The ID of the course containing the document.
        doc_id: The ID of the document (docID) to download.
        ss_id: The ID of the folder (ssID) containing the document.
        target_path: The local file path (including filename) where the document
                     should be saved. If it's a directory, the original filename
                     might be inferred from headers (if available) or a default used.
        overwrite: If True, overwrite the target file if it already exists.
                   Defaults to False.

    Returns:
        The Path object representing the downloaded file.

    Raises:
        SmartschoolException: If the download fails, the target path is invalid,
                              or the file exists and overwrite is False.
        FileNotFoundError: If the target directory does not exist.
    """
    # Construct the download URL based on the provided example structure
    # /Documents/Download/Index/htm/0/courseID/4128/docID/402070/ssID/65
    # The 'htm/0' part might vary, but let's assume it's constant for now.
    # We might need to extract this path more reliably from the FileItem.download_url
    # if it's available. For now, we construct it.
    download_url_path = f"/Documents/Download/Index/htm/0/courseID/{course_id}/docID/{doc_id}/ssID/{ss_id}"
    full_download_url = session.create_url(download_url_path)

    target_filepath = Path(target_path)

    # Ensure target directory exists
    if not target_filepath.parent.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_filepath.parent}")
    if target_filepath.is_dir():
         # If target is a directory, we need a filename.
         # SmartSchool download URLs don't usually give us the filename directly.
         # We might need to get it from the CourseDocuments parsing or use a default.
         # For now, raise an error, requiring a full file path.
         raise ValueError("target_path must be a full file path, not a directory.")

    # Check for existing file
    if target_filepath.exists() and not overwrite:
        raise SmartschoolException(f"Target file already exists and overwrite is False: {target_filepath}")

    logger.info(f"Attempting to download document docID={doc_id} from courseID={course_id} to {target_filepath}")

    try:
        # Use stream=True for potentially large files
        with session.get(full_download_url, stream=True, allow_redirects=True) as response:
            response.raise_for_status() # Check for HTTP errors

            # Check if we were redirected to login (though session should handle this)
            if "/login" in response.url:
                 raise SmartschoolAuthenticationError(f"Redirected to login page when downloading docID {doc_id}. Session might be invalid.")

            # Write the content to the file
            with open(target_filepath, 'wb') as f:
                shutil.copyfileobj(response.raw, f)

            logger.info(f"Successfully downloaded document to {target_filepath}")
            return target_filepath

    except Exception as e:
        # Clean up potentially partially downloaded file on error
        if target_filepath.exists():
            try:
                target_filepath.unlink()
            except OSError:
                logger.warning(f"Could not remove partially downloaded file: {target_filepath}")
        # Wrap specific request errors or re-raise generic ones
        raise SmartschoolException(f"Failed to download document docID={doc_id} from {full_download_url}: {e}") from e
