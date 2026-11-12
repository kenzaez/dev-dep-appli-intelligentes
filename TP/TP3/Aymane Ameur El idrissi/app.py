"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)
    # Affiche les principaux indicateurs du jeu de données.
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean() * 100:.1f} %")
    c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    # Regroupe les relevés par tranches pour comparer les taux de panne.
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

    # Compare la température et la vibration, avec une couleur par résultat.
    st.scatter_chart(
        df,
        x="temperature_c",
        y="vibration_mm_s",
        color="failure",
    )


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

    if envoye:
        try:
            # Envoie le relevé à l'API avec l'URL et la clé saisies.
            resultat = MaintaiClient(url, api_key=cle).predict(releve)
        except APIError as exc:
            # L'API a répondu avec un code d'erreur.
            st.warning(f"Erreur API ({exc.status_code}) : {exc.detail}")
        except httpx.HTTPError as exc:
            # La connexion à l'API a échoué.
            st.error(f"API injoignable : {exc}")
        else:
            # Affiche la probabilité et le niveau de risque renvoyés par le modèle.
            pct = resultat["failure_probability"] * 100
            st.metric("Probabilité de panne", f"{pct:.0f} %")
            if resultat["alert"]:
                st.error("ALERTE : risque élevé de panne")
            else:
                st.success("Situation normale")
