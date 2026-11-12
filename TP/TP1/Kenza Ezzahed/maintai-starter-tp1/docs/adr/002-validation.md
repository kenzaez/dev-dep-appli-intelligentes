# ADR 002 : Validation des relevés et modèle indisponible

Date : 22/10/2026 · Auteurs : Kenza Ezzahed

## Contexte

L'API reçoit des mesures physiques qui alimentent directement le modèle : des valeurs impossibles ou hors du domaine prévu ne doivent pas être interprétées comme des prédictions fiables. Au démarrage, le fichier du modèle peut également manquer, par exemple avant le premier entraînement ; l'API doit alors signaler clairement que la prédiction n'est pas disponible.

## Options étudiées

1. **Bornes métier sur les mesures** : rejeter à l'entrée les valeurs hors du domaine défini pour chaque variable. Cela rend le contrat explicite et évite d'envoyer au modèle des entrées incohérentes, mais les bornes doivent être révisées si le matériel ou la définition des mesures change.
2. **Pas de bornes métier** : accepter toute valeur numérique et laisser le modèle produire une réponse. C'est plus permissif, mais laisse passer des valeurs physiquement impossibles ou très éloignées des données d'entraînement ; la prédiction peut alors être trompeuse.
3. **Démarrer l'API sans modèle et répondre 503 aux prédictions** : l'API reste joignable et peut exposer son état de santé, mais les prédictions sont temporairement indisponibles.
4. **Refuser de démarrer sans modèle** : la panne est visible immédiatement au lancement et aucun serveur partiellement fonctionnel n'est exposé, mais aucun endpoint (y compris le diagnostic de santé) n'est alors accessible.

## Décision

Nous validons les entrées avec des bornes cohérentes avec la grandeur physique et le domaine de fonctionnement retenu par le projet :

| Variable | Bornes | Justification |
|---|---:|---|
| `temperature_c` | -40 à 150 °C | Enveloppe plausible pour une mesure de température industrielle, du froid ambiant jusqu'à une température moteur très élevée. La limite haute rejette une valeur manifestement hors domaine comme 500 °C ; ce n'est pas une consigne de fonctionnement sûr. |
| `vibration_mm_s` | 0 à 30 mm/s | Une vitesse vibratoire est une grandeur positive. 30 mm/s couvre une vibration très sévère mais mesurable, au-delà des niveaux habituels de fonctionnement ; la limite valide l'entrée, elle ne signifie pas que ce niveau est acceptable. |
| `load_pct` | 0 à 100 % | Le pourcentage est défini ici par rapport à la charge nominale : zéro correspond à l'absence de charge et 100 % à la charge nominale. Une mesure de surcharge nécessiterait une définition différente et une révision de cette borne. |
| `runtime_hours` | 0 à 20 000 h | Un compteur d'heures écoulées ne peut pas être négatif. La limite haute fixe l'horizon de fonctionnement couvert par le modèle et le projet ; ce n'est pas une limite physique universelle de durée de vie et elle devra évoluer si le suivi dépasse cet horizon. |

Si le modèle n'est pas disponible, l'API démarre tout de même : `/health` indique `model_loaded: false` et `/v1/predict` répond avec HTTP **503 Service Unavailable**. Nous choisissons cette option car elle permet de diagnostiquer l'état du service et de distinguer une indisponibilité temporaire d'une erreur interne. Un 500 indiquerait plutôt une défaillance inattendue du serveur.

## Conséquences

La validation rend le contrat d'entrée visible dans OpenAPI et transforme les valeurs hors domaine en réponses 422, avant l'appel au modèle. Elle peut toutefois rejeter des mesures valides si le matériel ou la définition d'une variable change : les bornes doivent donc être documentées et réévaluées avec le domaine du modèle.

Avec le choix 503, les outils de supervision peuvent vérifier l'API même sans modèle, et les clients savent qu'ils peuvent réessayer après disponibilité du modèle. En contrepartie, une instance démarrée sans modèle peut sembler active si le client ne vérifie que la disponibilité réseau ; les sondes de disponibilité doivent aussi prendre en compte `model_loaded`.
