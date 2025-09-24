from datetime import date

from app.router import ModelRouter


def test_entry_level_routing():
    router = ModelRouter()
    model = router.select_model("Junior Developer", {"years_experience": 1})
    assert model == "gpt-4o-mini"


def test_senior_routing_by_keywords():
    router = ModelRouter()
    profile = {"years_experience": 8}
    model = router.select_model("Senior Staff Engineer", profile)
    assert model == "gpt-4o"


def test_executive_routing_requires_years_and_keywords():
    router = ModelRouter()
    profile = {"years_experience": 15}
    model = router.select_model("Chief Technology Officer", profile)
    assert model == "gpt-4o"


def test_senior_routing_uses_dated_experience():
    router = ModelRouter()
    profile = {
        "experience": [
            {
                "company": "Example Corp",
                "start_date": "2010-01-01",
                "end_date": "2019-01-01",
            }
        ]
    }
    model = router.select_model("Senior Software Engineer", profile)
    assert model == "gpt-4o"


def test_executive_routing_uses_dated_experience():
    router = ModelRouter()
    profile = {
        "experiences": [
            {
                "company": "Example Corp",
                "start_date": date(2005, 1, 1),
                "end_date": date(2015, 1, 1),
            },
            {
                "company": "Another Corp",
                "start_date": "2015-01-01",
                "end_date": "2022-01-01",
            },
        ]
    }
    model = router.select_model("Chief Information Officer", profile)
    assert model == "gpt-4o"
