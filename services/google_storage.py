from google.cloud import storage
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import requests
import os
import re


MESES_ES = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
]


class gcpService:
    def __init__(self, credentials_path: str = None):
        """
        Initialize GCP Storage service.

        Args:
            credentials_path: Path to service account JSON file.
                              If None, uses GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        self.client = storage.Client()

    def get_image_from_path(self, bucket_name: str, blob_path: str) -> Image.Image:
        """
        Fetch an image from bucket and path.

        Args:
            bucket_name: Name of the GCS bucket
            blob_path: Path to the file within the bucket

        Returns:
            PIL Image object
        """
        return self._download_image(bucket_name, blob_path)

    def get_image_bytes(self, gs_url: str) -> bytes:
        """
        Fetch image as raw bytes from a gs:// URL.

        Args:
            gs_url: Google Storage URL

        Returns:
            Raw image bytes
        """
        bucket_name, blob_path = self._parse_gs_url(gs_url)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        return blob.download_as_bytes()

    def parse_public_url(self, url: str) -> tuple:
        """
        Parse a public GCS URL into bucket name and blob path.

        Args:
            url: Public URL (e.g., https://storage.googleapis.com/bucket/path/to/file)

        Returns:
            Tuple of (bucket_name, blob_path)
        """
        prefix = "https://storage.googleapis.com/"
        if not url.startswith(prefix):
            raise ValueError(f"Invalid public GCS URL: {url}")

        path = url[len(prefix):]  # Remove prefix
        parts = path.split("/", 1)

        if len(parts) < 2:
            raise ValueError(f"Invalid public GCS URL format: {url}")

        return parts[0], parts[1]

    def _download_image(self, bucket_name: str, blob_path: str) -> Image.Image:
        """
        Download image from GCS and return as PIL Image.

        Args:
            bucket_name: Name of the GCS bucket
            blob_path: Path to the file within the bucket

        Returns:
            PIL Image object
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        image_bytes = blob.download_as_bytes()
        image = Image.open(BytesIO(image_bytes))

        return image

    def generate_signed_url(self, bucket_name: str, blob_path: str, expiration_minutes: int = 60) -> str:
        """
        Generate a signed URL for a file in GCS.

        Args:
            bucket_name: Name of the GCS bucket
            blob_path: Path to the file within the bucket
            expiration_minutes: URL expiration time in minutes (default: 60)

        Returns:
            Signed URL string
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url

    def generate_signed_url_from_gs(self, gs_url: str, expiration_minutes: int = 60) -> str:
        """
        Generate a signed URL from a gs:// URL.

        Args:
            gs_url: Google Storage URL (e.g., gs://bucket/path/to/file)
            expiration_minutes: URL expiration time in minutes (default: 60)

        Returns:
            Signed URL string
        """
        bucket_name, blob_path = self._parse_gs_url(gs_url)
        return self.generate_signed_url(bucket_name, blob_path, expiration_minutes)

    def _parse_gs_url(self, gs_url: str) -> tuple:
        """Parse a gs:// URL into bucket name and blob path."""
        if not gs_url.startswith("gs://"):
            raise ValueError(f"Invalid GCS URL: {gs_url}")

        path = gs_url[5:]
        parts = path.split("/", 1)

        if len(parts) < 2:
            raise ValueError(f"Invalid GCS URL format: {gs_url}")

        return parts[0], parts[1]

    def _get_path_by_date(self, fecha: datetime = None) -> dict:
        """Generate folder path based on date."""
        if fecha is None:
            fecha = datetime.now()

        year = str(fecha.year)
        month = MESES_ES[fecha.month - 1]

        return {"year": year, "month": month}

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename: replace spaces, remove special chars."""
        name, ext = os.path.splitext(filename)
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        return f"{name}{ext}"

    def upload_file(self, bucket_name: str, local_path: str, folder_prefix: str = "images-vouchers", fecha: datetime = None) -> dict:
        """
        Upload a file to GCS.

        Args:
            bucket_name: GCS bucket name
            local_path: Path to the local file
            folder_prefix: Folder prefix (e.g., "images-vouchers")
            fecha: Date for organizing into folders (defaults to today)

        Returns:
            dict with url, gsUrl, fileName, path, mimeType, fileSize
        """
        if not os.path.exists(local_path):
            raise Exception(f"File not found: {local_path}")

        date_path = self._get_path_by_date(fecha)

        original_name = os.path.basename(local_path)
        timestamp = int(datetime.now().timestamp() * 1000)
        safe_name = f"{timestamp}_{self._sanitize_filename(original_name)}"

        ext = os.path.splitext(local_path)[1].lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.pdf': 'application/pdf',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')

        gcs_path = f"{folder_prefix}/{date_path['year']}/{date_path['month']}/{safe_name}"

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        file_size = os.path.getsize(local_path)
        blob.upload_from_filename(local_path, content_type=content_type)

        blob.cache_control = 'public, max-age=31536000'
        blob.patch()

        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        gs_url = f"gs://{bucket_name}/{gcs_path}"

        print(f"Uploaded: {gcs_path}")

        return {
            "url": public_url,
            "fileGsUrl": gs_url,
            "fileName": safe_name,
            "bucket": bucket_name,
            "path": gcs_path,
            "mimeType": content_type,
            "fileSize": file_size
        }