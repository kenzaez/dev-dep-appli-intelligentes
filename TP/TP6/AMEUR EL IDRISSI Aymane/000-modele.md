# ADR 000 : Choix du modèle de détection de panne

Date : 26/11/2026 · Auteurs : Aymane Ameur El idrissi

## Contexte
MaintAI doit estimer la probabilité de panne à partir de quatre mesures numériques de capteurs et fournir une prédiction avec un seuil d'alerte configurable. Le modèle doit rester simple à entraîner et à exécuter sur CPU, et son prétraitement ainsi que son contrat d'entrée doivent être conservés pour servir les prédictions de façon cohérente.

## Options étudiées
1. Régression logistique dans un pipeline avec `StandardScaler` : modèle léger, probabilités disponibles et prétraitement sauvegardé avec le classifieur; sa frontière de décision reste linéaire.
2. `RandomForestClassifier` : peut apprendre des relations non linéaires, mais est plus complexe à expliquer et à maintenir.
3. `DummyClassifier` comme baseline : référence très simple, mais ne détecte pas les pannes lorsqu'il prédit toujours la classe majoritaire.

## Décision
Retenir la régression logistique (`C=1.0`) comme modèle par défaut, dans un pipeline qui sauvegarde ensemble l'échelle des variables et le classifieur; conserver la forêt aléatoire comme option explicite d'entraînement. Comparer les résultats à la baseline et enregistrer avec le modèle ses métriques, ses quatre variables d'entrée, son seuil d'alerte et la version de scikit-learn.

## Conséquences
Le pipeline rend le prétraitement identique à l'entraînement et à l'inférence, et la baseline vérifie que le modèle apporte une valeur mesurable : sur le jeu de test actuel, le rappel est de 0,75 contre 0,0 pour la baseline. Le modèle sérialisé dépend de scikit-learn 1.8.0, qui doit rester épinglé; les données étant synthétiques, ces métriques ne démontrent pas les performances sur des machines réelles et devront être réévaluées avec des données représentatives.
