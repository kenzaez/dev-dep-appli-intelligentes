# ADR 000 : choix du modèle de prédiction

Date : 19/11/2026 · Auteurs : Belayachi Adnane 

## Contexte
MaintAI doit détecter les risques de panne à partir des relevés de capteurs. Une panne manquée coûte plus cher qu'une fausse alerte : il faut donc privilégier un bon recall tout en conservant une précision acceptable.

## Options étudiées
1. Régression logistique : entraînement rapide, résultat interprétable, mais performance éventuellement limitée par les relations non linéaires.
2. Forêt aléatoire : peut modéliser des relations non linéaires, avec un coût de calcul et une moindre interprétabilité plus élevés.

## Décision
La régression logistique avec un seuil de décision de 0.2 est retenue. Sur les runs comparés, ce modèle obtient un recall de 0.838, supérieur à celui du seuil par défaut et à celui de la forêt aléatoire.

Cette décision correspond au run MLflow `9934442aafe54bd5acab0abde51e8576`, utilisant la version des données dont l'empreinte `data_md5` est `73e0b7cb3c6f795c70c3ddf970b99c15`.

## Conséquences
Cette configuration permet de détecter davantage de pannes au prix d'une précision plus faible et donc de davantage de fausses alertes. Le seuil doit être surveillé, ainsi que les dérives des données et les changements de leur distribution.
