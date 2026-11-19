# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** G1  ·  **Membres :** Belayachi Adnane  ·  **Date :** 12/11/2026 10:00

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :
```
5 failed, 18 passed
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

…

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

…

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
| Relevés |5000 |
| Taux de panne |13,6% |
| Température moyenne |59,8 C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

…

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

…

À quoi sert `@st.cache_data` sur la fonction `charger` ?

…

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {"X-API-Key": self.api_key} if self.api_key is not None else {}
    response = self.http.post("/v1/predict", json=reading, headers=headers)
    if response.status_code != 200:
        raise APIError(response.status_code, response.json().get("detail"))
    return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 1.42s
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé |ALERTE |
| valeurs par défaut, fausse clé | erreur 401|
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) |API injoignable |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS concerne le navigateur, port 8051 n'en a pas besoin

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   …
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   …
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   …

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? oui / non

## 7. Ce qui reste flou

…
