# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  ·  **Membres :** Aymane Ameur El idrissi  ·  **Date :** 22/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Résultat de validation disponible dans l'environnement :

```
============================== 13 passed, 1 warning in 3.77s ==============================
```

La sortie intermédiaire correspondant exactement au squelette avant les
implémentations n'a pas été conservée ; la sortie ci-dessus est celle de la
version finale du TP.

Dans `tests/test_api.py`, les quatre tests qui passent déjà avec le squelette sont :

- `test_health` ;
- `test_missing_field_is_rejected` ;
- `test_503_when_model_missing` ;
- `test_openapi_documents_predict`.

Les deux tests qui attendent 422 (`test_out_of_range_value_is_rejected` et
`test_missing_field_is_rejected`) peuvent passer pour une mauvaise raison avant
la déclaration des champs. Comme `extra="forbid"` interdit les champs inconnus,
les clés envoyées par le client sont alors rejetées comme des champs
supplémentaires, au lieu que la valeur soit contrôlée par une borne `ge` ou
`le`, ou qu'il soit réellement détecté qu'un champ obligatoire manque. Après
avoir déclaré les quatre champs, le 422 de la température à 500 provient bien
de la contrainte `le=150`, et celui du relevé incomplet provient de l'absence de
`load_pct`.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | `-40` | `150` | Plage réaliste de température d'un équipement industriel : du froid extrême à une température moteur très élevée. |
| `vibration_mm_s` | `float` | `0` | `100` | Une vibration est positive ; 100 mm/s couvre une vibration exceptionnellement forte tout en rejetant les valeurs absurdes. |
| `load_pct` | `float` | `0` | `100` | Une charge est exprimée en pourcentage : 0 % signifie aucune charge et 100 % la charge nominale maximale. |
| `runtime_hours` | `float` | `0` | `100000` | Un compteur d'heures ne peut pas être négatif ; 100 000 h couvre plusieurs années d'exploitation continue. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
Les tests qui vérifiaient les prédictions et les bornes échouaient alors que
les champs et les contraintes n'étaient pas encore correctement définis. C'est
un bon signe : les tests détectent précisément le comportement restant à
implémenter, au lieu de masquer une erreur silencieuse.
```

Après la déclaration des champs avec ces contraintes, l'ensemble des tests
relatifs au schéma passe.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Modele non chargé")
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Le code 503 (*Service Unavailable*) indique que le serveur fonctionne, mais
qu'il ne peut momentanément pas fournir le service car sa dépendance (le
modèle) n'est pas disponible. Un code 500 signalerait plutôt une erreur
interne inattendue de l'application.

Le modèle est chargé une seule fois au démarrage dans la fonction `lifespan`.
Cela évite de relire le fichier et de reconstruire l'objet de prédiction à
chaque requête, ce qui réduit fortement la latence et la consommation de
ressources. L'objet chargé est ensuite réutilisé par les requêtes.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
============================== 13 passed, 1 warning in 3.77s ==============================
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).


| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | **200** | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | **200** | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-22T12:07:01Z"}` |
| `POST /v1/predict` avec une température de 500 | **422** | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | **404** | `{"detail":"Not Found"}` |

Dans `/docs`, les bornes apparaissent dans le schéma du corps de la requête
`SensorReading`, dans la documentation générée par OpenAPI. Elles sont aussi
visibles dans la description de chaque propriété du modèle et lors de
l'affichage des erreurs de validation.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style architectural pour concevoir des services accessibles par
   HTTP, avec des ressources, des URI et des méthodes comme GET ou POST.
   FastAPI est un framework Python qui permet d'implémenter une API REST (entre
   autres) et d'en générer automatiquement la validation et la documentation.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide les données entrantes et leurs bornes, documente automatiquement le
   contrat OpenAPI de l'API, et sérialise/désérialise les données Python et JSON
   (notamment pour la réponse).
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` désigne la machine locale, `8000` le port d'écoute du serveur
   Uvicorn, et `/v1/predict` le chemin de la ressource de prédiction dans la
   version 1 de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   `/v1` versionne le contrat de l'API. Une future version incompatible pourra
   être exposée sous `/v2` sans casser les clients utilisant `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le chemin Python du module qui contient l'application,
   et `app` est l'objet `FastAPI` que Uvicorn doit charger.

## 7. Le rendu Git

- Lien de la pull request : Non disponible dans l'environnement local fourni.
- Le tag `tp1` existe sur GitHub : Non vérifiable depuis cet environnement.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Non disponible dans l'environnement local fourni.

## 8. Ce qui reste flou

Le seul point restant à compléter est la partie liée au rendu Git (URL de la
pull request, existence du tag et relecture), car ce dossier n'est pas un dépôt
Git local et aucun lien GitHub n'a été fourni. Les tests affichent également un
avertissement de dépréciation provenant de `starlette.testclient` concernant
`httpx`; il n'empêche pas les 13 tests de réussir, mais pourra être traité lors
d'une mise à jour des dépendances.
