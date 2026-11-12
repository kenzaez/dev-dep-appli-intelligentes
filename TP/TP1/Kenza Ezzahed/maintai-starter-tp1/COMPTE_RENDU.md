# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G3 · **Membres :** Kenza Ezzahed · **Date :** 22/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Les sorties ci-dessous sont celles observées dans l'environnement du projet.

---

## 1. Mise en place

Au premier essai, `pytest` n'était pas installé dans le Python global. La commande `python -m pytest` a donc affiché :

```
No module named pytest
```

Après installation des dépendances dans l'environnement virtuel, les tests ont pu être exécutés depuis `TP/TP1/Kenza Ezzahed/maintai-starter-tp1`.

Dans le squelette où `SensorReading` ne déclare aucun champ et conserve `extra="forbid"`, les quatre tests qui peuvent passer sont `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`. Les deux tests qui attendent 422 passent à tort : tous les champs envoyés dans le JSON sont alors considérés comme des champs supplémentaires et rejetés. Ces réponses ne prouvent donc ni que la température est bornée, ni qu'un champ obligatoire est correctement déclaré. La validation des vraies bornes et champs requis est vérifiée une fois le schéma complété.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---:|---:|---:|---|
| `temperature_c` | float | -40 °C | 150 °C | Enveloppe plausible de mesure industrielle, du froid ambiant à une température moteur très élevée. La borne haute est une limite de validation, pas une consigne de sécurité. |
| `vibration_mm_s` | float | 0 mm/s | 30 mm/s | La vitesse vibratoire mesurée est positive. 30 mm/s couvre un état très sévère mais mesurable ; ce n'est pas un niveau de fonctionnement acceptable. |
| `load_pct` | float | 0 % | 100 % | Le pourcentage est défini par rapport à la charge nominale. Une surcharge demanderait de redéfinir la mesure et sa limite. |
| `runtime_hours` | float | 0 h | 20 000 h | Un compteur de durée écoulée ne peut pas être négatif. La limite supérieure est l'horizon couvert par le projet et le modèle, pas une durée de vie physique universelle. |

Lors du premier lancement des tests avec les bornes laissées sous forme de `...`, pytest n'a pas pu collecter `test_api.py`. Pydantic a signalé une `SchemaError` sur `vibration_mm_s`, avec `TypeError: must be real number, not ellipsis`. C'est utile : le schéma invalide est détecté immédiatement, avant le traitement des requêtes.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Corps de la fonction :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Modèle de prédiction indisponible.")
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Nous répondons **503 Service Unavailable** plutôt que 500, car le service fonctionne mais sa dépendance nécessaire à la prédiction (le modèle) est absente. Le code 503 décrit une indisponibilité potentiellement temporaire et permet au client ou à la supervision de réessayer ; le code 500 suggérerait une erreur inattendue du serveur.

Le modèle est chargé une seule fois au démarrage par le `lifespan` de FastAPI. Cela évite de relire le fichier et de reconstruire le prédicteur à chaque requête, réduit le coût et la latence, et garantit que les requêtes d'une même instance utilisent le même modèle.

## 4. Les tests

Dernière ligne de `python -m pytest -q` à la fin du TP :

```
13 passed, 1 warning in 14.56s
```

## 5. L'API en marche

Après génération des données et entraînement du modèle, les réponses observées étaient :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c":72.5,"vibration_mm_s":6.1,"load_pct":85,"runtime_hours":15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-22T11:49:29Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, les bornes sont visibles dans le schéma de requête `SensorReading`, dans la documentation OpenAPI de `POST /v1/predict` (contraintes `minimum` et `maximum`).

## 6. Questions de compréhension

1. **REST et FastAPI : quelle est la différence ?**  
   REST est un style d'architecture et de conventions pour concevoir des API HTTP. FastAPI est un framework Python qui permet de construire ces API, de valider leurs données et de générer leur documentation.

2. **Le schéma Pydantic sert à trois choses. Lesquelles ?**  
   Il valide les entrées (types, champs requis et bornes), convertit les données reçues vers les types Python attendus, et décrit les modèles pour générer le schéma OpenAPI et `/docs`.

3. **Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**  
   `localhost` désigne la machine locale, `8000` le port du serveur, et `/v1/predict` le chemin de la route de prédiction versionnée.

4. **Pourquoi `/v1` dans l'adresse ?**  
   Pour identifier la version du contrat de l'API. Une évolution incompatible peut être publiée sous une nouvelle version sans casser immédiatement les clients de `/v1`.

5. **Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**  
   `maintai.api.main` est le chemin Python du module à importer ; `app` est l'objet ASGI FastAPI défini dans ce module et servi par Uvicorn.

## 7. Le rendu Git

- ADR : [docs/adr/000-modele.md](docs/adr/000-modele.md) (choix du modèle) et [docs/adr/002-validation.md](docs/adr/002-validation.md) (validation et 503)
- Lien de la pull request : à compléter après sa création.
- Le tag `tp1` existe sur GitHub : à vérifier.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ? À compléter après la relecture.

## 8. Ce qui reste flou

Les bornes supérieures de `load_pct` et `runtime_hours` dépendent de la définition exacte du capteur et du matériel suivi. Si l'application doit accepter les surcharges ou suivre des machines au-delà de 20 000 heures, il faudra ajuster les limites et vérifier que ces entrées restent pertinentes pour le modèle.
