# TPO : Prévision des repas de la cantine

**Nom :** Prénom Nom
**Groupe :** G3

# Le problème

Chaque jour à 10 h, le gestionnaire de la cantine commande à la cuisine le nombre de repas du lendemain. Aujourd'hui, il reprend le chiffre de la même journée la semaine précédente. Un repas en trop est jeté (environ 15 DH perdus), un repas manquant entraîne un élève sans déjeuner, un remplacement d'urgence et des plaintes. L'objectif est de prédire `repas_servis` à partir des informations connues la veille : nombre d'inscrits, menu, jour de la semaine, météo, examens, sorties et veilles de vacances.

Les données couvrent 340 jours d'école, de septembre 2024 à juin 2026. Le découpage est chronologique : l'entraînement porte sur le passé, le test sur les 20 % de jours les plus récents, soit environ 68 jours.

# Résultats sur le jeu de test

| Modèle | MAE (repas) | RMSE (repas) | R² |
|---|---|---|---|
| ridge | 22.377 | 28.315 | 0.882 |
| gradient_boosting | 29.852 | 37.727 | 0.790 |
| random_forest | 31.825 | 41.647 | 0.745 |
| knn | 40.274 | 49.450 | 0.640 |
| baseline | 70.271 | 88.416 | -0.151 |

Meilleur modèle selon le MAE : **ridge**.

# Le critère (MAE ≤ ... repas) est-il atteint ?

Le template demande un rappel supérieur ou égal à 0,75. Ce critère ne s'applique pas à une prévision de nombres. Le critère de ce projet doit être défini : une erreur moyenne de 22 repas est-elle acceptable pour le gestionnaire ? La réponse dépend du coût d'un repas manquant, qui n'est pas encore estimé. Le ridge bat nettement la baseline (MAE 22 contre 70), mais cela ne dit pas si le gestionnaire y gagne de l'argent.

# Ce qui reste flou

- **Coût asymétrique non calculé.** Le MAE traite un repas en trop comme un repas manquant. Le coût réel (15 DH par repas en trop, C DH par repas manquant) et le taux de jours en rupture restent à mesurer pour chaque modèle.
- **Modèle quantile non testé.** Un modèle entraîné sur un quantile d'environ 0,73 pourrait réduire les ruptures, au prix de plus de repas jetés.
- **Une seule fenêtre de test.** Le score repose sur une fin d'année scolaire. La stabilité du classement entre modèles n'est pas vérifiée.
- **Baseline à préciser.** Il faut confirmer ce que représente exactement la baseline (reprise de la semaine précédente ou autre), et comment les lundis après les vacances, où `repas_semaine_precedente` est vide, ont été traités.
- **Choix de la métrique.** Le modèle est choisi sur le MAE, alors que la décision finale devrait dépendre du coût.

---
*Développement et déploiement d'applications intelligentes*