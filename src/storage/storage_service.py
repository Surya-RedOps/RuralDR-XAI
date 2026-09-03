"""
RuralDR-XAI: Storage Service
Supports AWS S3 private bucket storage with signed URLs and secure local storage fallback.
"""

import os
import io
import logging
from pathlib import Path
from typing import Tuple, Optional, Union
import cv2
import numpy as np

logger = logging.getLogger("ruraldr.storage")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
        self.aws_region = os.getenv("AWS_REGION", "ap-south-1").strip()
        self.s3_bucket = os.getenv("AWS_S3_BUCKET", "").strip()

        self.use_s3 = bool(self.aws_access_key and self.aws_secret_key and self.s3_bucket)
        self.s3_client = None

        if self.use_s3:
            try:
                import boto3
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region,
                )
                logger.info(f"StorageService initialized with AWS S3 bucket: {self.s3_bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client ({e}). Falling back to local storage.")
                self.use_s3 = False
        else:
            logger.info(f"StorageService initialized with local storage: {LOCAL_UPLOAD_DIR}")

    def save_image(
        self,
        image_data: Union[bytes, np.ndarray],
        case_id: str,
        filename: str,
        mime_type: str = "image/jpeg",
    ) -> Tuple[str, str, int, int, int]:
        """
        Saves image to S3 or local disk.

        Returns:
            storage_key: Identifier string
            storage_type: 's3' or 'local'
            width: Image width
            height: Image height
            file_size: Size in bytes
        """
        # Convert numpy array to bytes if needed
        if isinstance(image_data, np.ndarray):
            # Convert RGB to BGR for cv2 encoding
            if image_data.ndim == 3 and image_data.shape[2] == 3:
                bgr = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)
            else:
                bgr = image_data
            h, w = image_data.shape[:2]
            success, buffer = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if not success:
                raise ValueError("Failed to encode image data.")
            byte_content = buffer.tobytes()
        elif isinstance(image_data, bytes):
            byte_content = image_data
            # Read dimensions
            nparr = np.frombuffer(byte_content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            h, w = (img.shape[0], img.shape[1]) if img is not None else (1024, 1024)
        else:
            raise TypeError("Expected image_data as bytes or np.ndarray.")

        file_size = len(byte_content)
        sanitized_filename = Path(filename).name
        storage_key = f"cases/{case_id}/{sanitized_filename}"

        if self.use_s3 and self.s3_client is not None:
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=storage_key,
                    Body=byte_content,
                    ContentType=mime_type,
                    ServerSideEncryption="AES256",
                )
                return storage_key, "s3", w, h, file_size
            except Exception as e:
                logger.error(f"S3 upload failed ({e}). Falling back to local disk.")

        # Local storage fallback
        dest_path = LOCAL_UPLOAD_DIR / case_id / sanitized_filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(byte_content)

        return storage_key, "local", w, h, file_size

    def save_file(
        self,
        file_bytes: bytes,
        relative_path: str,
        content_type: str = "application/pdf",
    ) -> Tuple[str, str]:
        """
        Saves arbitrary file bytes (such as PDF reports) to S3 or local disk.
        Returns: (storage_key, storage_type)
        """
        storage_key = relative_path.lstrip("/")
        if self.use_s3 and self.s3_client is not None:
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=storage_key,
                    Body=file_bytes,
                    ContentType=content_type,
                    ServerSideEncryption="AES256",
                )
                return storage_key, "s3"
            except Exception as e:
                logger.error(f"S3 file upload failed ({e}). Falling back to local disk.")

        dest_path = LOCAL_UPLOAD_DIR / storage_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(file_bytes)
        return storage_key, "local"

    def get_image_url(self, storage_key: str, storage_type: str = "local") -> str:
        """
        Generates presigned S3 URL or relative local API endpoint.
        """
        if storage_type == "s3" and self.use_s3 and self.s3_client is not None:
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.s3_bucket, "Key": storage_key},
                    ExpiresIn=3600,  # 1 hour
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate S3 presigned URL ({e}).")

        # Local file URL served by FastAPI static route
        return f"/api/v1/files/{storage_key}"

    def get_image_rgb(self, storage_key: str, storage_type: str = "local") -> Optional[np.ndarray]:
        """Loads RGB numpy array from storage."""
        if storage_type == "s3" and self.use_s3 and self.s3_client is not None:
            try:
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=storage_key)
                byte_content = response["Body"].read()
                nparr = np.frombuffer(byte_content, np.uint8)
                bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if bgr is not None:
                    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            except Exception as e:
                logger.error(f"Failed to read from S3 ({e}).")

        # Local file
        local_path = LOCAL_UPLOAD_DIR / storage_key.replace("cases/", "")
        if not local_path.is_file():
            # Try alternate path pattern
            local_path = LOCAL_UPLOAD_DIR / storage_key
        if local_path.is_file():
            bgr = cv2.imread(str(local_path))
            if bgr is not None:
                return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        return None


# Global singleton
_STORAGE_INSTANCE: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is None:
        _STORAGE_INSTANCE = StorageService()
    return _STORAGE_INSTANCE


storage_service = get_storage_service()

