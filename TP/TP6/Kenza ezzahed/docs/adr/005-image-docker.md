# ADR 005 : le modèle hors de l'image Docker, apporté par un volume

Date : 26/11/2026 · Auteurs : Kenza Ezzahed

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : on l'emballe dans une image Docker
(`maintai:0.4.0`). Il faut décider ce qui entre dans l'image (figé à chaque `docker build`) et ce qui arrive au
lancement (`docker run`). Deux questions : le modèle doit-il être dans l'image ou venir d'un volume ? Et que doit
laisser dehors le `.dockerignore` ?

## Décision 1 : le modèle arrive par un volume, en lecture seule

### Options étudiées
1. **Modèle dans l'image** (`COPY models ./models`)
   - gagne : une seule chose à livrer, l'image démarre toujours avec un modèle ; le couple code + modèle est figé
     ensemble (impossible de charger un modèle incompatible avec le code) ; pas d'oubli de `-v` (piège 1 du TP).
   - perd : chaque nouveau modèle (réentraînement, nouvelles données) oblige à reconstruire et redistribuer une
     image de plus d'1 Go, alors que le code n'a pas changé ; l'image mélange deux cycles de vie (code / MLOps) ;
     le modèle n'est plus géré par MLflow / DVC (TP5) mais par le tag de l'image ; le build dépend d'un
     entraînement préalable sur le PC qui construit.
2. **Modèle monté par un volume** (`-v ./models:/app/models:ro`, `MAINTAI_MODELS_DIR=/app/models`) — **retenue**
   - gagne : on change de modèle sans nouveau code ni nouveau build (même règle que le wheel du TP4 : le paquet
     porte le code, pas le modèle) ; l'image reste générique et partageable ; `:ro` empêche le conteneur de
     modifier le modèle ; le modèle reste versionné par DVC / suivi par MLflow.
   - perd : le conteneur dépend d'un dossier extérieur ; sans `-v`, l'API démarre avec `model_loaded: false` et
     répond 503 ; il faut garantir que la version de scikit-learn de l'image (`==1.8.0`) est celle qui a écrit
     le modèle.

### Décision
Le modèle arrive au lancement par un volume en lecture seule. Raison principale : le modèle et le code n'ont pas
le même rythme de changement ; on veut réentraîner sans reconstruire l'image.

## Décision 2 : ce que `.dockerignore` laisse dehors

| Laissé dehors | Pourquoi |
|---|---|
| `.env` | le secret (`MAINTAI_API_KEY`) : une image se partage (registre, collègues), un secret n'y entre jamais ; il arrive par `--env-file .env` / `env_file:` |
| `data/`, `models/` | changent sans nouveau code : ils arrivent par des volumes ; les copier alourdirait l'image et invaliderait le cache |
| `mlflow.db`, `mlruns/`, `.dvc/` | outils d'entraînement et de versionnement : inutiles pour servir des prédictions, et lourds |
| `.venv/`, `TP/` (venv local) | environnement Windows du PC, inutilisable dans un Linux ; l'image installe ses propres bibliothèques |
| `tests/`, `.pytest_cache/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `*.egg-info/` | on ne teste pas et on ne construit pas de paquet dans l'image ; fichiers temporaires ou historique |

### Options étudiées
1. **Pas de `.dockerignore`** (tout le dossier comme contexte de build)
   - gagne : rien à maintenir, aucun risque d'oublier un fichier utile.
   - perd : contexte de build énorme (`.venv` de plusieurs centaines de Mo) envoyé à chaque build ; risque de
     faire entrer `.env` dans l'image si un jour on écrit `COPY . .` ; données et modèle figés dans l'image.
2. **`.dockerignore` restrictif** — **retenue**
   - gagne : build plus rapide, image plus petite, aucun secret ni donnée dans l'image même en cas de `COPY . .`.
   - perd : un fichier réellement utile ajouté plus tard pourrait être exclu par erreur (à vérifier si l'image
     échoue au lancement).

### Décision
Un `.dockerignore` restrictif : n'entrent que `requirements-docker.txt`, `maintai/` et `ui/`. Raison principale :
la sécurité (le secret) et la séparation code / données / modèle.

## Conséquences
- Facilité : un réentraînement ne demande qu'un redémarrage du conteneur ; l'image se reconstruit en quelques
  secondes quand seul le code change (couche `pip install` en cache) ; l'image peut être poussée sur un registre
  sans fuite de clé.
- Plus difficile : le lancement demande les bonnes options (`-p`, `-v`, `--env-file`) — d'où `compose.yaml`.
- À surveiller : la version de scikit-learn figée dans `requirements-docker.txt` doit rester celle qui a entraîné
  le modèle monté ; `/health` (`model_loaded`) doit être vérifié après chaque déploiement.
