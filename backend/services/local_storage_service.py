"""
Local File Storage Service for image storage and retrieval
Alternative to S3 for development/local environments
"""
import os
import io
from PIL import Image
import uuid
from datetime import datetime
from typing import Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Service for managing image uploads to local filesystem"""

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize local storage service

        Args:
            base_path: Base directory for storing files (defaults to project_root/uploads)
        """
        if base_path is None:
            # Default to project root's uploads directory
            # Go up from backend/services to project root
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / "uploads"
        else:
            self.base_path = Path(base_path)

        self.base_url = "http://localhost:8000/uploads"  # Base URL for serving files

        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at: {self.base_path.absolute()}")

    def upload_image(
        self,
        image_data: bytes,
        folder: str = "images",
        filename: Optional[str] = None,
        content_type: str = "image/png"
    ) -> Tuple[str, str]:
        """
        Save image to local filesystem and return URL and path

        Args:
            image_data: Image bytes
            folder: Subfolder/prefix
            filename: Optional filename (generates UUID if not provided)
            content_type: MIME type

        Returns:
            Tuple of (url, relative_path)
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                ext = content_type.split('/')[-1]
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"

            # Construct file path
            folder_path = self.base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)

            file_path = folder_path / filename
            relative_path = f"{folder}/{filename}"

            # Save file
            with open(file_path, 'wb') as f:
                f.write(image_data)

            # Construct URL
            url = f"{self.base_url}/{relative_path}"

            logger.info(f"Saved image locally: {file_path}")
            return url, relative_path

        except Exception as e:
            logger.error(f"Error saving to local storage: {e}")
            raise

    def upload_from_pil(
        self,
        image: Image.Image,
        folder: str = "images",
        filename: Optional[str] = None,
        format: str = "PNG"
    ) -> Tuple[str, str]:
        """
        Save PIL Image to local filesystem

        Args:
            image: PIL Image object
            folder: Subfolder/prefix
            filename: Optional filename
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Tuple of (url, relative_path)
        """
        # Convert PIL image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)

        content_type = f"image/{format.lower()}"
        return self.upload_image(buffer.getvalue(), folder, filename, content_type)

    def upload_from_url(
        self,
        image_url: str,
        folder: str = "images",
        filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Download image from URL and save to local filesystem

        Args:
            image_url: URL of image to download
            folder: Subfolder/prefix
            filename: Optional filename

        Returns:
            Tuple of (url, relative_path)
        """
        import requests

        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get('content-type', 'image/png')

            return self.upload_image(
                response.content,
                folder,
                filename,
                content_type
            )

        except Exception as e:
            logger.error(f"Error downloading and saving image: {e}")
            raise

    def create_thumbnail(
        self,
        image_data: bytes,
        max_size: Tuple[int, int] = (300, 300),
        folder: str = "thumbnails",
        filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create and save thumbnail

        Args:
            image_data: Original image bytes
            max_size: Maximum thumbnail dimensions
            folder: Subfolder/prefix
            filename: Optional filename

        Returns:
            Tuple of (url, relative_path)
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))

            # Create thumbnail
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Upload thumbnail
            return self.upload_from_pil(image, folder, filename)

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise

    def delete_image(self, relative_path: str) -> bool:
        """
        Delete image from local filesystem

        Args:
            relative_path: Relative path of the image

        Returns:
            True if successful
        """
        try:
            file_path = self.base_path / relative_path
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted image from local storage: {file_path}")
                return True
            else:
                logger.warning(f"Image not found: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting from local storage: {e}")
            return False

    def get_full_path(self, relative_path: str) -> Path:
        """
        Get full filesystem path from relative path

        Args:
            relative_path: Relative path

        Returns:
            Full Path object
        """
        return self.base_path / relative_path


# Global local storage service instance
local_storage_service = LocalStorageService()
