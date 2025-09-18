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
from pydantic import BaseModel
from typing import Optional

from models.profile import UserProfile
from services.profile_service import create_profile_service


class ProfileResponse(BaseModel):
    """Response model for profile operations."""
    profile: Optional[UserProfile] = None
    message: str
    profile_exists: bool


class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates."""
    profile: UserProfile


# Create router for profile endpoints
router = APIRouter(prefix="/profile", tags=["profile"])

# Initialize profile service
profile_service = create_profile_service()


@router.get("", response_model=ProfileResponse)
async def get_profile() -> ProfileResponse:
    """
    Get current user profile.

    Returns the user's profile data if it exists, or indicates
    that no profile has been created yet.

    Returns:
        ProfileResponse: Profile data and status
    """
    try:
        profile = await profile_service.load_profile()

        if profile is None:
            return ProfileResponse(
                profile=None,
                message="No profile found. Please create a profile first.",
                profile_exists=False
            )

        return ProfileResponse(
            profile=profile,
            message="Profile loaded successfully",
            profile_exists=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Profile file error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load profile: {str(e)}"
        )


@router.put("", response_model=ProfileResponse)
async def update_profile(request: ProfileUpdateRequest) -> ProfileResponse:
    """
    Create or update user profile.

    Saves the provided profile data to storage, creating or overwriting
    the existing profile file.

    Args:
        request: Profile update request with new profile data

    Returns:
        ProfileResponse: Confirmation of profile save

    Raises:
        HTTPException: If profile validation or saving fails
    """
    try:
        # Save profile using service
        await profile_service.save_profile(request.profile)

        return ProfileResponse(
            profile=request.profile,
            message="Profile saved successfully",
            profile_exists=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Profile validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save profile: {str(e)}"
        )


@router.delete("", response_model=ProfileResponse)
async def delete_profile() -> ProfileResponse:
    """
    Delete user profile.

    Removes the profile file from storage. This operation cannot be undone.

    Returns:
        ProfileResponse: Confirmation of deletion

    Raises:
        HTTPException: If deletion fails
    """
    try:
        deleted = await profile_service.delete_profile()

        if not deleted:
            return ProfileResponse(
                profile=None,
                message="No profile found to delete",
                profile_exists=False
            )

        return ProfileResponse(
            profile=None,
            message="Profile deleted successfully",
            profile_exists=False
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Profile deletion error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


__all__ = ["router", "ProfileResponse", "ProfileUpdateRequest"]