# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** 1  ·  **Membres :** ezzahed kenza  ·  **Date :** 12/11/2026 12:15

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
FAILED tests/test_package.py::test_installed_version_matches_the_code - impor...
FAILED tests/test_package.py::test_command_is_declared - AssertionError: asse...
================== 2 failed, 25 passed, 1 warning in 58.53s ===================
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` échouent :
- `test_installed_version_matches_the_code` : `importlib.metadata.version("maintai")` lève `PackageNotFoundError`. Grâce à `pythonpath = .` dans `pytest.ini`, le code s'importe, mais le package n'est pas **installé** : pip n'a écrit aucune métadonnée (`maintai.dist-info`) dans le `.venv`.
- `test_command_is_declared` : la commande `maintai-predict` n'apparaît pas dans les points d'entrée `console_scripts`. Ils ne sont pas encore déclarés dans `pyproject.toml` (`[project.scripts]`), et le package n'est pas installé.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
    "httpx>=0.27",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` liste uniquement ce dont le code du package a besoin pour fonctionner chez **tout** utilisateur (`dataset`, `data`, `train`, `predict`, `cli`, `client` importent numpy, pandas, scikit-learn, joblib et httpx). `pytest` sert seulement aux développeurs pour tester : il est dans le groupe optionnel `dev`. `fastapi`/`uvicorn` ne servent qu'à la partie `maintai.api` : ils sont dans le groupe optionnel `api` (`pip install maintai[api]`). Ainsi, quelqu'un qui veut seulement la commande `maintai-predict` n'installe pas un serveur web ni un outil de test.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne à partir de relevés de capteurs (modèle, API, CLI)
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
======================= 27 passed, 1 warning in 14.47s ========================
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
Probabilité de panne : 95 % (ALERTE)
C:\Users\kenza\Downloads\TP4\maintai-starter-tp4\maintai\__init__.py
```

Même depuis `%TEMP%`, la commande fonctionne et `maintai` s'importe. Python trouve le code **dans le dossier du projet**, pas dans `site-packages` : `pip install -e .` a seulement placé dans `site-packages` un lien (fichier `.pth` / finder éditable) qui pointe vers `TP4\maintai-starter-tp4`. Le modèle est trouvé car `config.ROOT` est calculé à partir de `__file__`, donc `ROOT / "models"` reste le dossier du projet.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui, le changement est visible immédiatement (`Risque de panne (modifié) : 95 % (ALERTE)`). En mode éditable, pip n'a pas copié le code : il pointe vers les fichiers sources. `maintai-predict.exe` importe `maintai.cli` à chaque lancement et lit donc la version actuelle du fichier. (Message remis à l'original ensuite.)

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
maintai-0.2.0-py3-none-any.whl   11 630 octets
maintai-0.2.0.tar.gz             12 243 octets
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Non : ni `models/`, ni `tests/`, ni `ui/`, ni `data/`. `[tool.setuptools.packages.find] include = ["maintai*"]` ne retient que le dossier `maintai/` et ses sous-packages. Le wheel contient le **code** et les métadonnées (version, dépendances, point d'entrée dans `entry_points.txt`). Le modèle est un artefact produit par l'entraînement : il change sans que le code change, il est volumineux et ne doit pas être figé dans le package. Les tests et l'interface ne servent pas à l'utilisateur du package.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : C:\Users\...\Temp\essai\.venv\Lib\site-packages\models\model.joblib` puis « Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR. » (code de sortie 1) |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | 3 avertissements `InconsistentVersionWarning: Trying to unpickle estimator StandardScaler / LogisticRegression / Pipeline from version 1.8.0 when using version 1.9.1`, puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Le wheel déclare `scikit-learn>=1.5` : pip a installé la dernière version disponible (1.9.1). Le modèle `model.joblib` est un pickle d'objets scikit-learn créés avec la 1.8.0 ; en le relisant avec une autre version, scikit-learn prévient que le comportement peut être incorrect. La ligne `"sklearn_version": "1.8.0"` de `models/model_info.json` indique la version utilisée pour l'entraînement : il faut la même version pour charger le modèle sans risque (d'où les versions figées dans `requirements.txt`).

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` décrit un **environnement** précis et reproductible : toutes les bibliothèques (y compris pytest, fastapi, streamlit, build) avec des versions **exactes** (`==`), celles avec lesquelles le modèle a été entraîné. `dependencies` décrit ce dont le **package** a besoin pour fonctionner, avec des versions **minimales** (`>=`), pour rester compatible avec les autres packages de l'utilisateur ; pip choisit les versions au moment de l'installation.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `-e .` (éditable) installe un lien vers le dossier source : les modifications du code sont prises en compte sans réinstaller, et `config.ROOT` pointe vers le projet. C'est le mode développement. Installer le wheel **copie** les fichiers dans `site-packages` : c'est une version figée, indépendante du dossier source (il faut reconstruire et réinstaller pour voir un changement), et `ROOT` pointe vers `site-packages`, d'où le besoin de `MAINTAI_MODELS_DIR`. C'est ce que reçoit un utilisateur.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   C'est une déclaration `commande = "module:fonction"` : à l'installation, pip génère un petit exécutable qui lance l'interpréteur de l'environnement, importe `maintai.cli` et appelle `main()`, puis renvoie son code de retour comme code de sortie. Pip le crée dans le dossier `Scripts` de l'environnement (ici `.venv\Scripts\maintai-predict.exe`), qui est dans le `PATH` quand le venv est activé.

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? non : ils sont listés dans `.gitignore` (`dist/`, `build/`, `*.egg-info/`), tout comme `models/` et `.venv/`.

## 6. Ce qui reste flou

…
