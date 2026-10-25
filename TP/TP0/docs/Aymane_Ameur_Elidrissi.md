# TPO : MaintAI

**Nom :** Aymane Ameur El idrissi · **Groupe :** G1

## Le problème

Prédire une panne à partir de 4 capteurs ; une panne manquée arrête une ligne.

## Résultats sur le jeu de test

| Modèle | Accuracy | Rappel | Précision |
| --- | ---: | ---: | ---: |
| Baseline | 0.824 | 0.000 | 0.000 |
| Régression logistique | 0.888 | 0.534 | 0.758 |
| Arbre de décision | 0.830 | 0.540 | 0.516 |
| Forêt aléatoire | 0.862 | 0.500 | 0.638 |
| Plus proches voisins | 0.853 | 0.500 | 0.599 |

## Mon choix, et pourquoi

Je retiens la régression logistique, car elle obtient la meilleure accuracy
(0,888) et la meilleure précision (0,758) parmi les modèles testés. Elle
améliore l'accuracy de 0,064 point par rapport à la baseline (0,824). Ce
choix reste toutefois à nuancer, car l'arbre de décision obtient un rappel
légèrement supérieur (0,540 contre 0,534).

## Le critère (rappel ≥ 0,75) est-il atteint ?

Non. Le meilleur rappel obtenu est celui de l'arbre de décision, avec 0,540,
ce qui reste inférieur à 0,75. La régression logistique retenue atteint un
rappel de 0,534 : elle manque donc encore trop de pannes au regard de
l'objectif métier. Elle ne devrait pas être déployée telle quelle sans
amélioration ou validation complémentaire.

## Ce qui reste flou

- Le jeu de test est-il suffisamment représentatif des pannes réelles et
  contient-il assez d'exemples de pannes ?
- Le seuil de décision de la régression logistique doit-il être ajusté pour
  privilégier le rappel, quitte à diminuer la précision ?
- Il faut préciser le coût d'une fausse alerte par rapport au coût d'une
  panne manquée, ainsi que vérifier les résultats avec une matrice de
  confusion et une validation croisée.


# TPO Suite : CantineAI

**Nom :** Aymane Ameur El idrissi · **Groupe :** G1

## Le problème

Prédire le nombre de repas servis à partir des informations disponibles sur la
journée : inscriptions, menu, météo, examens, sortie scolaire et vacances.
L'objectif est d'anticiper les besoins de la cantine afin de limiter les
erreurs de préparation.

La métrique principale retenue est la **MAE** (erreur absolue moyenne), car
elle indique directement de combien de repas la prédiction s'écarte en moyenne
de la réalité. Plus cette valeur est faible, meilleur est le modèle.

## Données et découpage

Le fichier utilisé est `data/cantine_repas.csv`. Il contient 340 lignes
exploitables. Les variables utilisées sont toutes les colonnes sauf la cible
`repas_servis` et la date utilisée pour le tri chronologique.

Le découpage est chronologique : les 20 % de lignes les plus récentes sont
réservés au jeu de test. Le modèle apprend donc sur le passé et est évalué sur
des dates futures.

## Résultats sur le jeu de test

| Modèle | MAE | RMSE | R² |
|---|---:|---:|---:|
| Baseline | 70.271 | 88.416 | -0.151 |
| Régression linéaire | **22.239** | **28.170** | **0.883** |
| Forêt aléatoire | 31.845 | 41.540 | 0.746 |
| K plus proches voisins | 36.212 | 46.037 | 0.688 |
| Arbre de décision | 46.000 | 59.710 | 0.475 |

## Mon choix, et pourquoi

Je retiens la **régression linéaire**. Elle obtient la meilleure MAE
(22.239 repas), ainsi que le meilleur RMSE et le meilleur R². Elle réduit
l'erreur absolue moyenne de 70.271 à 22.239 repas par rapport à la baseline,
soit une amélioration d'environ 68,4 %.

Le modèle retenu est sauvegardé dans `models/model.joblib`, et les résultats
complets sont conservés dans `models/metrics.json`.

## Le critère d'acceptation est-il atteint ?

Le critère « rappel ≥ 0,75 » du template concerne une tâche de classification
de pannes. Le projet actuel est configuré en **régression** (`TASK =
"regression"`), avec `repas_servis` comme cible : ce critère de rappel ne
s'applique donc pas.

Pour la tâche actuelle, la régression linéaire dépasse nettement la baseline
sur la métrique principale MAE.

## Ce qui reste flou

- Le jeu de données reste limité à 340 lignes et les résultats peuvent varier
  sur une période différente.
- Une erreur moyenne de 22 repas peut cacher des erreurs beaucoup plus fortes
  certains jours.
- La qualité des prédictions dépend de la représentativité des menus, de la
  météo et des événements présents dans les données.
