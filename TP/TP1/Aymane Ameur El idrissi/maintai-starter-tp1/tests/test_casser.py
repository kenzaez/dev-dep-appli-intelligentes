import pytest

# HEADERS = {"X-API-Key": "test-key"} # la clé des tests (conftest.py) ; inutile en TP1, nécessaire en
# TP2
VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}
CAS_REFUSES = [
    # (description, url, corps, code attendu)
    ("valeur absurde", "/v1/predict", {**VALID, "load_pct": 250}, 422),
    ("Champ manquant", "/v1/predict", {**VALID, "load_pct": None}, 422),
    (
        "Texte au lieu d’un nombre",
        "/v1/predict",
        {**VALID, "load_pct": "cinquante"},
        422,
    ),
    ("Champ en trop", "/v1/predict", {**VALID, "load_pct": 50, "pression ": 42}, 422),
    ("Mauvaise route", "/v1/predictt", {**VALID, "load_pct": 50}, 404),
    # ... vos quatre autres cas
]


@pytest.mark.parametrize("description, url, corps, attendu", CAS_REFUSES)
def test_requete_refusee(client, description, url, corps, attendu):
    assert client.post(url, json=corps).status_code == attendu
