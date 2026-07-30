import os
import time
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.dies_task import Attachment
from app.schemas.dies_task import AttachmentResponse

router = APIRouter(tags=["attachments"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


@router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Validate MIME type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image file uploads are supported."
        )

    # 2. Validate file extension strictly
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{file_ext}' is not allowed. Valid extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    # 3. Read content and validate size before saving
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum limit of 5MB."
        )

    # 4. Ensure uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # 5. Create unique filename
    unique_filename = f"{int(time.time() * 1000)}{file_ext}"
    dest_path = os.path.join(upload_dir, unique_filename)

    # 6. Save file to storage securely
    try:
        with open(dest_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file to storage: {str(e)}"
        )


    file_size = len(contents)
    url_path = f"/uploads/{unique_filename}"

    # 7. Insert metadata into DET_ATTACHMENT
    db_attachment = Attachment(
        attachment_name=file.filename,
        mimetype=file.content_type,
        size=file_size,
        file_path=url_path
    )
    
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment

