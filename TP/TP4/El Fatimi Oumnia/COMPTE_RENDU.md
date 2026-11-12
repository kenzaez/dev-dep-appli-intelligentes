# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** G1  ·  **Membres :** El Fatimi oumnia ·  **Date :**12/11/2026


> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
FAILED tests/test_package.py::test_installed_version_matches_the_code - importlib.metadata.PackageNotFoundError: No package metadata was found for m...
FAILED tests/test_package.py::test_command_is_declared - AssertionError: assert 'maintai-predict' in ['pyproject-build', 'normalizer'...
=================== 2 failed, 25 passed, 1 warning in 8.71s ====================
```

Quels sont les deux tests qui échouent, et pourquoi ?
- tests et tests_package
- maintai n'est pas installé c pour ca qu'ils échouent
…

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```
dependencies = [
    "pandas>=2.2",
    "numpy>=1.26",
    "scikit-learn>=1.4",
    "joblib>=1.3",
    "httpx>=0.27",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?
ils ne sont pas essentiels pour faire marcher pytest
…

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: TODO : une phrase qui dit ce que fait le package
Home-page: 
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================= 27 passed, 1 warning in 6.37s ==================================
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?
Probabilité de panne : 95 % (ALERTE)
…

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?
[MaintAI] Risque de panne : 95 % (ALERTE).
oui le mess est visible

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
Mode                 LastWriteTime         Length Name                             
----                 -------------         ------ ----                             
-a----        12/11/2026     12:15          11637 maintai-0.2.0-py3-none-any.whl   
-a----        12/11/2026     12:15          12474 maintai-0.2.0.tar.gz             

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

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | |
| après `pip install scikit-learn==1.8.0` | |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?
Il vient du modele qui vient d'etre entrainé c un decalage de version

…

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
requirements.txt fixe des versions exactespour recréer l'environnement où le modèle a été entraîné. dependencies donne des versions minimales

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
pip install -e ne copie rien : il pointe vers mon dossier, donc chaque modification du code est prise en compte tout de suite. Le wheel installe une copie figée 

3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
Un point d'entrée est une ligne qui dit à pip quelle fonction lancer et pip cree maintai-predict.exe dans .venv\Scripts

## 5. Le rendu Git

- Lien de la pull request : …
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? oui / non

## 6. Ce qui reste flou

…
