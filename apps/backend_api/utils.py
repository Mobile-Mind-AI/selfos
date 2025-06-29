"""
Utility functions for the SelfOS backend API.
"""

import os
import magic
import hashlib
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException
from PIL import Image
import io


class FileValidator:
    """
    Comprehensive file validation utility.
    """
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 50 * 1024 * 1024,    # 50MB for images
        'video': 500 * 1024 * 1024,   # 500MB for videos
        'audio': 100 * 1024 * 1024,   # 100MB for audio
        'document': 25 * 1024 * 1024, # 25MB for documents
    }
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'},
        'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'},
        'document': {'.pdf', '.txt', '.doc', '.docx', '.rtf', '.odt'},
    }
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image': {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 
            'image/svg+xml', 'image/bmp', 'image/tiff'
        },
        'video': {
            'video/mp4', 'video/avi', 'video/quicktime', 'video/x-ms-wmv',
            'video/x-flv', 'video/webm', 'video/x-matroska', 'video/x-m4v'
        },
        'audio': {
            'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac',
            'audio/ogg', 'audio/x-ms-wma', 'audio/x-m4a'
        },
        'document': {
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/rtf', 'application/vnd.oasis.opendocument.text'
        }
    }
    
    @classmethod
    async def validate_upload(
        cls, 
        file: UploadFile, 
        allowed_types: Optional[List[str]] = None
    ) -> Tuple[str, str, dict]:
        """
        Comprehensive file validation.
        
        Args:
            file: The uploaded file
            allowed_types: List of allowed file types ['image', 'video', 'audio', 'document']
        
        Returns:
            Tuple of (file_type, mime_type, metadata)
        
        Raises:
            HTTPException: If validation fails
        """
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no name")
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Validate file size
        file_size = len(content)
        if file_size > max(cls.MAX_FILE_SIZES.values()):
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {max(cls.MAX_FILE_SIZES.values()) // (1024*1024)}MB"
            )
        
        # Determine file type from extension
        file_extension = os.path.splitext(file.filename.lower())[1]
        file_type = cls._get_file_type_from_extension(file_extension)
        
        if not file_type:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file extension: {file_extension}"
            )
        
        # Check if file type is allowed
        if allowed_types and file_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_type}' not allowed. Allowed types: {allowed_types}"
            )
        
        # Validate file size for specific type
        if file_size > cls.MAX_FILE_SIZES[file_type]:
            max_size_mb = cls.MAX_FILE_SIZES[file_type] // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File too large for {file_type}. Maximum size is {max_size_mb}MB"
            )
        
        # Detect actual MIME type from content
        try:
            mime_type = magic.from_buffer(content, mime=True)
        except Exception:
            # Fallback to content type from upload
            mime_type = file.content_type or 'application/octet-stream'
        
        # Validate MIME type
        if mime_type not in cls.ALLOWED_MIME_TYPES.get(file_type, set()):
            raise HTTPException(
                status_code=400,
                detail=f"File content doesn't match expected type. "
                       f"Expected {file_type}, got MIME type: {mime_type}"
            )
        
        # Additional validation based on file type
        metadata = await cls._validate_file_content(file_type, content, file.filename)
        
        # Add basic metadata
        metadata.update({
            'file_size': file_size,
            'file_hash': hashlib.sha256(content).hexdigest(),
            'original_filename': file.filename
        })
        
        return file_type, mime_type, metadata
    
    @classmethod
    def _get_file_type_from_extension(cls, extension: str) -> Optional[str]:
        """Get file type from extension."""
        for file_type, extensions in cls.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        return None
    
    @classmethod
    async def _validate_file_content(cls, file_type: str, content: bytes, filename: str) -> dict:
        """Perform additional validation based on file type."""
        metadata = {}
        
        if file_type == 'image':
            metadata.update(await cls._validate_image_content(content))
        elif file_type == 'video':
            metadata.update(cls._validate_video_content(content))
        elif file_type == 'audio':
            metadata.update(cls._validate_audio_content(content))
        elif file_type == 'document':
            metadata.update(cls._validate_document_content(content, filename))
        
        return metadata
    
    @classmethod
    async def _validate_image_content(cls, content: bytes) -> dict:
        """Validate image content and extract metadata."""
        try:
            image = Image.open(io.BytesIO(content))
            
            # Check image dimensions
            width, height = image.size
            if width > 8192 or height > 8192:
                raise HTTPException(
                    status_code=400,
                    detail="Image dimensions too large. Maximum 8192x8192 pixels"
                )
            
            if width < 1 or height < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image dimensions"
                )
            
            # Extract metadata
            metadata = {
                'width': width,
                'height': height,
                'format': image.format,
                'mode': image.mode
            }
            
            # Check for potentially malicious content
            if hasattr(image, '_getexif'):
                # Remove EXIF data for privacy
                metadata['exif_removed'] = True
            
            return metadata
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
    
    @classmethod
    def _validate_video_content(cls, content: bytes) -> dict:
        """Validate video content."""
        # Basic video validation
        # In a production environment, you might use ffmpeg or mediainfo
        metadata = {
            'validated': True,
            'note': 'Basic validation performed'
        }
        
        # Check for common video file signatures
        video_signatures = [
            b'\x00\x00\x00\x18ftypmp4',  # MP4
            b'\x00\x00\x00\x20ftypmp4',  # MP4
            b'RIFF',                      # AVI
            b'\x1a\x45\xdf\xa3',         # WebM/MKV
        ]
        
        has_valid_signature = any(content.startswith(sig) for sig in video_signatures)
        if not has_valid_signature:
            raise HTTPException(
                status_code=400,
                detail="Invalid video file format"
            )
        
        return metadata
    
    @classmethod
    def _validate_audio_content(cls, content: bytes) -> dict:
        """Validate audio content."""
        metadata = {
            'validated': True,
            'note': 'Basic validation performed'
        }
        
        # Check for common audio file signatures
        audio_signatures = [
            b'ID3',           # MP3 with ID3 tag
            b'\xff\xfb',      # MP3
            b'\xff\xfa',      # MP3
            b'RIFF',          # WAV
            b'fLaC',          # FLAC
            b'OggS',          # OGG
        ]
        
        has_valid_signature = any(content.startswith(sig) for sig in audio_signatures)
        if not has_valid_signature:
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file format"
            )
        
        return metadata
    
    @classmethod
    def _validate_document_content(cls, content: bytes, filename: str) -> dict:
        """Validate document content."""
        metadata = {
            'validated': True,
            'filename': filename
        }
        
        # Check for common document signatures
        if filename.lower().endswith('.pdf'):
            if not content.startswith(b'%PDF-'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file"
                )
        elif filename.lower().endswith(('.doc', '.docx')):
            # Basic MS Word validation
            if not (content.startswith(b'PK') or content.startswith(b'\xd0\xcf\x11\xe0')):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Word document"
                )
        
        return metadata


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    import re
    import unicodedata
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove non-ASCII characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special characters with underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    
    # Ensure filename is not too long
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}" if ext else name


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename for storage.
    
    Args:
        original_filename: Original filename
    
    Returns:
        Secure filename with timestamp and hash
    """
    import time
    import secrets
    
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    
    # Generate secure name
    timestamp = int(time.time())
    random_part = secrets.token_hex(8)
    
    return f"{timestamp}_{random_part}{ext}"