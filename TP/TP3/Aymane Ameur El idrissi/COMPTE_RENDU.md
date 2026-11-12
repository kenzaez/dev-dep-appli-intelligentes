# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** G1  ·  **Membres :** AMEUR EL IDRISSI Aymane  ·  **Date :** 12/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
3 failed, 20 passed, 1 warning
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

Au départ, les trois tests de `tests/test_client.py` échouaient car
`MaintaiClient.predict` levait `NotImplementedError`.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
streamlit : commande introuvable / non reconnue
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

`python -m streamlit` utilise Streamlit installé dans l'environnement virtuel
du projet. La commande `streamlit` seule n'est pas présente dans le `PATH`.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df['failure'].mean() * 100:.1f} %")
c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

variable = st.selectbox("Variable à analyser", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux_par_tranche = (
    df.assign(tranche=tranches)
    .groupby("tranche", observed=False)["failure"]
    .mean()
    .mul(100)
    .rename("Taux de panne (%)")
    .reset_index()
)
taux_par_tranche["tranche"] = taux_par_tranche["tranche"].astype(str)
st.bar_chart(taux_par_tranche, x="tranche", y="Taux de panne (%)")

st.scatter_chart(
    df,
    x="temperature_c",
    y="vibration_mm_s",
    color="failure",
)
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente nettement lorsque la vibration augmente.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Le message `relance` apparaît à chaque modification. Streamlit réexécute
le script lorsque l'utilisateur interagit avec la page.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

`@st.cache_data` mémorise le fichier déjà chargé et évite de relire le CSV à
chaque réexécution si le chemin n'a pas changé.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
headers = {"X-API-Key": self.api_key} if self.api_key else {}
response = self.http.post("/v1/predict", json=reading, headers=headers)
if response.status_code != 200:
    raise APIError(response.status_code, response.json().get("detail"))
return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 % ; **ALERTE** |
| valeurs par défaut, fausse clé | Avertissement API : erreur 401 |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Erreur : API injoignable |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

Les CORS concernent les requêtes des navigateurs. Streamlit envoie la requête
depuis Python vers l'API ; le port 8501 n'a donc pas besoin d'être autorisé
dans `MAINTAI_CORS_ORIGINS`.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, le JavaScript du navigateur envoie la requête. Dans Streamlit,
   c'est le client Python `MaintaiClient` qui l'envoie.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Ils utilisent un `TestClient` qui appelle directement l'application FastAPI
   en mémoire.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration rapide, je choisirais Streamlit car il est simple à
   utiliser et affiche directement les graphiques. Pour une application de
   technicien, je choisirais plutôt HTML + JavaScript, car elle permet une
   interface plus personnalisée et mieux adaptée au téléphone.

## 6. Le rendu Git

- Lien de la pull request : 
- Le tag `tp3` existe sur GitHub : 
- `git status` avant le commit : `.env`, `data/` et `models/` étaient ignorés par Git : oui

## 7. Ce qui reste flou

La différence entre CORS et une requête serveur-à-serveur est maintenant
comprise. Il reste à renseigner le lien de la pull request et à vérifier le
tag `tp3` sur GitHub.
