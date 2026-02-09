from pydantic import BaseModel
from typing import Optional
from typing import Optional, Dict, Any
from datetime import datetime

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    num_inference_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5
    width: int = 512
    height: int = 512
    seed: Optional[int] = None


class ImagesParams(BaseModel):
    page: int = 1
    limit: int = 12 
    task_id: Optional[str] = None


class GenerationStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'processing', 'completed', 'cancelled', 'error'
    progress: Optional[float] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class GenerationResult(BaseModel):
    task_id: str
    image_data: str        
    prompt: str
    total_inference_time: Optional[float] = None
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class ImageResponse(BaseModel):
    id: int
    task_id: str
    image_url: str
    prompt: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class ImagesSliceResponse(BaseModel):
    length: int
    slice: Optional[list[ImageResponse]] = None

class TaskData(BaseModel):
    task_id: str
    progress: int
    prompt: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class TasksResponse(BaseModel):
    total_tasks: int
    tasks: Optional[list[TaskData]] = None
    class Config:
        from_attributes = True

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    created_at: datetime
    cancelled: bool
    prompt: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class GenerationResponse(BaseModel):
    status:str
    task_id:str
    message:str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  
        }

class CancellationResponse(BaseModel):
    success: bool
    message: str
    task_id: str

class DeletionResponse(BaseModel):
    success: bool
    message: str