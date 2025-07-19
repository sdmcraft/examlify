import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import logging
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class FileUtils:
    """Utility class for file operations"""

    @staticmethod
    def validate_pdf_file(file: UploadFile) -> None:
        """
        Validate uploaded PDF file

        Args:
            file: Uploaded file object

        Raises:
            HTTPException: If file validation fails
        """
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )

        # Check file size
        max_size = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024  # 50MB default

        # Read file content to check size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"
            )

        # Check if file is empty
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="File cannot be empty"
            )

    @staticmethod
    def save_uploaded_file(file: UploadFile, upload_dir: str, filename: str) -> str:
        """
        Save uploaded file to disk

        Args:
            file: Uploaded file object
            upload_dir: Directory to save file
            filename: Name to save file as

        Returns:
            Full path to saved file
        """
        try:
            # Create upload directory if it doesn't exist
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, filename)

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"File saved successfully: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file"
            )

    @staticmethod
    def save_to_temp(file: UploadFile, temp_dir: str, filename: str) -> str:
        """
        Save uploaded file to temporary directory for processing

        Args:
            file: Uploaded file object
            temp_dir: Temporary directory path
            filename: Name to save file as

        Returns:
            Full path to saved temporary file
        """
        try:
            # Create temp directory if it doesn't exist
            os.makedirs(temp_dir, exist_ok=True)

            temp_file_path = os.path.join(temp_dir, filename)

            # Save file to temp location
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"File saved to temp location: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            logger.error(f"Failed to save file to temp location: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file to temporary location"
            )

    @staticmethod
    def create_temp_directory(prefix: str = "pdf_processing_") -> str:
        """
        Create a temporary directory for processing

        Args:
            prefix: Prefix for the temporary directory name

        Returns:
            Path to created temporary directory
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            logger.info(f"Created temporary directory: {temp_dir}")
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to create temporary directory: {str(e)}")
            raise

    @staticmethod
    def cleanup_temp_directory(temp_dir: str) -> None:
        """
        Clean up temporary directory and its contents

        Args:
            temp_dir: Path to temporary directory to clean up
        """
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary directory {temp_dir}: {str(e)}")

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes

        Args:
            file_path: Path to file

        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            logger.error(f"Failed to get file size for {file_path}: {str(e)}")
            return 0

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if file exists

        Args:
            file_path: Path to file

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(file_path)

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False