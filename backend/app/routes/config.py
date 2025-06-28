"""
Configuration Management Routes

API endpoints for reading and updating trading strategy configuration.
"""

import os
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter()

# Path to the configuration file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "config.yaml")

class ConfigUpdate(BaseModel):
    """Model for configuration update requests"""
    data_mode: Optional[str] = None
    initial_capital: Optional[float] = None
    strategies: Optional[Dict[str, bool]] = None
    allocation: Optional[Dict[str, float]] = None
    wheel_symbols: Optional[List[str]] = None
    rotator_symbols: Optional[List[str]] = None
    simulation: Optional[Dict[str, Any]] = None

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(CONFIG_PATH, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except yaml.YAMLError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing configuration: {str(e)}")

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to YAML file"""
    try:
        with open(CONFIG_PATH, 'w') as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

@router.get("/config")
async def get_config():
    """
    Get current configuration settings
    
    Returns the current config.yaml contents as JSON.
    """
    return load_config()

@router.put("/config")
async def update_config(config_update: ConfigUpdate):
    """
    Update configuration settings
    
    Merges provided fields into existing configuration and saves to file.
    """
    # Load existing config
    current_config = load_config()
    
    # Update only provided fields
    update_data = config_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if isinstance(value, dict) and key in current_config and isinstance(current_config[key], dict):
            # For nested dictionaries, merge rather than replace
            current_config[key].update(value)
        else:
            current_config[key] = value
    
    # Validate allocation percentages if updated
    if 'allocation' in update_data:
        allocation = current_config.get('allocation', {})
        total = sum(allocation.values())
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise HTTPException(
                status_code=400, 
                detail=f"Allocation percentages must sum to 1.0, got {total}"
            )
    
    # Save updated config
    save_config(current_config)
    
    return {
        "message": "Configuration updated successfully",
        "config": current_config
    }

@router.get("/config/symbols")
async def get_available_symbols():
    """
    Get lists of available symbols for strategies
    
    Returns commonly used symbols for wheel and rotator strategies.
    """
    return {
        "wheel_symbols": ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "TSLA"],
        "rotator_symbols": ["BTC", "ETH", "SOL", "ADA", "DOT", "MATIC", "AVAX"],
        "data_modes": ["mock", "live"]
    }