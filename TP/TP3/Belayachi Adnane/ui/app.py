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
    # TODO TP3 sprint 1 :
    # 1. Trois indicateurs côte à côte[cite: 3]
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
    c3.metric("Température moy.", round(df.temperature_c.mean(), 1)) 

# 2. Liste déroulante[cite: 3]
    variable = st.selectbox("Variable", FEATURES)

# 3. Le taux de panne par tranche (bar chart)[cite: 3, 4]
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True).failure.mean()
    taux.index = [round(i.mid) for i in taux.index]
    st.bar_chart(taux)
# 4. Nuage de points[cite: 3, 4]
# "une colonne oui/non se lit mieux que 0/1"[cite: 4]
    df["Panne"] = df["failure"].map({0: "Non", 1: "Oui"}) 
    st.scatter_chart(df, x="temperature_c", y="vibration_mm_s", color="Panne")
    st.info("Sprint 1 : les indicateurs et les graphiques viendront ici.")


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
        # TODO TP3 sprint 2 :

        client = MaintaiClient("http://localhost:8000", api_key=cle)

        try:
            res= client.predict(releve)
        except httpx.ConnectError:
            st.error("API injoignable: Uvicorn est il lance?")
        except APIError:
            st.error("Erreur 401: cle API invalide")

        else:
            pct = round(res["failure_probability"] * 100)
            st.metric("Probabilité de panne", f"{pct} %")        
        # Alerte[cite: 5]
            if res["failure_probability"] >= res["threshold"]: 
                st.error(f"ALERTE : au-dessus du seuil ({res['threshold']})")
        st.info("Sprint 2 : la prédiction s'affichera ici.")
