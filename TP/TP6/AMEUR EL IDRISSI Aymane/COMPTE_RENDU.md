# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G1  ·  **Membres :** Aymane Ameur El idrissi  ·  **Date :** 26/11/2026 11:30

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
Client: Version 29.8.2 (windows/amd64)
Server: Docker Desktop 4.95.0 (242831), Engine Version 29.8.2 (linux/amd64)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
.\.venv\Scripts\python.exe -m pytest
================== 2 failed, 36 passed, 4 warnings in 57.60s ==================
```

Les deux échecs restants concernent le sprint 2 : le montage du modèle dans `compose.yaml` est encore un TODO, et l'interface n'utilise pas encore `MAINTAI_API_URL`.

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   Une image est le modèle immuable qui contient l'application et ses dépendances. Un conteneur est une instance de cette image en cours d'exécution, avec sa propre configuration et, éventuellement, des volumes.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Docker met en cache chaque couche. Tant que le fichier des dépendances ne change pas, l'installation des bibliothèques reste en cache, même si le code de `maintai` change.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle fourni a été sérialisé avec scikit-learn 1.8.0. Figer cette version évite les incompatibilités de chargement ou de prédiction qu'une autre version pourrait introduire.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert l'API et l'interface; elle n'entraîne pas le modèle, ne suit pas les expériences, ne versionne pas les données et n'exécute pas les tests. Ces outils restent dans l'environnement de développement, ce qui évite d'alourdir l'image inutilement.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# Même version de Python que l'environnement de développement, sur une image légère.
FROM python:3.11-slim

# Toutes les commandes suivantes s'exécutent depuis /app.
WORKDIR /app

# Installer d'abord les dépendances pour réutiliser cette couche en cache
# lorsque seul le code de l'application change.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Ajouter le code de l'API et de l'interface après l'installation.
COPY maintai/ ./maintai/
COPY ui/ ./ui/

# Les données et le modèle ne sont pas inclus dans l'image; ces chemins
# peuvent être alimentés par des volumes au lancement du conteneur.
ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

# Indiquer le port écouté par l'API.
EXPOSE 8000

# Écouter sur toutes les interfaces du conteneur pour permettre la publication du port.
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build (sans cache) | 179,7 s (2 min 59,7 s) | 1,13 GB |
| après une modification de `maintai/predict.py` | 4,7 s | 1,13 GB |

Que signifie `CACHED` dans le journal du second build ?

Docker réutilise une couche déjà construite parce que ses instructions et ses fichiers d'entrée n'ont pas changé. Ici, l'installation des dépendances est réutilisée; la copie de `maintai` est reconstruite après le changement de `predict.py`.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run --name test -d -p 8002:8000 -e MAINTAI_API_KEY=tp6-test-key -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `200` — `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | `401` — clé API absente ou invalide |
| `POST /v1/predict` avec la clé | `200` — `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"2026-11-26T09:23:16Z"}` |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond `200` avec `model_loaded:false`, car le modèle est exclu de l'image et n'est pas monté dans le conteneur. Avec une clé API valide, `/v1/predict` répond `503` (modèle non chargé); sans clé, l'authentification échoue d'abord avec `401`.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` indique `Uvicorn running on http://127.0.0.1:8000`. L'URL `http://localhost:8002/health` depuis le PC ne répond pas : le serveur n'écoute que sur l'interface de boucle locale du conteneur, pas sur son interface réseau. Il faut écouter sur `0.0.0.0` pour que la publication du port Docker fonctionne.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .                            # Construit l'image depuis le Dockerfile local
    image: maintai:0.4.0
    env_file: .env                     # Fournit la clé API sans l'inclure dans l'image
    ports:
      - "8000:8000"                    # Publie l'API sur le port 8000 du PC
    volumes:
      - ./models:/app/models:ro        # Le modèle reste sur le PC et est monté en lecture seule

  ui:
    image: maintai:0.4.0              # Réutilise l'image construite par le service api
    command: ["python", "-m", "streamlit", "run", "ui/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000 # DNS Compose : l'API est joignable par son nom de service
    ports:
      - "8501:8501"                    # Publie Streamlit sur le port 8501 du PC
    volumes:
      - ./data:/app/data:ro            # Les données de l'interface restent sur le PC
    depends_on:
      - api                            # Démarre l'API avant l'interface
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       9 minutes ago   Up 9 minutes   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        9 minutes ago   Up 9 minutes   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Compose la fournit dans `MAINTAI_API_URL`; le nom `api` est le nom du service et se résout sur le réseau Compose. L'interface lit cette variable d'environnement et utilise `http://localhost:8000` seulement si elle n'est pas définie.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
> docker compose exec -T ui python -c "import httpx; print(httpx.get('http://api:8000/health', timeout=5).json())"
{'status': 'ok', 'model_loaded': True}

> docker compose exec -T ui python -c "import httpx; print(httpx.get('http://localhost:8000/health', timeout=2).json())"
httpx.ConnectError: [Errno 111] Connection refused
```

Dans le conteneur UI, `localhost` désigne le conteneur UI lui-même, où aucun serveur n'écoute sur le port 8000. Le nom de service `api` permet de joindre l'API sur le réseau Compose.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
.\.venv\Scripts\python.exe -m pytest
======================= 38 passed, 4 warnings in 57.71s =======================
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le fichier `docs/adr/005-image-docker.md` n'est pas présent dans le workspace; cette synthèse est donc déduite de la configuration Compose actuelle. L'application et ses dépendances sont intégrées à l'image, tandis que le modèle et les données sont montés en lecture seule et la clé API est fournie au démarrage par `.env`.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   L'image contient Python, les dépendances figées de `requirements-docker.txt` et le code des dossiers `maintai/` et `ui/`. Au lancement, Compose fournit la clé par `env_file: .env`, monte le modèle et les données depuis le PC en lecture seule, définit `MAINTAI_API_URL` et publie les ports 8000 et 8501.
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Le fichier `.env` est exclu du contexte de build par `.dockerignore`; Compose injecte la clé au démarrage. Elle peut ainsi être changée sans reconstruire l'image et n'est pas enregistrée dans ses couches.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Il faut livrer et versionner le modèle avec la bonne version de scikit-learn, puis choisir de l'ajouter à l'image ou de le fournir séparément. Ici, il reste un artefact sur le PC monté dans le conteneur, ce qui garde l'image indépendante du modèle mais impose de fournir ce volume au déploiement.

## 8. Le rendu Git

- Lien de la pull request : 
- Le tag `tp6` existe sur GitHub : 
- `git status` avant le commit :  Le `.gitignore` courant exclut `.env`, `models/` et `data/*.csv`.

## 9. Ce qui reste flou

