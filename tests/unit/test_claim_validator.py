import pytest

from app.agents.validator import ClaimValidator


@pytest.mark.asyncio
async def test_claim_validation_success() -> None:
    validator = ClaimValidator()
    result = await validator.validate_claim(
        claim="5 years of Python experience",
        source_profile={"skills": [{"name": "Python", "years": 5}]},
    )
    assert result.confidence > 0.9
    assert not result.issues


@pytest.mark.asyncio
async def test_claim_validation_failure() -> None:
    validator = ClaimValidator()
    result = await validator.validate_claim(
        claim="10 years of Rust experience",
        source_profile={"skills": [{"name": "Python", "years": 5}]},
    )
    assert result.confidence < 0.5
    assert result.issues
