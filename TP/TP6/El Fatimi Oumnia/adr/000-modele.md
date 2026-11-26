# ADR 005 : Image Docker de MaintAI, modèle par volume

Date : 26/11/2026 · Auteurs : Oumnia El Fatimi, …

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de .venv. Il faut décider ce qui entre dans l'image Docker et ce qui reste dehors, sachant que le modèle change sans nouveau code et que la clé API est un secret.

## Options étudiées
1. **Le modèle dans l'image** : l'image marche toute seule, sans volume à penser. Mais il faut reconstruire et republier une image à chaque réentraînement, et l'image est plus lourde.
2. **Le modèle donné au lancement par un volume (`-v`)** : l'image reste légère et valable quand le modèle change. Mais si on oublie le volume, l'API répond `model_loaded: false` et 503.
3. **Tout copier dans l'image (pas de `.dockerignore`)** : plus simple à écrire. Mais l'image devient très lourde, et elle peut contenir la clé `.env` et les données, donc fuiter si on la partage.
4. **Un `.dockerignore` strict** : l'image est petite, le build est rapide et sans secret. Mais l'image seule ne suffit pas à tourner : il faut lui donner le modèle et la clé.

## Décision
Le modèle arrive par un volume en lecture seule (`-v ...models:/app/models:ro`), et la clé par `--env-file .env`. Le `.dockerignore` laisse dehors `.venv/`, `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/`, `.dvc/`, `tests/` et `.git/`. La raison principale : le modèle et les données changent sans nouveau code, et un secret ne doit jamais entrer dans une image qu'on peut partager.

## Conséquences
- Facilite : réentraîner le modèle sans refaire de build, une image plus petite, aucun secret ni donnée dans l'image.
- Rend plus difficile : il faut penser à monter le volume et à fournir le `.env`, sinon `model_loaded: false` (503) ou 401. Dans Compose, ces deux éléments sont écrits une fois dans `compose.yaml`.
- À surveiller : la version de scikit-learn est fixée (`==1.8.0`), elle doit rester la même que celle de l'entraînement du modèle.