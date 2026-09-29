"""Tests for synonyms."""
from chatbot.data.synonyms import (
    expand_synonyms,
    find_symptom_key,
    find_symptom_terms,
)


def test_expand_paracetamol():
    result = expand_synonyms("باراسيتامول")
    assert "بنادول" in result
    assert "سيتامول" in result


def test_find_symptom_key():
    assert find_symptom_key("صداع") == "صداع"
    assert find_symptom_key("headache") == "صداع"
    assert find_symptom_key("وجع راس") == "صداع"


def test_find_symptom_terms():
    terms = find_symptom_terms("صداع")
    assert "صداع" in terms
    assert "headache" in terms
