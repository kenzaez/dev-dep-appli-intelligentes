# TPO : MaintAI

**Nom :** [Prénom Nom]  
**Groupe :** G3  
**Formation :** Développement et déploiement d'applications intelligentes — S4  
**Date :** 22/10/2026

## Le problème

MaintAI cherche à prédire une panne à partir de quatre mesures : température,
vibration, charge et durée de fonctionnement. Une panne manquée peut arrêter une
ligne de production ; le rappel de la classe « panne » est donc le critère
principal à surveiller.

## Données et méthode

Le jeu de données `data/exemple_pannes.csv` contient **5 000 observations**,
quatre variables capteurs et la cible `failure` (0 : pas de panne, 1 : panne).
Il comprend 878 pannes (17,6 %) et 4 122 observations sans panne (82,4 %).
Aucune valeur manquante n'a été relevée dans ce fichier.

Les résultats ci-dessous sont ceux fournis pour le jeu de test. La baseline
prédit la classe majoritaire ; elle sert de comparaison avec la régression
logistique. Les détails du découpage et de la graine ne sont pas précisés dans
les résultats transmis.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel (panne) | Précision (panne) | F1 (panne) |
|---|---:|---:|---:|---:|
| Baseline (classe majoritaire) | 0,824 | 0,000 | 0,000 | 0,000 |
| Régression logistique | 0,889 | 0,574 | 0,737 | ≈ 0,644* |

La régression logistique améliore l'accuracy de **6,5 points** par rapport à la
baseline et détecte davantage de pannes. Cependant, elle manque encore environ
42,6 % des pannes du jeu de test.

## Le critère (rappel ≥ 0,75) est-il atteint ?

**Non.** Le rappel observé est de **0,574**, soit **0,176** en dessous du seuil
de 0,75. Le modèle ne satisfait donc pas encore le critère d'acceptation et ne
devrait pas être utilisé seul pour décider qu'une machine peut continuer à
fonctionner.

## Décision et suites proposées

La régression logistique est préférable à la baseline, mais le rappel atteint
reste insuffisant au regard du coût d'une panne manquée. Il faut notamment
étudier un ajustement du seuil de décision et des poids de classes, puis
comparer les modèles sur un découpage adapté à l'ordre temporel des mesures.
Le choix final devra tenir compte du compromis entre pannes manquées et fausses
alertes, ainsi que de la validation sur des données de production indépendantes.

## Ce qui reste flou et limites

- Les résultats transmis ne précisent pas la méthode de découpage, la taille du
  jeu de test ni la graine utilisée.
- Le seuil de 0,75 est indiqué, mais le coût acceptable des fausses alertes et
  le seuil de décision opérationnel restent à définir.
- Le F1 n'était pas lisible dans les résultats fournis : la valeur indiquée est
  calculée à partir du rappel et de la précision publiés, et doit être confirmée
  avec la sortie exacte de l'évaluation.
- Le fichier d'exemple est un jeu de données fourni avec le projet ; ses
  performances ne garantissent pas les mêmes résultats en conditions réelles.
- Les conséquences d'une alerte, le délai de prévision souhaité et les modalités
  de déploiement restent à préciser.

*F1 estimé par \(2 \times précision \times rappel / (précision + rappel)\), à
partir des valeurs arrondies communiquées.*
