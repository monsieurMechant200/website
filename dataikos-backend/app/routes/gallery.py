from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
from PIL import Image
import io
from app.models import GalleryItemCreate, GalleryItemInDB
from app.auth import auth_handler
from app.crud import crud_handler
from app.config import settings
from app.utils.supabase_client import db_manager

router = APIRouter(prefix="/api/gallery", tags=["gallery"])

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file: UploadFile) -> Optional[str]:
    """Save uploaded image and return filename"""
    try:
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Create uploads directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Read and compress image if needed
        image_data = file.file.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Resize if too large (max 2000px on largest side)
        max_size = 2000
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save compressed image
        img.save(file_path, 'JPEG' if file_extension == 'jpg' else file_extension.upper(), 
                quality=85, optimize=True)
        
        return unique_filename
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

@router.get("/", response_model=List[GalleryItemInDB])
async def get_gallery_items(
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get gallery items with optional category filter"""
    items = await crud_handler.get_gallery_items(
        skip=skip,
        limit=limit,
        category=category
    )
    
    # Add full URL to images
    for item in items:
        if item.get('image_url') and not item['image_url'].startswith('http'):
            item['image_url'] = f"{settings.FRONTEND_URL}/uploads/{item['image_url']}"
    
    return items

@router.post("/upload")
async def upload_image(
    title: str,
    category: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Upload image to gallery (admin only)"""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start
    
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Check file extension
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Save image
    filename = save_image(file)
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image"
        )
    
    # Create gallery item in database
    gallery_item = GalleryItemCreate(
        title=title,
        category=category,
        description=description,
        image_url=filename
    )
    
    created_item = await crud_handler.create_gallery_item(gallery_item)
    
    if not created_item:
        # Delete uploaded file if database save failed
        try:
            os.remove(os.path.join(settings.UPLOAD_DIR, filename))
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create gallery item"
        )
    
    # Add full URL to response
    created_item['image_url'] = f"{settings.FRONTEND_URL}/uploads/{filename}"
    
    return created_item

@router.delete("/{item_id}")
async def delete_gallery_item(
    item_id: str,
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Delete gallery item (admin only)"""
    # First get item to get filename
    items = await crud_handler.get_gallery_items()
    item = next((i for i in items if i.get('id') == item_id), None)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery item not found"
        )
    
    # Delete from database
    success = await crud_handler.delete_gallery_item(item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete gallery item from database"
        )
    
    # Delete image file
    if item.get('image_url'):
        filename = item['image_url'].split('/')[-1]
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Failed to delete image file: {e}")
    
    return {"message": "Gallery item deleted successfully"}

@router.get("/categories")
async def get_gallery_categories():
    """Get list of gallery categories"""
    items = await crud_handler.get_gallery_items()
    
    # Extract unique categories
    categories = set()
    for item in items:
        if item.get('category'):
            categories.add(item['category'])
    
    return {"categories": list(categories)}

@router.post("/bulk-upload")
async def bulk_upload_images(
    files: List[UploadFile] = File(...),
    category: str = "general",
    current_user: dict = Depends(auth_handler.get_current_admin)
):
    """Bulk upload multiple images (admin only)"""
    uploaded_items = []
    failed_items = []
    
    for file in files:
        try:
            # Check file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            
            if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                failed_items.append({
                    "filename": file.filename,
                    "error": f"File too large (> {settings.MAX_FILE_SIZE_MB}MB)"
                })
                continue
            
            # Check file extension
            if not allowed_file(file.filename):
                failed_items.append({
                    "filename": file.filename,
                    "error": "File type not allowed"
                })
                continue
            
            # Save image
            filename = save_image(file)
            if not filename:
                failed_items.append({
                    "filename": file.filename,
                    "error": "Failed to save image"
                })
                continue
            
            # Create gallery item
            title = file.filename.rsplit('.', 1)[0]
            gallery_item = GalleryItemCreate(
                title=title,
                category=category,
                description=None,
                image_url=filename
            )
            
            created_item = await crud_handler.create_gallery_item(gallery_item)
            
            if created_item:
                created_item['image_url'] = f"{settings.FRONTEND_URL}/uploads/{filename}"
                uploaded_items.append(created_item)
            else:
                # Delete file if database save failed
                try:
                    os.remove(os.path.join(settings.UPLOAD_DIR, filename))
                except:
                    pass
                
                failed_items.append({
                    "filename": file.filename,
                    "error": "Failed to save to database"
                })
                
        except Exception as e:
            failed_items.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "message": f"Uploaded {len(uploaded_items)} of {len(files)} images",
        "uploaded": uploaded_items,
        "failed": failed_items
    }