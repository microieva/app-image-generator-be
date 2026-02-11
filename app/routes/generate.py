from datetime import datetime
import os
import sys
import time
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from requests.exceptions import Timeout, RequestException, HTTPError, ConnectionError

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.events.db_events import save_task_to_db
from app.schemas.schemas import GenerateRequest, GenerationResponse
from app.core.database import get_db
from app.core.config import settings
from app.schemas.errors import SpaceAPIError

load_dotenv() 

router = APIRouter()

@router.post("/generate")
async def generate_image(
    generate_request: GenerateRequest,
    db: Session = Depends(get_db),
    timeout:int = settings.REQUEST_TIMEOUT
):
  try:
    if not generate_request.prompt or generate_request.prompt.strip() == "":
      raise HTTPException(
          status_code=400,
          detail={"message": "Prompt cannot be empty"}
      )
        
    if generate_request.width % 8 != 0 or generate_request.height % 8 != 0:
      raise HTTPException(
          status_code=400,
          detail={"message": "Width and height must be divisible by 8"}
      )
    
    if generate_request.prompt:
      health_response = requests.get(
        f"{settings.HF_SPACE_URL}/health",
        headers={
          "Authorization": f"Bearer {settings.HF_TOKEN}"
        }
      )
    
      if health_response.status_code != 200:
        raise SpaceAPIError(
            f"Space health check failed. Status: {health_response.status_code}"
        )
    
    task_id = f"{int(time.time())}"
    task_data = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "prompt": generate_request.prompt
    }
    
    space_request = {
        "task_id": task_id,
        "prompt": generate_request.prompt,
        "negative_prompt": generate_request.negative_prompt or "", 
        "num_inference_steps": generate_request.num_inference_steps or 20,
        "guidance_scale": generate_request.guidance_scale or 7.5,
        "width": generate_request.width or 512,
        "height": generate_request.height or 512,
        "seed": generate_request.seed or None
    }
        
    space_request = {k: v for k, v in space_request.items() if v is not None}
    
    generate_response = requests.post(
      f"{settings.HF_SPACE_URL}/generate",
      json=space_request,
      headers={
          "Content-Type": "application/json",
          "Authorization": f"Bearer {settings.HF_TOKEN}"
      },
      timeout=timeout
    )

    response_json = generate_response.json()

    response_data = {
        "status": response_json.get('status', 'unknown'),
        "task_id": response_json.get('task_id', task_id), 
        "message": response_json.get('message', ''),
        "created_at": datetime.now().isoformat()
    }

    save_task_to_db(task_data, db)

    return GenerationResponse(**response_data)
  
  except Timeout as e:
    raise SpaceAPIError(f"Space API request timed out after {timeout} seconds")
  
  except HTTPError as e:
    status_code = e.response.status_code if hasattr(e, 'response') else None
    response_text = e.response.text if hasattr(e, 'response') else str(e)
    
    if status_code == 401:
        raise SpaceAPIError("Invalid or expired authentication token")
    elif status_code == 403:
        raise SpaceAPIError("Access forbidden to Space API")
    elif status_code == 404:
        raise SpaceAPIError("Space API endpoint not found")
    elif status_code == 429:
        raise SpaceAPIError("Rate limit exceeded for Space API")
    elif 500 <= status_code < 600:
        raise SpaceAPIError(f"Space API server error: {status_code}")
    else:
        raise SpaceAPIError(f"Space API HTTP error {status_code}: {response_text}")
  
  except ConnectionError as e:
      raise SpaceAPIError(f"Failed to connect to Space API: {str(e)}")
      
  except RequestException as e:
      raise SpaceAPIError(f"Space API request failed: {str(e)}")
      
  except ValueError as e:
      raise SpaceAPIError("Invalid JSON response from Space API")
      
  except Exception as e:
      raise SpaceAPIError(f"Unexpected error: {str(e)}")

