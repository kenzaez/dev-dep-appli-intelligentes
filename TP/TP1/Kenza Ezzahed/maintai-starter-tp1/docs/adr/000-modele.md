# ADR 000 : Modèle de prédiction de panne et seuil d'alerte

Date : 22/10/2026 · Auteurs : Kenza Ezzahed

## Contexte
MaintAI doit transformer un relevé de quatre capteurs numériques (`temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours`) en une probabilité de panne exploitable par l'API. Les pannes sont minoritaires dans les données (environ 14 % des relevés de test), et en maintenance préventive une panne manquée coûte plus cher qu'une inspection inutile : le modèle doit donc détecter les pannes, pas seulement avoir une bonne accuracy.

## Options étudiées
1. **Baseline `DummyClassifier` (classe majoritaire)** : immédiate à entraîner et utile comme référence ; mais elle répond toujours « pas de panne », donc son recall est nul et elle ne sert à rien pour l'alerte.
2. **Pipeline `StandardScaler` + `LogisticRegression`** : rapide, reproductible, fournit directement `predict_proba()` et s'interprète par ses coefficients ; le scaler fait partie de l'artefact, donc le prétraitement est identique en entraînement et en production. Limite : elle suppose une relation à peu près linéaire entre les mesures et le risque.
3. **Modèle à base d'arbres (forêt aléatoire, gradient boosting)** : capte les non-linéarités et les interactions entre capteurs ; mais il est plus lourd, moins lisible, et rien ne montre pour l'instant qu'il est nécessaire sur ces quatre variables.

## Décision
Nous retenons la **pipeline `StandardScaler` + `LogisticRegression`**, sauvegardée en un seul fichier `models/model.joblib`, avec un **seuil d'alerte de 0,3** (configurable par `MAINTAI_THRESHOLD`) au lieu du seuil implicite de 0,5.

Résultats sur le jeu de test (4 000 relevés d'entraînement, 1 000 de test) :

| Modèle | Accuracy | Recall | Precision |
|---|---:|---:|---:|
| Régression logistique, seuil 0,3 | 0,904 | 0,750 | 0,622 |
| Baseline classe majoritaire | 0,864 | 0,000 | — |

L'écart d'accuracy (0,864 → 0,904) est modeste, ce qui montre que l'accuracy seule est trompeuse sur des classes déséquilibrées. Le critère décisif est le recall : la régression logistique détecte trois pannes sur quatre, la baseline aucune. Le seuil abaissé à 0,3 privilégie justement cette détection, au prix de fausses alertes acceptables pour une inspection préventive.

## Conséquences
- **Facilité :** un seul artefact à charger au démarrage de l'API, une probabilité entre 0 et 1, une prédiction rapide. `model_info.json` fixe le contrat d'entrée (noms et ordre des variables, seuil, version de scikit-learn, date d'entraînement) ; la date sert de `model_version` dans les réponses.
- **Difficulté :** une precision de 0,622 signifie qu'environ 4 alertes sur 10 sont des fausses alarmes ; le modèle linéaire peut aussi manquer des interactions entre capteurs.
- **À surveiller :** recall et precision sur des données réelles (les données actuelles sont synthétiques), le choix du seuil avec les équipes de maintenance, la dérive des mesures capteurs (réentraîner si nécessaire), et la compatibilité de version scikit-learn entre entraînement et chargement. Un modèle à base d'arbres pourra être comparé sur le même jeu de test si la régression logistique devient insuffisante.
