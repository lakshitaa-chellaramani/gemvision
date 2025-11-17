"""
AWS S3 Service for image storage and retrieval
"""
import boto3
from botocore.exceptions import ClientError
from backend.app.config import settings
import io
from PIL import Image
import uuid
from datetime import datetime
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing image uploads to AWS S3"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket = settings.aws_s3_bucket

    def upload_image(
        self,
        image_data: bytes,
        folder: str = "images",
        filename: Optional[str] = None,
        content_type: str = "image/png"
    ) -> Tuple[str, str]:
        """
        Upload image to S3 and return URL and key

        Args:
            image_data: Image bytes
            folder: S3 folder/prefix
            filename: Optional filename (generates UUID if not provided)
            content_type: MIME type

        Returns:
            Tuple of (url, key)
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                ext = content_type.split('/')[-1]
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"

            # Construct S3 key
            key = f"{folder}/{filename}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=image_data,
                ContentType=content_type
            )

            # Generate presigned URL for temporary access (24 hours)
            presigned_url = self.generate_presigned_url(key, expiration=86400)

            if not presigned_url:
                # Fallback to direct URL if presigned generation fails
                presigned_url = f"https://s3.{settings.aws_region}.amazonaws.com/{self.bucket}/{key}"

            logger.info(f"Uploaded image to S3: {key} (presigned URL generated)")
            return presigned_url, key

        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            raise

    def upload_from_pil(
        self,
        image: Image.Image,
        folder: str = "images",
        filename: Optional[str] = None,
        format: str = "PNG"
    ) -> Tuple[str, str]:
        """
        Upload PIL Image to S3

        Args:
            image: PIL Image object
            folder: S3 folder/prefix
            filename: Optional filename
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Tuple of (url, key)
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
        Download image from URL and upload to S3

        Args:
            image_url: URL of image to download
            folder: S3 folder/prefix
            filename: Optional filename

        Returns:
            Tuple of (url, key)
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
            logger.error(f"Error downloading and uploading image: {e}")
            raise

    def create_thumbnail(
        self,
        image_data: bytes,
        max_size: Tuple[int, int] = (300, 300),
        folder: str = "thumbnails",
        filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create and upload thumbnail

        Args:
            image_data: Original image bytes
            max_size: Maximum thumbnail dimensions
            folder: S3 folder/prefix
            filename: Optional filename

        Returns:
            Tuple of (url, key)
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

    def delete_image(self, key: str) -> bool:
        """
        Delete image from S3

        Args:
            key: S3 key of the image

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted image from S3: {key}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting from S3: {e}")
            return False

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access

        Args:
            key: S3 key
            expiration: URL expiration in seconds

        Returns:
            Presigned URL or None
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None


# Global S3 service instance
s3_service = S3Service()
