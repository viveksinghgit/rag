"""Azure Blob Storage client for document management."""
import logging
from pathlib import Path
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional["BlobStorageClient"] = None


class BlobStorageClient:
    def __init__(self):
        from azure.storage.blob import BlobServiceClient
        conn = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={settings.azure_storage_account_name};"
            f"AccountKey={settings.azure_storage_account_key};"
            f"EndpointSuffix=core.windows.net"
        )
        self._svc = BlobServiceClient.from_connection_string(conn)
        self._container = settings.azure_storage_container
        self._ensure_container()

    def _ensure_container(self):
        try:
            self._svc.get_container_client(self._container).get_container_properties()
        except Exception:
            self._svc.create_container(self._container)
            logger.info("Created blob container: %s", self._container)

    def upload(self, name: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        from azure.storage.blob import ContentSettings
        blob = self._svc.get_container_client(self._container).get_blob_client(name)
        blob.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
        logger.info("Uploaded blob: %s (%d bytes)", name, len(data))

    def list_blobs(self) -> List[dict]:
        cc = self._svc.get_container_client(self._container)
        return [
            {
                "name": b.name,
                "size": b.size,
                "last_modified": b.last_modified.isoformat() if b.last_modified else None,
            }
            for b in cc.list_blobs()
        ]

    def download_all_to_dir(self, target_dir: Path) -> int:
        target_dir.mkdir(parents=True, exist_ok=True)
        cc = self._svc.get_container_client(self._container)
        count = 0
        for blob in cc.list_blobs():
            dest = target_dir / blob.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(cc.get_blob_client(blob.name).download_blob().readall())
            count += 1
        logger.info("Downloaded %d blobs to %s", count, target_dir)
        return count


def get_blob_client() -> Optional[BlobStorageClient]:
    global _client
    if _client is None:
        if settings.azure_storage_account_name and settings.azure_storage_account_key:
            try:
                _client = BlobStorageClient()
            except Exception as exc:
                logger.warning("Blob storage unavailable: %s", exc)
    return _client
