# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** …  ·  **Membres :** Kenza Ezzahed  ·  **Date :** 19/11/2026

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
FAILED tests/test_tracking.py::test_training_creates_a_run - AssertionError: ...
FAILED tests/test_tracking.py::test_run_records_metrics - AssertionError: auc...
FAILED tests/test_tracking.py::test_run_records_data_version - AssertionError...
FAILED tests/test_tracking.py::test_run_stores_the_model - AssertionError: au...
FAILED tests/test_tracking.py::test_options_change_the_run - AssertionError: ...
5 failed, 27 passed, 2 warnings in 60.62s (0:01:00)
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test_tracking.py` échouent. `log_run` n'est pas encore écrite : elle renvoie `""` sans rien enregistrer. `mlflow.search_runs` ne trouve donc aucun run, d'où « aucun run MLflow : log_run n'a rien enregistré ». Les 27 autres tests (données, entraînement, API, CLI, package, UI) sont ceux du TP4 et passent toujours.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avec l'environnement du TP4, `maintai` pointait vers le dossier du TP4, à cause de l'installation éditable du TP4. Ici, j'ai créé un environnement neuf dans `TP/TP5` : avant `pip install -e .`, `import maintai` depuis un autre dossier donnait `ModuleNotFoundError: No module named 'maintai'`. Après, il pointe vers le TP5 :

```
...\TP\TP5\Kenza ezzahed\maintai\__init__.py 0.3.0
```

C'est ce que vérifie `test_installed_version_matches_the_code`.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
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
32 passed, 4 warnings in 41.23s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training »), sur les données v1 (`data_md5` = `73e0b7cb…`) :

| Commande | Run | recall | precision | accuracy |
|---|---|---|---|---|
| `python -m maintai.train` | `9b6401d4…` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | `4511b2f4…` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | `954180d6…` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | `668f7f9b…` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` (mon essai) | `0124c832…` | 0.831 | 0.479 | 0.854 |

(Baseline « toujours pas de panne » : accuracy 0.864, recall 0.)

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je choisis la régression logistique au seuil 0.2 (run `954180d6…`). Elle a le meilleur recall (0.838) : elle manque environ 16 % des pannes, contre 25 % au seuil 0.3. En échange, la precision baisse (0.54), donc il y a plus de fausses alertes, mais une fausse alerte coûte moins cher qu'une panne. La forêt aléatoire n'est **pas** meilleure : à seuil égal, elle a un recall et une precision plus faibles que la logreg (0.728/0.562 contre 0.750/0.622 à 0.3 ; 0.831/0.479 contre 0.838/0.543 à 0.2). Elle est aussi plus lourde. Réduire C (0.01) régularise davantage et fait baisser le recall. On remarque aussi que l'accuracy est trompeuse : la baseline fait déjà 0.864 sans détecter une seule panne.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0`. On y trouve aussi `mlflow==3.18.0`, `numpy==2.4.4`, `pandas==3.0.2`, `skops==0.16.0`, etc. Cela règle le problème du `InconsistentVersionWarning` du TP4 : le wheel déclarait `scikit-learn>=1.5`, pip installait la 1.9.1 et chargeait un modèle entraîné avec la 1.8.0. Maintenant, chaque modèle est enregistré avec la liste exacte des versions qui l'ont produit. On peut recréer l'environnement qui convient pour le charger, et il n'est plus nécessaire de lire `model_info.json`.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Les paramètres, les métriques et les identifiants sont dans la base SQLite `mlflow.db`, dans le dossier courant (`TP/TP5/Kenza ezzahed`). Les artefacts (modèle, `requirements.txt`, `MLmodel`, exemple d'entrée) sont dans `mlruns/1/<run_id>/artifacts/`. Ces fichiers ne vont **pas** dans Git : ils sont dans le `.gitignore`. Ce sont des résultats générés, souvent volumineux (des modèles binaires), qui changent à chaque entraînement. Git versionne le code qui les produit, et MLflow est l'outil fait pour les stocker et les comparer. En équipe, on utiliserait un serveur MLflow partagé.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

C'est la **même** valeur : `73e0b7cb3c6f795c70c3ddf970b99c15`. `file_md5` calcule la même empreinte que DVC. Le run MLflow est donc relié au reçu DVC : à partir d'un run, on sait exactement quelle version des données l'a produit.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Le fichier de données peut être gros (ici 127 Ko, mais souvent des centaines de Mo). Git le gère mal et garderait chaque version pour toujours dans l'historique. DVC stocke le fichier dans son cache et dans le stockage (`dvc push`). Git ne garde que le reçu `.dvc` : 4 lignes avec le md5 et la taille. Ce reçu suffit à retrouver la bonne version (`dvc checkout` / `dvc pull`). D'ailleurs, `data/*.csv` est dans le `.gitignore`.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `3ad35c2 Données v1` | `73e0b7cb` | 5000 |
| v2 | `a306e6a Données v2` | `93fdeef2` | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Après `git checkout 3ad35c2 -- data/sensors.csv.dvc` et `dvc checkout` (`M data\sensors.csv`), le fichier contient **5000** lignes. `git status` montre alors le `.dvc` modifié (l'ancien reçu) : je ne l'ai pas commité. Après `git checkout HEAD -- data/sensors.csv.dvc` et `dvc checkout`, on revient à **8000** lignes.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

```
A       data\sensors.csv
1 file fetched and 1 file added
```

DVC lit le md5 du reçu, télécharge le fichier depuis le stockage (`%USERPROFILE%\dvc-stockage`) dans le cache, puis le replace dans `data/`. On retrouve les 8000 lignes de la v2, et `dvc status` répond « Data and pipelines are up to date ». C'est la situation d'un coéquipier qui clone le dépôt : il a les reçus via Git et récupère les données avec `dvc pull`.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages (logreg, C = 1, seuil 0.3) :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 (`9b6401d4…`) | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 (`89af20e1…`) | `93fdeef2` | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le recall baisse un peu (0.741 contre 0.750) et la precision monte un peu (0.650 contre 0.622). Ces écarts sont faibles, et surtout les deux modèles ne sont **pas évalués sur le même jeu de test** : chaque run est testé sur 20 % de ses propres données. La v2 vient d'une autre graine, avec plus de relevés et un taux de panne différent (12.8 % contre 13.6 %). Les métriques mesurent donc à la fois le modèle et la difficulté du jeu de test. Pour comparer deux modèles, il faut les évaluer sur un même jeu de test fixe, et idéalement répéter la mesure (validation croisée) pour voir si l'écart dépasse le bruit.

## 5. Décision : l'ADR 004

Voir [`000-modele.md`](000-modele.md) : régression logistique, C = 1, seuil 0.2. Run MLflow `954180d6e5ff4ab4b7d5f3967fd1c02c`, données `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (v1).

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   **Git** versionne le **code**, plus les petits reçus `.dvc` des données. **DVC** versionne les **fichiers de données** : il les stocke dans un cache et un stockage partagé, et les retrouve à partir du md5 écrit dans le reçu. **MLflow** garde la trace de chaque **entraînement** (run) : les paramètres, le `data_md5`, les métriques, le modèle et les versions exactes des bibliothèques. Ensemble, ils couvrent les trois choses qui changent en MLOps : le code, les données et le modèle.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de mon PC (`C:\Users\kenza\dvc-stockage`). Ce chemin n'a de sens que sur ma machine, donc il ne doit pas aller dans Git. `--local` l'écrit dans `.dvc/config.local`, qui est ignoré par Git. Pour partager les données avec le groupe, il faudrait un stockage accessible à tous (S3, Google Drive, un serveur SSH ou un dossier réseau), ajouté **sans** `--local` dans `.dvc/config`, qui est commité. Chacun pourrait alors faire `dvc push` et `dvc pull`, avec ses identifiants d'accès gardés dans son `config.local`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le **code** est dans Git (et dans le wheel du TP4). Les **données** sont gérées par DVC : le reçu est dans Git, le fichier est dans le stockage. Le **modèle** est dans MLflow : c'est un run identifié par son `run_id`, avec les **versions exactes** de l'environnement dans le `requirements.txt` du modèle. Le `data_md5` du run fait le lien entre le modèle et ses données.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? **non**. `git status --ignored` les montre comme ignorés : `mlflow.db`, `mlruns/` et `data/*.csv` sont dans le `.gitignore` du TP5, et `.dvc/cache`, `.dvc/tmp` et `.dvc/config.local` sont dans `.dvc/.gitignore`, créé par `dvc init`.

## 8. Ce qui reste flou

Comment partager en pratique un serveur MLflow et un stockage DVC entre les membres du groupe : quel hébergement, et comment gérer les identifiants sans les mettre dans Git ?
