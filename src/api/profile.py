"""
Profile management endpoints for Resume Assistant API.

Handles user profile operations including loading, saving, and validation
using the ProfileService with constitutional file-based storage.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to ProfileService for operations
- Structured error responses
- Standard REST patterns
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models.profile import UserProfile
from services.profile_service import create_profile_service


class ErrorResponse(BaseModel):
    """Error response model for API errors."""

    error: str
    timestamp: str


# Create router for profile endpoints
router = APIRouter(prefix="/profile", tags=["profile"])

# Initialize profile service
profile_service = create_profile_service()


@router.get("", response_model=UserProfile)
async def get_profile() -> UserProfile:
    """
    Get current user profile.

    Returns the user's profile data if it exists.

    Returns:
        UserProfile: The user's profile data

    Raises:
        HTTPException: 404 if profile doesn't exist, 500 for other errors
    """
    try:
        profile = await profile_service.load_profile()

        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        return profile

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Profile file error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load profile: {str(e)}",
        ) from e


@router.put("", response_model=UserProfile)
async def update_profile(profile: UserProfile) -> UserProfile:
    """
    Create or update user profile.

    Saves the provided profile data to storage, creating or overwriting
    the existing profile file.

    Args:
        profile: User profile data to save

    Returns:
        UserProfile: The saved profile data

    Raises:
        HTTPException: If profile validation or saving fails
    """
    try:
        # Save profile using service
        await profile_service.save_profile(profile)

        return profile

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Profile validation error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}",
        ) from e


@router.delete("")
async def delete_profile():
    """
    Delete user profile.

    Removes the profile file from storage. This operation cannot be undone.

    Returns:
        204 No Content on successful deletion

    Raises:
        HTTPException: 404 if profile doesn't exist, 500 for other errors
    """
    try:
        deleted = await profile_service.delete_profile()

        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Profile deletion error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}",
        ) from e


__all__ = ["router", "ErrorResponse"]
