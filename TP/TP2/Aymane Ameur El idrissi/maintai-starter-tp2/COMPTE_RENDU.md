# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** AMEUR EL IDRISSI Aymane   ·  **Date :** 15/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| `POST /v1/predict` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"runtime_hours":5000}` | champ manquant (`load_pct`) | **422** | **422** |
| `POST /v1/predict` avec `{"temperature_c":500,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | valeur absurde | **422** | **422** |
| `POST /v1/predict` avec `{"temperature_c":"cinquante","vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | texte au lieu d'un nombre | **422** | **422** |
| `POST /v1/predict` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000,"pressure":2}` | champ en trop (`pressure`) | **422** | **422** |
| `POST /v1/predictt` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | mauvaise route | **404** | **404** |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

…

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
===================================================================== 19 passed, 1 warning in 3.03s ======================================================================
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

Ce décorateur permet d'exécuter la même fonction de test avec plusieurs jeux
   de paramètres. Il évite de dupliquer le code de test tout en vérifiant
   plusieurs comportements ou données d'entrée.

   Pour `test_requete_refusee`, pytest compte **5 tests**, car `CAS_REFUSES`
   contient cinq tuples. Chaque tuple produit un cas de test indépendant,
   généralement affiché avec un identifiant entre crochets.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
All checks passed!
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff check .` analyse statiquement les fichiers Python du projet : il
   recherche des erreurs de style, des imports inutilisés et certaines erreurs
   de qualité ou de programmation, sans exécuter les tests.

   `python -m pytest` exécute les fonctions de test du projet et vérifie le
   comportement réel du code, notamment les réponses HTTP et les codes de
   statut de l'API. Ruff contrôle donc la qualité du code source, tandis que
   pytest contrôle son fonctionnement.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
=============================================================== 18 passed, 1 warning in 3.48s ================================================================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

…

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    configured_key = get_settings().api_key
    if configured_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API serveur non configurée",
        )

    if x_api_key is None or not secrets.compare_digest(x_api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Deux tests échouent : `test_missing_key_is_rejected` et
`test_wrong_key_is_rejected`. Le routeur n'utilise pas encore
`require_api_key`, donc les requêtes sans clé ou avec une fausse clé atteignent
la route et reçoivent `200` au lieu de `401`.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
============================== 18 passed in 3.10s ==============================
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Sans clé, la dépendance d'authentification est exécutée avant la validation du
corps : la requête est donc refusée en `401`. Avec la bonne clé, le corps est
validé et la température `500 °C` dépasse la limite de `150 °C`, ce qui donne
`422`.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

Le code obtenu est `500` avec
`{"detail":"Clé API serveur non configurée"}`. Sans `--env-file .env`, la
variable `MAINTAI_API_KEY` n'est pas chargée : le serveur ne possède aucune clé
de référence. Il s'agit donc d'une erreur de configuration serveur, et non
d'une clé client absente ou incorrecte.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
(collez ici)
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | |
| 500 °C, bonne clé | |
| relevé normal, fausse clé | |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

…

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

…

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

…

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
(collez ici)
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   …
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   …
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   …
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   …
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   …

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

…
