# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :**G1  ·  **Membres :**EL FATIMI OUMNIA  ·  **Date :**

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
```

Dernière ligne de `python -m pytest` après la mise en place :

```
38 passed, 6 warnings in 55.27s
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   
   L'image est le paquet figé et nommé maintai:0.4.0 produit par docker build et le conteneur est une copie de cette image en train de tourne
   
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   
   Docker garde en mémoire les étapes déjà faites et en les mettant en premier Docker ne les réinstalle pas quand je modifie seulement le code et c'est plus rzpide

3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   
   Le modèle a été créé avec cette version. Avec une autre version, il peut ne pas se charger ou donner d'autres résultats. En fixant la version exacte, l'image sera toujours la même

4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   
   Ce sont des outils pour développer pas pour faire tourner l'API et les enlever rend l'image plus légère et le build plus rapide.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build |179,7 s (2 min 59,7 s)|	1,13 GB  |
| après une modification de `maintai/predict.py` | 4,7 s |	1,13 GB |

Que signifie `CACHED` dans le journal du second build ?

CACHED indique que Docker a réutilisé une couche déjà construite au lieu de la refaire…

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` |{"status":"ok","model_loaded":true} |
| `POST /v1/predict` sans clé | 401|
| `POST /v1/predict` avec la clé | 200, {"failure_probability": …, "alert": …} |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

/health répond {"status":"ok","model_loaded":false} et /v1/predict répond 503 « Modèle non chargé ». L'API démarre, mais le modèle n'est pas dans l'image

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

docker logs test affiche Uvicorn running on http://127.0.0.1:8000, mais http://localhost:8002/health ne répond pas (réponse vide). Dans un conteneur, 127.0.0.1 veut dire « ce conteneur seulement ». Docker relie le port 8002 du PC à l'interface réseau externe du conteneur, sur laquelle uvicorn n'écoute pas. Avec --host 0.0.0.0, il écoute sur toutes les interfaces, dont celle que Docker relie au PC.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
services:
  api:
    container_name: maintai-api
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command:
      - python
      - -m
      - streamlit
      - run
      - ui/app.py
      - --server.address=0.0.0.0
      - --server.port=8501
      - --server.headless=true
    environment:
      MAINTAI_API_URL: "http://api:8000"
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api

```

Sortie de `docker compose ps` :

```
NAME       IMAGE           COMMAND                  SERVICE   CREATED          STATUS          PORTS
tp6-ui-1   maintai:0.4.0   "python -m streamlit…"   ui        46 minutes ago   Up 46 minutes   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

[…](http://api:8000)
elle vient de la variable d'environnement MAINTAI_API_URL

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
{"status":"ok","model_loaded":true}
```
httpx.ConnectError: [Errno 111] Connection refused
…

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
Compose place les services sur un même réseau où chacun se joint par son nom : http://api:8000 atteint le conteneur de l'API. localhost désigne toujours le conteneur lui-même ; dans le conteneur ui, il n'y a pas d'API sur le port 8000, d'où le refus de connexion
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le modèle n'est pas dans l'image : il arrive par un volume en lecture seule, car il change sans nouveau code (MLOps) et l'image reste ainsi légère, réutilisable et sans donnée sensible. .dockerignore laisse dehors .venv/, data/, models/, .env, mlflow.db, mlruns/, .dvc/, tests/ et .git/, pour garder l'image petite, éviter d'y embarquer un secret ou des données, et ne pas invalider le cache inutilement.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.

Dans l'image, au docker build : Linux, Python 3.11, les bibliothèques (requirements-docker.txt) et le code (maintai/, ui/).
Au lancement : le modèle (volume -v ...models:/app/models:ro), les données (volume data/) et la clé API (--env-file .env).

2. Pourquoi la clé API n'est-elle jamais dans l'image ?

Une image peut être partagée ou publiée, et quiconque la reçoit peut en lire le contenu, couches comprises

3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Docker ajoute l'environnement d'exécution

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

## 9. Ce qui reste flou

…
