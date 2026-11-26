# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** …  ·  **Membres :** Kenza Ezzahed  ·  **Date :** 26/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
Client: Docker Engine - Version 29.5.3 (API 1.54, windows/amd64)
Server: Docker Desktop 4.77.0 - Engine 29.5.3 (API 1.54, linux/amd64)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed
```

(Après le sprint 1 — Dockerfile et `.dockerignore` — : `2 failed, 36 passed` ; après le sprint 2 : `38 passed`.)

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le paquet figé et nommé (`maintai:0.4.0`) produit par `docker build` à partir du Dockerfile :
   Linux + Python 3.11 + bibliothèques + code, en lecture seule. Le conteneur est une copie de l'image qui tourne
   (`docker run`), isolée (ses fichiers, son réseau, ses processus). Une image → autant de conteneurs qu'on veut.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche, et Docker réutilise le cache jusqu'à la première couche qui change. Les
   bibliothèques (installation lente, ~9 min ici) changent rarement, le code change souvent : en copiant d'abord
   la seule liste des bibliothèques, une modification du code ne relance pas `pip install`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle (`model.joblib`) est un objet scikit-learn sérialisé : il doit être relu avec la version qui l'a
   écrit (TP4). Avec `>=1.5`, un build futur pourrait installer une autre version, et le modèle monté ne se
   chargerait plus ou donnerait des avertissements / résultats différents. `==` rend aussi le build reproductible.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert des prédictions : on n'y entraîne pas (MLflow), on n'y versionne pas les données (DVC) et on n'y
   teste pas (pytest). Ces outils alourdiraient l'image, rallongeraient le build et augmenteraient la surface
   d'attaque sans rien apporter au service.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# 1. L'image de départ : Linux + Python 3.11, version « slim » (plus légère)
FROM python:3.11-slim

# 2. Le dossier de travail dans l'image
WORKDIR /app

# 3. Les bibliothèques AVANT le code : cette étape lente (pip install) reste en cache
#    tant que requirements-docker.txt ne change pas
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Le code : il change souvent, donc en dernier
COPY maintai ./maintai
COPY ui ./ui

# 5. Où l'application trouve le modèle et les données (montés par volume au lancement)
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Le port de l'API, et la commande lancée par docker run
#    --host 0.0.0.0 : écouter sur toutes les interfaces (127.0.0.1 = ce conteneur seulement)
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 794 s (≈ 13 min 14 s, dont `pip install` 559 s) | 1,13 Go (259 Mo compressés) |
| après une modification de `maintai/predict.py` | 9 s | 1,13 Go |

Que signifie `CACHED` dans le journal du second build ?

```
#6 [2/6] WORKDIR /app                                                CACHED
#7 [3/6] COPY requirements-docker.txt .                              CACHED
#8 [4/6] RUN pip install --no-cache-dir -r requirements-docker.txt   CACHED
#9 [5/6] COPY maintai ./maintai                                      DONE 0.4s
#10 [6/6] COPY ui ./ui                                               DONE 0.1s
```

`CACHED` : Docker a réutilisé la couche du build précédent au lieu de rejouer l'instruction, car rien de ce
dont elle dépend n'a changé. Seules `COPY maintai` (le fichier modifié) et les couches suivantes sont
reconstruites : d'où 9 s au lieu de 13 min.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` (200) |
| `POST /v1/predict` sans clé | `{"detail":"Clé API absente ou invalide"}` (401) |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9976,"alert":true,"threshold":0.3,"model_version":"2026-11-26T09:47:01Z"}` (200) |

Relevé envoyé : `{"temperature_c": 95, "vibration_mm_s": 6, "load_pct": 85, "runtime_hours": 15000}`.
(Avec `releve.json` tel quel, `temperature_c = 500` → 422 : la validation Pydantic refuse > 150 °C.)

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` → `{"status":"ok","model_loaded":false}` ; `/v1/predict` (avec la clé) → 503
`{"detail":"Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"}`.
Le modèle n'est pas dans l'image (`models/` est dans `.dockerignore`) : `/app/models` est vide dans le
conteneur. Au démarrage, `Predictor.load` lève `FileNotFoundError`, l'API démarre quand même sans modèle,
`/health` le signale et `/predict` répond 503.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` : tout semble normal — `Application startup complete.` puis
`Uvicorn running on http://127.0.0.1:8000`. Mais `http://localhost:8002/health` ne répond rien
(curl : `Empty reply from server`). Dans un conteneur, 127.0.0.1 veut dire « ce conteneur seulement » :
Uvicorn n'écoute que sur l'interface de boucle locale du conteneur, alors que Docker transmet le port publié
(8002 → 8000) par l'interface réseau du conteneur. D'où `--host 0.0.0.0` dans le `CMD`.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    volumes:
      - ./models:/app/models:ro        # le modèle vient du PC, en lecture seule

  ui:
    image: maintai:0.4.0               # la même image, une autre commande
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000 # l'API vue depuis ce conteneur : le nom du service
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro            # les données, pour l'onglet « Données »
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       Up 9 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        Up 8 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie pour le service `ui`
dans `compose.yaml` (`environment:`) et lue dans `ui/app.py` par
`os.getenv("MAINTAI_API_URL", "http://localhost:8000")` (valeur par défaut hors Docker).
Avec la clé de `.env`, onglet « Prédiction », « Prédire » (72 °C, 6 mm/s, 85 %, 15 000 h) :
**Probabilité de panne 95 %**, « ALERTE : au-dessus du seuil 0.3 ».

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
> docker compose exec ui python -c "import httpx; print(httpx.get('http://api:8000/health').text)"
{"status":"ok","model_loaded":true}

> docker compose exec ui python -c "import httpx; print(httpx.get('http://localhost:8000/health').text)"
httpx.ConnectError: [Errno 111] Connection refused
```

Dans un conteneur, `localhost` veut toujours dire « ce conteneur-ci ». Depuis `ui`, `localhost:8000` désigne
le conteneur `ui` lui-même, où rien n'écoute sur le port 8000 : connexion refusée. L'API est dans un autre
conteneur ; Compose met les deux services sur le même réseau (`tp6_default`) avec un DNS interne où chacun se
joint par son nom de service : `http://api:8000`. Dans le navigateur, `localhost:8000` marche car c'est le PC,
et `-p 8000:8000` (ports:) publie le port de l'API sur le PC.

**`docker compose down`** : arrête puis supprime les conteneurs `tp6-ui-1` et `tp6-api-1` et le réseau
`tp6_default`. Elle ne supprime ni l'image `maintai:0.4.0` (toujours dans `docker images`), ni les dossiers
montés du PC (`models/`, `data/` restent intacts), ni `.env`.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed in 63.42s (0:01:03)
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le modèle n'entre pas dans l'image : il arrive au lancement par un volume en lecture seule
(`./models:/app/models:ro`), pour pouvoir réentraîner sans reconstruire ni redistribuer l'image. Le
`.dockerignore` laisse dehors le secret (`.env`), les données et le modèle, les fichiers MLflow / DVC et
l'environnement local, pour que l'image ne porte que le code et ses bibliothèques.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (`docker build`) : Linux + Python 3.11 (`FROM python:3.11-slim`), les bibliothèques
   (`COPY requirements-docker.txt` + `RUN pip install`), le code `maintai/` et `ui/` (`COPY`).
   Au lancement (`docker run`) : le modèle `models/` (volume `-v ...:/app/models:ro`), les données `data/`
   (volume), la clé API (`--env-file .env` / `env_file:` dans Compose).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage (registre, collègues, serveur) et chacune de ses couches peut être inspectée
   (`docker history`, extraction des fichiers) : un secret qui y entre est publié. La clé change aussi selon
   l'environnement (dev, prod) sans changer le code. Elle arrive donc au lancement, et `.env` est dans
   `.dockerignore` et `.gitignore`.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Avant : le wheel (code), le modèle + sa version de scikit-learn, les métriques / le run MLflow, la version
   des données (DVC). Docker ajoute l'environnement d'exécution lui-même : le système, la version de Python et
   les bibliothèques figées, dans une image nommée et taguée (`maintai:0.4.0`), plus la façon de la lancer
   (port, volumes, variables d'environnement, `compose.yaml`). Plus besoin de préparer un `.venv` sur le serveur.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? non (ils sont dans `.gitignore`)

## 9. Ce qui reste flou

…
