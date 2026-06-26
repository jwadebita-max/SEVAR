from pathlib import Path
from uuid import uuid4

from flask import current_app, url_for
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def save_upload(file_storage, folder):
    if not file_storage or not file_storage.filename:
        raise ValueError("File is required")
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only jpg, jpeg, png and webp files are allowed")
    filename = f"{uuid4().hex}.{ext}"
    relative = f"uploads/{folder}/{filename}"
    destination = Path(current_app.static_folder) / "uploads" / folder / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(destination)
    return relative, url_for("static", filename=relative)
