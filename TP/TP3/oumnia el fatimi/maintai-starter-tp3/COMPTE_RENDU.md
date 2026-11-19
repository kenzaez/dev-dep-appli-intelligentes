# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** G1  ·  **Membres :** Oumnia El Fatimi  ·  **Date :** 12/11/2026 10:00

> Les observations qui n'ont pas pu être vérifiées dans cette copie sont signalées comme telles.

## 1. Mise en place (dans `TP/TP3`)

Au premier essai, `python -m pytest -q` ne pouvait pas démarrer, car pytest n'était pas installé :

```
ModuleNotFoundError: No module named 'pytest'
```

Après l'installation des dépendances du projet (`python -m pip install -r requirements.txt`), une exécution intermédiaire a échoué dans `tests/test_ui.py::test_ui_shows_the_prediction` : l'interface affichait `95%` alors que le test attendait `95 %`. L'espace a été ajouté. Le résultat final est donné à la section 4.

## 2. Lancer Streamlit

L'interface a été lancée avec `python -m streamlit run ui/app.py` sur le port 8502. Le serveur a répondu `HTTP 200` sur son point de santé. Le test automatisé de l'interface a également réussi.

La commande `streamlit run ui/app.py` seule n'a pas été vérifiée séparément. Si Windows ne trouve pas la commande `streamlit` dans le `PATH`, `python -m streamlit` permet d'utiliser Streamlit depuis l'interpréteur Python courant.

Pour lancer l'API depuis la racine du projet :

```powershell
python -m uvicorn maintai.api.main:app --reload
```

Il faut se placer dans `maintai-starter-tp3` avant de lancer ces commandes. Depuis le dossier parent, Python ne trouve pas le module `maintai`.

## 3. Sprint 1 : l'onglet « Données »

Code de l'onglet « Données » :

```python
with onglet_donnees:
    df = charger(get_settings().data_path)
    a, b, c = st.columns(3)
    a.metric("Relevés", f"{len(df)}")
    b.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    variable = st.selectbox("Variable à analyser", FEATURES)
    tranches = pd.cut(df[variable], bins=10)
    taux_par_tranche = df.groupby(tranches, observed=True)["failure"].mean()
    taux_par_tranche.index = taux_par_tranche.index.astype(str)
    st.subheader(f"Taux de panne selon {variable}")
    st.bar_chart(taux_par_tranche)

    nuage = df.assign(etat=df["failure"].map({0: "normal", 1: "panne"}))
    st.subheader("Température et vibration")
    st.scatter_chart(nuage, x="temperature_c", y="vibration_mm_s", color="etat")
```

Indicateurs du jeu de données généré (`data/sensors.csv`, 5 000 relevés) :

| Indicateur | Valeur affichée |
|---|---:|
| Relevés | 5000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

Avec `vibration_mm_s`, le taux de panne augmente nettement dans les tranches de vibration supérieures. Il est d'environ 2 % dans la tranche la plus basse, dépasse 60 % autour de 6,7–8,9 mm/s, puis dépasse 80 % au-dessus de 8,9 mm/s. Les données étant synthétiques, cette tendance décrit le jeu fourni, pas nécessairement des machines réelles.

L'essai avec `print("relance")` n'a pas été fait. On s'attend à voir le message réapparaître dans le terminal lors des relances de l'application : Streamlit réexécute le script quand l'utilisateur interagit avec un widget.

`@st.cache_data` conserve le résultat de `charger` pour éviter de relire le CSV à chaque relance tant que ses entrées ne changent pas.

## 4. Sprint 2 : l'onglet « Prédiction »

Méthode `predict` de `maintai/client.py` :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {"X-API-Key": self.api_key} if self.api_key is not None else {}
    response = self.http.post("/v1/predict", json=reading, headers=headers)
    if response.status_code != 200:
        raise APIError(response.status_code, response.json().get("detail"))
    return response.json()
```

Résultat final de `python -m pytest -q` :

```
23 passed, 1 warning in 11.65s
```

L'avertissement est une dépréciation de Starlette concernant l'utilisation de `httpx` dans son client de test; il n'empêche pas les tests de réussir.

Les appels en direct avec Uvicorn, une vraie clé et une fausse clé n'ont pas été vérifiés. Les tests confirment le comportement du client et l'interface avec une réponse simulée :

| Essai | Résultat vérifié ou attendu |
|---|---|
| Valeurs par défaut, bonne clé | En réponse simulée, l'interface affiche `95 %` et une alerte. À confirmer avec l'API réellement lancée et la clé configurée. |
| Valeurs par défaut, fausse clé | Le test du client confirme une réponse 401; l'interface affiche un avertissement avec le code et le détail de l'API. |
| API arrêtée | Pas testé en direct; une erreur HTTP est interceptée et l'interface indique que l'API est injoignable. |

Le port 8501 n'a pas besoin d'être dans `MAINTAI_CORS_ORIGINS` pour la prédiction Streamlit : c'est le serveur Python de Streamlit qui appelle l'API. Le navigateur n'envoie pas directement la requête à l'API, donc la règle CORS du navigateur ne s'applique pas à cet appel.

## 5. Questions de compréhension

1. Dans la page web du TP2, le JavaScript du navigateur envoie la requête à l'API. Dans Streamlit, le code Python côté serveur envoie la requête avec `MaintaiClient`.
2. `test_client.py` injecte le client de test FastAPI dans `MaintaiClient`. La requête reste dans le processus de test et n'a donc pas besoin d'un serveur Uvicorn séparé.
3. Pour une démonstration rapide à un client, Streamlit est pratique pour construire et modifier une interface de données. Pour une application quotidienne destinée à un technicien, une page web dédiée peut offrir une expérience plus ciblée et un déploiement plus adapté. Le choix dépend des besoins et du contexte.

## 6. Le rendu Git

- Lien de la pull request : non disponible dans cette copie.
- Le tag `tp3` existe sur GitHub : non vérifiable ici.
- `git status` avant le commit : impossible à vérifier, car le dossier fourni n'est pas un dépôt Git. Le fichier `.gitignore` exclut `.env`, `data/*.csv` et `models/`; aucun fichier `.env` n'était présent lors de la vérification.

## 7. Ce qui reste flou

À vérifier avec le groupe : les essais manuels de prédiction avec Uvicorn lancé, la bonne clé et une fausse clé. Les informations de groupe, de membres, de date et le lien de pull request sont également à compléter.
