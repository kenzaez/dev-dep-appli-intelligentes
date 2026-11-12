# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** G1  ·  **Membres :** AMEUR EL IDRISSI Aymane  ·  **Date :** 12/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` échouent :

- `test_installed_version_matches_the_code` : le package `maintai` n'est pas encore installé avec `pip install -e .` ;
- `test_command_is_declared` : la commande `maintai-predict` n'est pas encore déclarée comme point d'entrée.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
[project]
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

`pytest` est uniquement nécessaire pour développer et tester le projet : il est donc dans
le groupe optionnel `dev`. `fastapi` est nécessaire seulement pour exécuter l'API : il
est donc dans le groupe optionnel `api`. Les dépendances principales contiennent seulement
les bibliothèques nécessaires au fonctionnement du package.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de pannes à partir de relevés de capteurs
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

La commande de prédiction affiche :

```
Probabilité de panne : 95 % (ALERTE)
```

La seconde commande affiche un chemin vers :

```
C:\Users\ayman\Desktop\DevAppInt\TP4\maintai-starter-tp4\maintai\__init__.py
```

Python trouve le code dans le dossier du projet grâce à l'installation éditable
(`pip install -e .`).

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui, le changement est visible. En mode éditable, l'environnement pointe directement
vers le code source du projet au lieu d'en copier une version figée dans
`site-packages`. Il n'est donc pas nécessaire de réinstaller après une modification
du code.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
maintai-0.2.0-py3-none-any.whl
maintai-0.2.0.tar.gz
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

Le modèle, les tests et `ui/` ne sont pas inclus. Le wheel est configuré pour ne
distribuer que le package `maintai*` grâce à `[tool.setuptools.packages.find]`.
Le modèle est un artefact généré séparément et les tests ainsi que l'interface
Streamlit ne font pas partie du package Python principal.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : ...\site-packages\models\model.joblib` puis les instructions pour entraîner le modèle ou définir `MAINTAI_MODELS_DIR` |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)` ; l'avertissement disparaît si la version correspond à celle utilisée pour entraîner le modèle |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Cet avertissement apparaît lorsque le modèle sérialisé avec `joblib` a été
entraîné avec une version de scikit-learn différente de celle utilisée pour le
charger. La ligne concernée est :

```json
"sklearn_version": "1.8.0"
```

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` contient les versions exactes utilisées pour reproduire
   l'environnement du projet. La liste `dependencies` décrit les dépendances
   nécessaires à l'installation du package, avec des versions minimales et sans
   les outils optionnels comme les tests ou l'API.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `pip install -e .` installe le projet en mode éditable : Python utilise
   directement les fichiers sources et les modifications sont immédiatement
   visibles. L'installation du wheel installe une distribution construite et
   figée, indépendante des fichiers sources du projet.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   Un point d'entrée associe une commande shell à une fonction Python. Après
   installation, pip crée `maintai-predict.exe` dans le dossier `Scripts` de
   l'environnement virtuel, par exemple `.venv\Scripts\maintai-predict.exe`.

## 5. Le rendu Git

- Lien de la pull request : 
- Le tag `tp4` existe sur GitHub : 
- `git status` avant le commit : `dist/`, `build/` et
  `maintai.egg-info/` sont ignorés par `.gitignore`

## 6. Ce qui reste flou

