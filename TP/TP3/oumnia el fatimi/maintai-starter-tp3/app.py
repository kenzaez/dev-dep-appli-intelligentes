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
        client = MaintaiClient(url, api_key=cle)
        try:
            resultat = client.predict(releve)
        except APIError as e:
            st.warning(f"Erreur API {e.status_code} : {e.detail}")
        except httpx.HTTPError:
            st.error("API injoignable. Vérifie l'URL et que le serveur est lancé.")
        else:
            proba = resultat["failure_probability"]
            st.metric("Probabilité de panne", f"{proba * 100:.0f} %")
            if resultat["alert"]:
                st.error("ALERTE : risque de panne élevé, prévoir une maintenance.")
            else:
                st.success("Fonctionnement normal.")