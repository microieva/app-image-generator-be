from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv() 
from app.core.config import settings


router = APIRouter()

@router.get("/health")
async def health_check():
    """Test connectivity to Hugging Face Space from Render.com"""
    import socket
    import requests
    from urllib.parse import urlparse
    
    results = {
        "space_url": settings.HF_SPACE_URL,
        "token_present": bool(settings.HF_TOKEN),
        "dns_lookup": None,
        "connection_tests": {}
    }
    
    # 1. Test DNS resolution
    parsed_url = urlparse(settings.HF_SPACE_URL)
    hostname = parsed_url.hostname
    try:
        ip_addresses = socket.gethostbyname_ex(hostname)
        results["dns_lookup"] = {
            "hostname": hostname,
            "ips": ip_addresses[2],
            "aliases": ip_addresses[1]
        }
    except Exception as e:
        results["dns_lookup"] = {"error": str(e)}
    
    # 2. Test basic HTTPS connection
    try:
        response = requests.get(
          f"{settings.HF_SPACE_URL}/health",
          headers={
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            #"Accept": "application/json"
          }
        )
        results["connection_tests"]["basic_https"] = {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        results["connection_tests"]["basic_https"] = {"error": str(e)}
    
    # 3. Test with authentication
    if settings.HF_TOKEN:
        try:
            response = requests.get(
                f"{settings.HF_SPACE_URL}/public-health",
                headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
                timeout=10
            )
            results["connection_tests"]["with_auth"] = {
                "status": response.status_code,
                "success": response.status_code == 200
            }
        except Exception as e:
            results["connection_tests"]["with_auth"] = {"error": str(e)}
    
    # 4. Test the generate endpoint (OPTIONS preflight)
    try:
        response = requests.options(
            f"{settings.HF_SPACE_URL}/generate",
            timeout=10
        )
        results["connection_tests"]["options_preflight"] = {
            "status": response.status_code,
            "headers": dict(response.headers)
        }
    except Exception as e:
        results["connection_tests"]["options_preflight"] = {"error": str(e)}
    
    return results