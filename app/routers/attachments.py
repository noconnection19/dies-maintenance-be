import os
import time
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.dies_task import Attachment
from app.schemas.dies_task import AttachmentResponse

router = APIRouter(tags=["attachments"])

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validate file content type is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image file uploads are supported."
        )

    # 2. Ensure uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # 3. Create unique filename using timestamp
    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        # Fallback extension if none is provided
        file_ext = ".jpg"
        
    unique_filename = f"{int(time.time() * 1000)}{file_ext}"
    dest_path = os.path.join(upload_dir, unique_filename)

    # 4. Save file to storage
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to storage: {str(e)}"
        )

    # 5. Get file size and compile public URL path
    file_size = os.path.getsize(dest_path)
    url_path = f"/uploads/{unique_filename}"

    # 6. Insert metadata into DET_ATTACHMENT
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
