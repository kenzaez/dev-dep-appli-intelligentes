# ADR 005 : Contenu de l'image Docker de MaintAI

Date : 26/11/2026 · Auteurs : Belayachi Adnane

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : on emballe l'API et l'interface dans l'image `maintai:0.4.0`. Il faut décider ce qui entre dans l'image (le modèle en particulier) et ce que `.dockerignore` laisse dehors.

## Options étudiées

**Décision 1 : où met-on le modèle ?**
1. Modèle dans l'image (`COPY models/ ./models`) : l'image est autonome et se lance sans rien monter. En revanche, chaque ré-entraînement oblige à reconstruire et redistribuer une image lourde, et le modèle (donné de production) est mélangé au code.
2. Modèle fourni au lancement par un volume (`-v ./models:/app/models:ro`) : l'image reste petite, identique d'une version du modèle à l'autre, et le modèle change sans nouveau build. En revanche, il faut penser au volume : sans lui, `/health` répond `model_loaded: false` et `/v1/predict` répond 503.

**Décision 2 : que laisse-t-on hors de l'image (`.dockerignore`) ?**
1. Tout copier (`COPY . .`) : plus simple à écrire. En revanche, l'image embarque le secret `.env`, les données, le modèle, l'historique Git et les fichiers MLflow/DVC : build plus long, image plus grosse, risque de fuite.
2. Exclure ce qui n'est pas du code : copier seulement `maintai/` et `ui/`, et lister dans `.dockerignore` `.venv/`, `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/`, `.dvc/`, `tests/`, `.git/`. L'image est plus légère et sûre, mais chaque exclusion doit être compensée au lancement (volume ou `--env-file`).

## Décision
1. Le modèle arrive par un volume en lecture seule : il change sans nouveau code (cycle MLOps), alors que l'image ne change que quand le code ou les bibliothèques changent.
2. L'image ne contient que le code (`maintai/`, `ui/`), Python et les bibliothèques épinglées (`scikit-learn==1.8.0`, pour rester à la version de l'entraînement). Données, modèle et secret restent dehors : les données et le modèle changent sans nouveau code, et un secret n'entre jamais dans une image qu'on peut partager.

## Conséquences
- Facilite : des builds rapides grâce au cache des couches (bibliothèques avant le code), une même image pour tous les environnements, un ré-entraînement sans rebuild.
- Rend plus difficile : le lancement demande des options (`-v`, `--env-file`, ou `compose.yaml`) et un oubli donne une API démarrée mais sans modèle.
- À surveiller : la version de scikit-learn de l'image doit rester celle de l'entraînement, car un modèle chargé avec une autre version peut échouer ; `git status` ne doit jamais montrer `.env`, `models/`, `data/*.csv` ni `mlflow.db`.
