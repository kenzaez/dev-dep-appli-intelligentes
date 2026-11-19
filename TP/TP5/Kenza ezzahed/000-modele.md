# ADR 000 : choix du modèle et du seuil d'alerte de MaintAI

Date : 19/11/2026 · Auteurs : Kenza Ezzahed

## Contexte
MaintAI doit signaler les machines qui risquent de tomber en panne. Une panne manquée (faux négatif) coûte bien plus cher qu'une fausse alerte (une inspection inutile) : la métrique prioritaire est donc le **recall**, la precision venant en second. Jusqu'au TP4, chaque entraînement écrasait le précédent ; depuis le TP5, chaque réglage est un run MLflow relié à la version exacte des données (DVC).

## Options étudiées
Runs MLflow de l'expérience `maintai`, tous sur les données v1 (`data_md5` = `73e0b7cb…`, 5000 relevés, `n_train` = 4000) :

| Option | Run | recall | precision | accuracy |
|---|---|---|---|---|
| Régression logistique, C = 1, seuil 0.3 (défaut) | `9b6401d4…` | 0.750 | 0.622 | 0.904 |
| Régression logistique, C = 0.01, seuil 0.3 | `4511b2f4…` | 0.691 | 0.653 | 0.908 |
| **Régression logistique, C = 1, seuil 0.2** | `954180d6…` | **0.838** | 0.543 | 0.882 |
| Forêt aléatoire, seuil 0.3 | `668f7f9b…` | 0.728 | 0.562 | 0.886 |
| Forêt aléatoire, seuil 0.2 | `0124c832…` | 0.831 | 0.479 | 0.854 |

1. **Logreg, seuil 0.3** : bon compromis, mais elle manque 1 panne sur 4.
2. **Logreg, C = 0.01** : un peu plus précise, mais elle manque encore plus de pannes. Rejetée.
3. **Logreg, seuil 0.2** : le meilleur recall. Elle déclenche environ une fausse alerte pour une vraie.
4. **Forêt aléatoire** : à seuil égal, elle fait moins bien que la logreg sur les deux métriques. Elle est aussi plus lourde et moins explicable. Rejetée.

## Décision
On retient la **régression logistique (C = 1) avec un seuil d'alerte de 0.2**.
- Run MLflow : `954180d6e5ff4ab4b7d5f3967fd1c02c`
- Données : `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (v1, commit Git « Données v1 », récupérable par `dvc checkout` / `dvc pull`)

C'est le meilleur recall mesuré (0.838 contre 0.750 au seuil 0.3). La contrainte qui décide est le coût d'une panne manquée.

## Conséquences
- On accepte **plus de fausses alertes** : la precision passe de 0.62 à 0.54, soit environ une inspection inutile pour une panne détectée. Il faut le dire à l'équipe de maintenance.
- La forêt aléatoire n'apporte rien ici : le modèle reste simple, rapide et lisible (coefficients).
- Le seuil se règle par `MAINTAI_THRESHOLD=0.2` (ou `--threshold 0.2`), sans modifier le code.
- À surveiller : les données v2 (`93fdeef2…`, 8000 relevés) ont une autre distribution. Il faudra ré-entraîner et re-mesurer avec ce seuil sur la v2, sur un même jeu de test, avant de livrer le modèle.
