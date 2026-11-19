# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membres :** AMEUR EL IDRISSI Aymane  ·  **Date :** 19/11/2026 12:00

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
32 passed, 4 warnings in 47.68s
```

Quels tests échouent, et pourquoi ?

Aucun test n'échoue après l'installation des dépendances et du package.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Après `pip install -e .`, le package est installé en mode éditable :
`C:\Users\ayman\Desktop\DevAppInt\TP5\TP5`.
Ainsi, `maintai.__file__` pointe vers
`C:\Users\ayman\Desktop\DevAppInt\TP5\TP5\maintai\__init__.py`.
Avant cette commande, le package n'était pas installé dans l'environnement du TP ;
depuis la racine du projet, Python pouvait toutefois importer le dossier local.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params({**params, "data_md5": file_md5(data_path)})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
        return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 47.68s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| (votre essai) | | | |

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je choisirais `python -m maintai.train --threshold 0.2`. Il obtient le meilleur
recall (0.838), donc il manque moins de pannes. Sa précision est plus faible
(0.543), mais ce compromis est acceptable puisque le coût d'une panne manquée
est supérieur à celui d'une fausse alerte.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

La version indiquée est `scikit-learn==1.8.0`. Le modèle enregistre donc sa
version exacte de scikit-learn, ce qui évite les incompatibilités entre la
version utilisée à l'entraînement et celle utilisée au chargement ou en
production (problème de reproductibilité du TP4).

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Les runs sont enregistrés dans `mlflow.db`, et les artefacts (notamment les
modèles) dans `mlruns/`. Non, ces fichiers ne vont pas dans Git : ils sont
générés localement, volumineux et reproductibles, et sont explicitement ignorés
par `.gitignore`. Git versionne le code et les fichiers de configuration,
tandis que MLflow conserve l'historique des entraînements et leurs artefacts.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 93fdeef2cac1893c4f720c16457eea75
  size: 202834
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

La valeur MD5 du fichier DVC est `93fdeef2cac1893c4f720c16457eea75` et le
dernier run MLflow enregistré sur la v2 possède la même valeur
`93fdeef2cac1893c4f720c16457eea75`. Les deux outils identifient donc exactement
la même version des données.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Le fichier `data/sensors.csv` contient les données volumineuses et est ignoré par
Git. `data/sensors.csv.dvc` contient uniquement une empreinte MD5, sa taille et
son emplacement logique ; ce petit fichier peut donc être versionné par Git.
DVC utilise ensuite le MD5 pour retrouver les données dans son cache ou dans
le stockage distant.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
Data and pipelines are up to date.
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | 9ced45f · Données v1 | 73e0b7cb | 5000 |
| v2 | 218f936 · Données v2 | 93fdeef2 | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

La restauration de la v1 produit un fichier `data/sensors.csv` contenant
**5000 lignes**. Puis le fichier DVC a été remis sur la v2 et
`dvc checkout` a restauré **8000 lignes**.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

Après suppression de `data/sensors.csv` et du dossier `.dvc/cache`,
`dvc pull` récupère une seule donnée depuis le stockage local :
`1 file fetched and 1 file added`. Le fichier est restauré avec ses 8000 lignes
et `dvc status` indique ensuite que les données et les pipelines sont à jour.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 | 93fdeef2 | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Sur ces résultats, la précision augmente sur la v2 mais le recall baisse
légèrement. On ne peut donc pas affirmer sans réserve que le modèle v2 est
meilleur : il dépend du critère retenu. De plus, les deux jeux de données ne
sont pas issus du même découpage : n_train passe de 4000 à 6400, les
distributions et leur séparation peuvent avoir changé. Une comparaison fiable
nécessiterait un même jeu de test, la même graine et idéalement plusieurs
évaluations croisées.

## 5. Décision : l'ADR 004

La décision est documentée dans `docs/adr/004-choix-du-modele.md`. Le modèle
retenu est la régression logistique avec un seuil de 0.2. Le run MLflow associé
est `9934442aafe54bd5acab0abde51e8576`, entraîné sur les données
`73e0b7cb3c6f795c70c3ddf970b99c15`.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
Git suit le code, l'historique des modifications et les petits fichiers de
référence. DVC suit les jeux de données volumineux hors dépôt Git grâce aux
fichiers `.dvc` et à un cache/stockage distant. MLflow suit les entraînements :
paramètres, métriques, dépendances et artefacts des modèles.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
Le stockage `--local` est utilisé uniquement pour le TP et reste sur la machine
locale. Pour partager les données avec tout le groupe, il faudrait configurer
un stockage accessible à tous, par exemple un serveur, un partage réseau ou un
remote cloud (S3, Azure Blob, etc.), puis pousser les fichiers avec `dvc push`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
Livrer un modèle demande : le code capable de charger/prédire, les poids ou
l'artefact sérialisé du modèle, et les métadonnées nécessaires à son usage
(colonnes, seuil, versions des bibliothèques). Ils se trouvent maintenant dans
`maintai/` pour le code, `models/model.joblib` pour le modèle local,
`models/model_info.json` pour le contrat d'entrée, et les artefacts MLflow
dans `mlruns/`.

## 7. Le rendu Git

- Lien de la pull request : 
- Le tag `tp5` existe sur GitHub : 
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non, ils sont ignorés ou gérés par DVC

## 8. Ce qui reste flou

