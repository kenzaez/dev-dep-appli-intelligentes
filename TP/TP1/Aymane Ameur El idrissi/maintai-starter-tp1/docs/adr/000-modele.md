# ADR 000 : Choix du modèle de prédiction

Date : 22/10/2026 · Auteurs : Aymane Ameur El idrissi

## Contexte
MaintAI doit estimer la probabilité de panne à partir de quatre mesures
numériques : température, vibration, charge et durée de fonctionnement. Le
modèle doit être suffisamment simple pour être entraîné et déployé localement,
tout en fournissant une probabilité exploitable par l'API et un comportement
reproductible.

## Options étudiées
1. **Baseline `DummyClassifier`** : très simple, rapide et utile comme point de
   comparaison ; en revanche, elle prédit toujours la classe majoritaire et ne
   détecte donc aucune panne.
2. **Pipeline `StandardScaler` + `LogisticRegression`** : adaptée aux quatre
   variables numériques, rapide à entraîner, capable de produire
   `predict_proba()` et facile à sérialiser avec `joblib` ; elle suppose
   toutefois une relation suffisamment simple entre les variables et le risque
   de panne.

## Décision
Nous retenons la pipeline **`StandardScaler` + `LogisticRegression`**, avec un
seuil d'alerte fixé à **0,3** au lieu du seuil implicite de 0,5. Le scaler et le
classifieur sont sauvegardés ensemble afin que le prétraitement appliqué en
production soit identique à celui de l'entraînement.

Sur les résultats obtenus, le modèle a été entraîné sur **4 000** observations
et évalué sur **1 000** observations :

| Modèle | Accuracy | Recall | Precision | Seuil |
|---|---:|---:|---:|---:|
| Pipeline retenue | 0,904 | 0,750 | 0,622 | 0,3 |
| Baseline majoritaire | 0,864 | 0,000 | — | — |

La pipeline est retenue car elle améliore l'accuracy de 0,864 à 0,904 et,
surtout, détecte les pannes avec un recall de 0,750, alors que la baseline a un
recall nul. Le seuil à 0,3 privilégie la détection des pannes, ce qui est
cohérent avec l'objectif de maintenance préventive.

## Conséquences
Cette décision facilite l'entraînement, le déploiement et l'interprétation de
la chaîne de prédiction. L'API peut charger un unique artefact
`models/model.joblib`, calculer une probabilité comprise entre 0 et 1 et
déclencher une alerte lorsque celle-ci atteint 0,3. Le modèle est versionné
avec ses métadonnées : les variables attendues sont
`temperature_c`, `vibration_mm_s`, `load_pct` et `runtime_hours`.

En contrepartie, la régression logistique peut moins bien représenter des
relations non linéaires ou des interactions complexes qu'un modèle en arbre ou
un ensemble d'arbres. La précision de 0,622 montre également que certaines
alertes sont des faux positifs. Il faudra donc surveiller le recall, la
precision et le choix du seuil sur des données réelles, réentraîner le modèle
si la distribution des capteurs évolue, et comparer ultérieurement d'autres
algorithmes sur le même jeu de validation.
