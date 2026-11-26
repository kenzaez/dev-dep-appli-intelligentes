# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G1  ·  **Membres :** Belayachi Adnane  ·  **Date :** 26/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
(collez ici)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
(collez ici)
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   …
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   …
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   …
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   …

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build |1.5s |1.13GB |
| après une modification de `maintai/predict.py` | | |

Que signifie `CACHED` dans le journal du second build ?

…

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "$(pwd)/models:/app/models:ro" maintai:0.4.0

| Essai | Réponse |
|---|---|
| `GET /health` |Successful Response |
| `POST /v1/predict` sans clé |cle api absente ou invalide|
| `POST /v1/predict` avec la clé |{"detail": "Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"} |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

…

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

…

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
    env_file: .env                     
    ports:
      - "8000:8000"                    
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       6 seconds ago   Up 4 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        6 seconds ago   Up 4 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

…

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```

```

api: {"status":"ok","model_loaded":true}
localhost: Connection Refused 

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
=== 38 passed, 6 warnings in 10.14s ===
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le modèle n'est pas dans l'image : il arrive au lancement par un volume en lecture seule, car il change (ré-entraînement) sans nouveau code. L'image ne contient que le code (`maintai/`, `ui/`) et les bibliothèques épinglées, tandis que les données, le modèle et la clé API restent dehors grâce à `.dockerignore`, aux volumes et à `--env-file`.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   …
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   …
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   …

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

## 9. Ce qui reste flou

…
