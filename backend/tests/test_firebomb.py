import io, zipfile, pytest
from fastapi import HTTPException
from security.firebomb import check_paste, check_upload

def test_paste_ok():
    check_paste("x" * 100)  # should not raise

def test_paste_too_large():
    with pytest.raises(HTTPException) as exc:
        check_paste("x" * (51 * 1024))
    assert exc.value.status_code == 413

def test_upload_ok():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("hello.py", "print('hello')")
    check_upload("sub.zip", buf.getvalue())

def test_upload_too_large_raw():
    with pytest.raises(HTTPException) as exc:
        check_upload("big.py", b"x" * (11 * 1024 * 1024))
    assert exc.value.status_code == 413

def test_zip_bomb_detected():
    # Build a zip where a single file is 51MB of zeros (compressed well)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bomb.txt", b"\x00" * (51 * 1024 * 1024))
    with pytest.raises(HTTPException) as exc:
        check_upload("bomb.zip", buf.getvalue())
    assert exc.value.status_code == 413
