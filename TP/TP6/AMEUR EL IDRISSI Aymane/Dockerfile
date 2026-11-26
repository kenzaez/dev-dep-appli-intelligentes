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
