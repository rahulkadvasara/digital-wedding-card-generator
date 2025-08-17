"""
File handling utilities for JSON data storage
"""
import json
import os
from typing import Any, List, Dict
import aiofiles


class FileHandler:
    """Utility class for handling JSON file operations"""
    
    async def read_json(self, filepath: str) -> List[Dict[str, Any]]:
        """Read JSON data from file with enhanced error handling"""
        if not os.path.exists(filepath):
            return []
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as file:
                content = await file.read()
                if not content.strip():
                    return []
                
                data = json.loads(content)
                
                # Ensure we return a list
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    print(f"Warning: Unexpected data type in {filepath}, returning empty list")
                    return []
                    
        except json.JSONDecodeError as e:
            print(f"JSON decode error in {filepath}: {e}")
            # Try to backup corrupted file
            try:
                backup_path = f"{filepath}.backup"
                os.rename(filepath, backup_path)
                print(f"Corrupted file backed up to {backup_path}")
            except Exception:
                pass
            return []
        except FileNotFoundError:
            return []
        except PermissionError:
            print(f"Permission denied reading {filepath}")
            return []
        except Exception as e:
            print(f"Unexpected error reading {filepath}: {e}")
            return []
    
    async def write_json(self, filepath: str, data: List[Dict[str, Any]]) -> bool:
        """Write JSON data to file with enhanced error handling"""
        try:
            # Validate input data
            if not isinstance(data, list):
                print(f"Warning: Expected list but got {type(data)} for {filepath}")
                return False
            
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_filepath = f"{filepath}.tmp"
            
            async with aiofiles.open(temp_filepath, 'w', encoding='utf-8') as file:
                json_content = json.dumps(data, indent=2, default=str, ensure_ascii=False)
                await file.write(json_content)
            
            # Windows-compatible atomic rename with retry
            # On Windows, we need to remove the target file first
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    
                    os.rename(temp_filepath, filepath)
                    return True
                    
                except OSError as e:
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt + 1}/{max_retries} for {filepath}: {e}")
                        import time
                        time.sleep(0.1)  # Brief delay before retry
                        continue
                    else:
                        print(f"Final attempt failed for {filepath}: {e}")
                        raise
            
        except PermissionError:
            print(f"Permission denied writing to {filepath}")
            return False
        except OSError as e:
            print(f"OS error writing to {filepath}: {e}")
            return False
        except json.JSONEncodeError as e:
            print(f"JSON encoding error for {filepath}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error writing to {filepath}: {e}")
            # Clean up temp file if it exists
            temp_filepath = f"{filepath}.tmp"
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            return False
    
    async def append_json(self, filepath: str, new_item: Dict[str, Any]) -> bool:
        """Append new item to JSON array file"""
        try:
            print(f"Reading existing data from {filepath}")
            data = await self.read_json(filepath)
            print(f"Current data length: {len(data)}")
            
            data.append(new_item)
            print(f"Appending new item, new length: {len(data)}")
            
            result = await self.write_json(filepath, data)
            print(f"Write result: {result}")
            return result
        except Exception as e:
            print(f"Error appending to {filepath}: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    
    async def update_json_item(self, filepath: str, item_id: str, updated_item: Dict[str, Any], id_field: str = "id") -> bool:
        """Update specific item in JSON array file"""
        try:
            data = await self.read_json(filepath)
            for i, item in enumerate(data):
                if item.get(id_field) == item_id:
                    data[i] = updated_item
                    return await self.write_json(filepath, data)
            return False
        except Exception as e:
            print(f"Error updating item in {filepath}: {e}")
            return False
    
    async def delete_json_item(self, filepath: str, item_id: str, id_field: str = "id") -> bool:
        """Delete specific item from JSON array file"""
        try:
            data = await self.read_json(filepath)
            original_length = len(data)
            data = [item for item in data if item.get(id_field) != item_id]
            
            if len(data) < original_length:
                return await self.write_json(filepath, data)
            return False
        except Exception as e:
            print(f"Error deleting item from {filepath}: {e}")
            return False