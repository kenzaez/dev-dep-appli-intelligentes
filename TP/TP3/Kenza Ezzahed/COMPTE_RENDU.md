# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 12/11/2026

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

- `tests/test_client.py` (3 tests) : `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`, car le corps de `predict` n'est pas encore écrit.
- `tests/test_ui.py` (2 tests) : `IndexError` sur `at.metric[...]`. La page n'affiche encore aucun `st.metric` (ni l'indicateur « Relevés », ni la probabilité de panne).

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
Traceback:
  File "...\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Avec `streamlit run`, Python cherche d'abord les modules dans le dossier du script, `TP3\ui\`, où il n'y a pas de dossier `maintai\`. Avec `python -m`, Python ajoute en plus le dossier courant, `TP3\`, à `sys.path`, et c'est là que se trouve `maintai\`. La première commande ne marche donc que si le package est installé (`pip install -e .`, TP4).

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]
st.subheader(f"Taux de panne par tranche de {variable}")
st.bar_chart(taux)

st.subheader("Température / vibration")
nuage = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(nuage, x="temperature_c", y="vibration_mm_s", color="panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente très vite avec la vibration : environ 2 % vers 1 mm/s, 10 % vers 3,4 mm/s, 32 % vers 5,6 mm/s, 66 % vers 7,8 mm/s, 84 % vers 10 mm/s, puis 100 % à partir d'environ 12 mm/s. La température a aussi un effet (de 0 % à environ 37 % entre 27 °C et 91 °C), mais plus faible : **la vibration est la variable qui compte le plus.**

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Ouverture de la page : `relance` s'affiche. Changement de la liste « Variable » : un `relance` de plus. Déplacement du curseur « Température » dans l'onglet « Prédiction » : rien. Clic sur « Prédire » : un `relance` de plus.

Streamlit réexécute tout le script, de la première à la dernière ligne, à chaque interaction avec un widget. Les curseurs de l'onglet « Prédiction » sont dans un `st.form` : les déplacer ne relance rien, et seul le bouton « Prédire » provoque une relance.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Comme le script est relancé à chaque clic, le CSV serait relu à chaque fois. `@st.cache_data` garde le résultat en mémoire : le fichier n'est lu qu'au premier appel (pour un même chemin), puis le même DataFrame est réutilisé, ce qui rend la page rapide.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text
        raise APIError(r.status_code, detail)
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | « Probabilité de panne : 95 % », puis un message rouge « ALERTE : au-dessus du seuil 0.3 » |
| valeurs par défaut, fausse clé | message jaune « Erreur 401 : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | message rouge « API injoignable : uvicorn est-il lancé ? » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une règle appliquée par le **navigateur** : c'est lui qui bloque un `fetch` venant d'une page d'une autre origine. Avec Streamlit, le navigateur n'appelle jamais l'API. C'est le serveur Streamlit, en Python (`httpx`), qui envoie la requête, comme le ferait `curl` ou le programme Java, sans en-tête `Origin` ni requête `OPTIONS`. CORS ne s'applique donc pas. La sécurité repose toujours sur la clé API, qui reste vérifiée.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, c'est le navigateur de l'utilisateur (le `fetch` JavaScript s'exécute dans la page). Dans Streamlit, c'est le serveur Streamlit (le processus Python, via `MaintaiClient` et `httpx`). Le navigateur ne fait qu'afficher la page.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   On donne à `MaintaiClient` le `TestClient` de FastAPI par le paramètre `http=`. Les requêtes vont directement à l'application en mémoire, sans réseau ni serveur. C'est pour cela que `predict` doit utiliser `self.http.post` et pas `httpx.post`.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration, Streamlit : tout est en Python, les graphiques sont prêts en quelques lignes, et la démo peut être construite en une séance. Pour l'application d'un technicien, plutôt une page HTML/JavaScript (ou une vraie application) : interface sur mesure, plus légère, adaptée au mobile, sans serveur Python par utilisateur. Streamlit relance tout le script à chaque clic et se personnalise peu.

## 6. Le rendu Git

- Lien de la pull request : …
- Le tag `tp3` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? non (ils sont exclus par le `.gitignore`)

## 7. Ce qui reste flou

…
