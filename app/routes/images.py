from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from app.models.db_models import Image
from app.schemas.schemas import ImagesParams, ImagesSliceResponse
from app.core.database import get_db

router = APIRouter()

@router.get("/images", response_model=ImagesSliceResponse)
async def get_images(
    images_params: ImagesParams = Depends(),  
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Image).order_by(Image.created_at.desc())
        
        if images_params.task_id:
            query = query.filter(Image.task_id == images_params.task_id)
        
        total_count = query.count()
        offset = (images_params.page - 1) * images_params.limit 
        images_slice = query.offset(offset).limit(images_params.limit).all() 
        
        images_list = []
        for image in images_slice:
            images_list.append({
                "id":image.id,
                "task_id": image.task_id,
                "prompt": image.prompt,
                "image_url": image.image_data,
                "created_at": image.created_at.isoformat() if image.created_at else None
            })
        
        return ImagesSliceResponse(
            length=total_count,
            slice=images_list
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving images: {str(e)}")