import io, zipfile, tarfile
from fastapi import HTTPException

MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10MB
MAX_PASTE_BYTES = 50 * 1024            # 50KB
MAX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50MB
MAX_RATIO = 100

def check_paste(code: str) -> None:
    if len(code.encode()) > MAX_PASTE_BYTES:
        raise HTTPException(413, "Code paste exceeds 50KB limit")

def check_upload(filename: str, content: bytes) -> None:
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds 10MB limit")
    name = filename.lower()
    if name.endswith(".zip"):
        _check_zip(content)
    elif name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2")):
        _check_tar(content)

def _check_zip(content: bytes) -> None:
    compressed = len(content)
    decompressed = 0
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
            decompressed += info.file_size
            _assert_limits(compressed, decompressed)

def _check_tar(content: bytes) -> None:
    compressed = len(content)
    decompressed = 0
    with tarfile.open(fileobj=io.BytesIO(content)) as tf:
        for member in tf.getmembers():
            decompressed += member.size
            _assert_limits(compressed, decompressed)

def _assert_limits(compressed: int, decompressed: int) -> None:
    if decompressed > MAX_DECOMPRESSED_BYTES:
        raise HTTPException(413, "Archive expands beyond 50MB limit")
    if compressed > 0 and decompressed / compressed > MAX_RATIO:
        raise HTTPException(413, "Suspicious compression ratio — possible zip bomb")
