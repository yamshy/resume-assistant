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
