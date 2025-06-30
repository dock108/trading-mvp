"""
File Management Routes

API endpoints for uploading and downloading configuration and data files.
"""

import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import yaml

router = APIRouter()

# Base paths for file operations
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CONFIG_PATH = os.path.join(BASE_PATH, "config", "config.yaml")
DATA_DIR = os.path.join(BASE_PATH, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

def ensure_directory_exists(path: str):
    """Ensure directory exists, create if not"""
    os.makedirs(path, exist_ok=True)

def validate_yaml_file(file_content: bytes) -> bool:
    """Validate that file content is valid YAML"""
    try:
        yaml.safe_load(file_content.decode('utf-8'))
        return True
    except yaml.YAMLError:
        return False

@router.post("/upload/config")
async def upload_config(file: UploadFile = File(...)):
    """
    Upload a new configuration file
    
    Replaces the current config.yaml with the uploaded file.
    Validates YAML format before saving.
    """
    # Validate file type
    if not file.filename.endswith(('.yaml', '.yml')):
        raise HTTPException(
            status_code=400, 
            detail="File must be a YAML file (.yaml or .yml extension)"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Validate YAML format
        if not validate_yaml_file(content):
            raise HTTPException(
                status_code=400,
                detail="Invalid YAML format"
            )
        
        # Backup existing config
        if os.path.exists(CONFIG_PATH):
            backup_path = CONFIG_PATH + ".backup"
            shutil.copy2(CONFIG_PATH, backup_path)
        
        # Save new config
        with open(CONFIG_PATH, 'wb') as f:
            f.write(content)
        
        return {
            "message": "Configuration file uploaded successfully",
            "filename": file.filename,
            "size": len(content)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading configuration: {str(e)}"
        )

@router.post("/upload/data")
async def upload_data_files(files: List[UploadFile] = File(...)):
    """
    Upload data files to the cache directory
    
    Accepts multiple files and saves them to the data cache.
    """
    # Ensure cache directory exists
    ensure_directory_exists(CACHE_DIR)
    
    uploaded_files = []
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            
            # Determine save path
            # Save to appropriate subdirectory based on file type
            if 'crypto' in file.filename.lower():
                save_dir = os.path.join(CACHE_DIR, "crypto")
            elif any(ext in file.filename.lower() for ext in ['etf', 'stock', 'spy', 'qqq']):
                save_dir = os.path.join(CACHE_DIR, "etf")
            else:
                save_dir = CACHE_DIR
            
            ensure_directory_exists(save_dir)
            save_path = os.path.join(save_dir, file.filename)
            
            # Save file
            with open(save_path, 'wb') as f:
                f.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": len(content),
                "path": save_path
            })
            
        except Exception as e:
            uploaded_files.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "message": f"Uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }

@router.get("/download/config")
async def download_config():
    """
    Download the current configuration file
    
    Returns the config.yaml file for download.
    """
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=404, detail="Configuration file not found")
    
    return FileResponse(
        path=CONFIG_PATH,
        media_type='application/x-yaml',
        filename="config.yaml"
    )

@router.get("/download/data")
async def download_data_file(filename: str):
    """
    Download a specific data file from cache
    
    Args:
        filename: Name of the file to download
    """
    # Search for file in cache directories
    possible_paths = [
        os.path.normpath(os.path.join(CACHE_DIR, filename)),
        os.path.normpath(os.path.join(CACHE_DIR, "crypto", filename)),
        os.path.normpath(os.path.join(CACHE_DIR, "etf", filename)),
        os.path.normpath(os.path.join(DATA_DIR, filename))
    ]
    
    file_path = None
    for path in possible_paths:
        # Ensure the path is within the allowed directories
        if path.startswith(CACHE_DIR) or path.startswith(DATA_DIR):
            if os.path.exists(path):
                file_path = path
                break
    
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail=f"Data file '{filename}' not found or access denied"
        )
    
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail=f"Data file '{filename}' not found"
        )
    
    # Determine media type based on file extension
    if filename.endswith('.csv'):
        media_type = 'text/csv'
    elif filename.endswith('.json'):
        media_type = 'application/json'
    elif filename.endswith(('.yaml', '.yml')):
        media_type = 'application/x-yaml'
    else:
        media_type = 'application/octet-stream'
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

@router.get("/list/data")
async def list_data_files():
    """
    List available data files in cache
    
    Returns a list of files available for download.
    """
    files = []
    
    # Scan cache directories
    cache_dirs = [
        ("root", CACHE_DIR),
        ("crypto", os.path.join(CACHE_DIR, "crypto")),
        ("etf", os.path.join(CACHE_DIR, "etf"))
    ]
    
    for dir_name, dir_path in cache_dirs:
        if os.path.exists(dir_path):
            try:
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        files.append({
                            "name": filename,
                            "directory": dir_name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
            except PermissionError:
                continue
    
    return {
        "files": files,
        "count": len(files)
    }