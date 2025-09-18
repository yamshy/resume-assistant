"""
Profile Management Service for Resume Assistant.

Handles loading, saving, and managing user profile data with JSON file storage.
Provides simple file-based persistence for single-user profile management.

Constitutional compliance:
- Single-purpose service (<100 lines)
- File-based JSON storage as per constitutional requirement
- No complex abstractions, direct file operations
- Error handling for common file system issues
"""

import json
import os
from pathlib import Path
from typing import Optional

from models.profile import UserProfile


class ProfileService:
    """
    Service for managing user profile data with JSON file storage.

    Handles loading, saving, and validating profile data stored in
    ~/.resume-assistant/profile.json as per constitutional requirement.
    """

    def __init__(self, profile_path: Optional[str] = None):
        """Initialize profile service with storage path."""
        if profile_path:
            self.profile_path = Path(profile_path)
        else:
            # Use constitutional default: ~/.resume-assistant/profile.json
            home_dir = Path.home()
            self.profile_dir = home_dir / ".resume-assistant"
            self.profile_path = self.profile_dir / "profile.json"

        # Ensure directory exists
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

    async def load_profile(self) -> Optional[UserProfile]:
        """
        Load user profile from JSON file.

        Returns:
            UserProfile if file exists and is valid, None otherwise

        Raises:
            ValueError: If profile file is corrupted or invalid
        """
        if not self.profile_path.exists():
            return None

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            # Validate and parse with pydantic
            return UserProfile.model_validate(profile_data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Profile file is corrupted: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load profile: {e}")

    async def save_profile(self, profile: UserProfile) -> None:
        """
        Save user profile to JSON file.

        Args:
            profile: UserProfile object to save

        Raises:
            ValueError: If profile is invalid or cannot be saved
        """
        try:
            # Convert to dict and serialize
            profile_data = profile.model_dump(mode='json')

            # Write atomically using temp file
            temp_path = self.profile_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            # Atomic move to final location
            temp_path.replace(self.profile_path)

        except Exception as e:
            # Clean up temp file if it exists
            temp_path = self.profile_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            raise ValueError(f"Failed to save profile: {e}")

    async def profile_exists(self) -> bool:
        """Check if profile file exists."""
        return self.profile_path.exists()

    async def delete_profile(self) -> bool:
        """
        Delete the profile file.

        Returns:
            True if file was deleted, False if file didn't exist

        Raises:
            ValueError: If deletion failed
        """
        if not self.profile_path.exists():
            return False

        try:
            self.profile_path.unlink()
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete profile: {e}")

    @staticmethod
    async def validate_profile(profile_data) -> bool:
        """
        Validate profile data structure and completeness.
        
        Args:
            profile_data: Profile data to validate (dict or UserProfile)
            
        Returns:
            True if profile is valid
            
        Raises:
            ValueError: If profile is invalid
        """
        try:
            if isinstance(profile_data, dict):
                UserProfile.model_validate(profile_data)
            elif hasattr(profile_data, 'model_validate'):
                # Already a pydantic model, just check if it's valid
                pass
            else:
                raise ValueError("Profile data must be dict or UserProfile instance")
            return True
        except Exception as e:
            raise ValueError(f"Profile validation failed: {e}")


# Factory function for service creation
def create_profile_service(profile_path: Optional[str] = None) -> ProfileService:
    """
    Create a new Profile Service instance.

    Args:
        profile_path: Optional custom path for profile file

    Returns:
        ProfileService configured with specified or default path
    """
    return ProfileService(profile_path)


__all__ = ["ProfileService", "create_profile_service"]