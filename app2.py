import streamlit as st
import pandas as pd
import os
import calendar
import plotly.graph_objects as go
from io import BytesIO
import csv

# Configuration Streamlit
st.set_page_config(page_title="Dashboard Combiné", layout="wide")

# CSS Styling
st.markdown("""
<style>
/* Background and Fonts */
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f7f7f7;
    color: #333;
    margin: 0;
    padding: 0;
}

/* Headers */
h1, h2, h3, .stMarkdown {
    text-align: center;
    color: #4CAF50;
    margin-bottom: 1em;
}

/* File Upload */
.stFileUploader > label {
    font-weight: bold;
    font-size: 1.1em;
    color: #444;
    margin-bottom: 0.5em;
}

/* Buttons */
.stButton button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 10px 20px;
    text-align: center;
    display: inline-block;
    font-size: 16px;
    border-radius: 5px;
    margin: 5px 2px;
    cursor: pointer;
}

.stButton button:hover {
    background-color: #45a049;
}

/* Tables */
[data-testid="stDataFrameContainer"] {
    border-radius: 15px;
    box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
}

/* Expander */
.stExpander {
    border: 1px solid #ddd;
    border-radius: 15px;
    padding: 10px;
    background-color: white;
    box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
}

/* Cards Background */
section.main > div {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.1);
    margin: 15px 0px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Combiné avec Stockage Permanent et Interface Esthétique")

# Fichiers pour le stockage permanent
FILE_APP1 = "data_app1.csv"
FILE_APP2 = "data_app2.csv"

# Fonctions utilitaires pour le stockage
def load_data_app1():
    if os.path.exists(FILE_APP1):
        return pd.read_csv(FILE_APP1, parse_dates=["Sch dep dt with time"])
    else:
        return pd.DataFrame(columns=["Flight No", "Sch dep dt with time", "CAP", "PAX", "COS"])

def save_data_app1(new_data):
    data = load_data_app1()
    combined = pd.concat([data, new_data]).drop_duplicates(subset=["Flight No", "Sch dep dt with time"])
    combined.to_csv(FILE_APP1, index=False)

def load_data_app2():
    if os.path.exists(FILE_APP2):
        return pd.read_csv(FILE_APP2, parse_dates=["Sch Dep Dt"])
    else:
        return pd.DataFrame(columns=["Sch Dep Dt", "Rez Class", "Total Ss Count", "Annee", "Mois"])

def save_data_app2(new_data):
    data = load_data_app2()
    combined = pd.concat([data, new_data], ignore_index=True)
    combined.to_csv(FILE_APP2, index=False)

# Section App1
st.header("📊 Partie 1 : Load Factor Moyen (Radar Chart)")

uploaded_file_app1 = st.file_uploader("📂 Charger un fichier CSV pour la Partie 1", type=["csv", "txt"], key="app1_upload")

if uploaded_file_app1 is not None:
    try:
        df_temp = pd.read_csv(uploaded_file_app1, sep=";")
        df_temp.columns = df_temp.columns.str.strip()

        if "Sch dep dt with time" in df_temp.columns:
            df_temp["Sch dep dt with time"] = pd.to_datetime(df_temp["Sch dep dt with time"], dayfirst=True, errors="coerce")
            df_temp["COS"] = pd.to_numeric(df_temp["COS"], errors="coerce")

            before_count = load_data_app1().shape[0]
            save_data_app1(df_temp)
            after_count = load_data_app1().shape[0]

            added_rows = after_count - before_count
            st.success(f"✅ {added_rows} ligne(s) ajoutée(s) avec succès pour la Partie 1 !")
        else:
            st.error("❌ Colonne 'Sch dep dt with time' introuvable.")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier pour la Partie 1 : {e}")

# Traitement et affichage de la Partie 1
df_app1 = load_data_app1()

if not df_app1.empty:
    df_app1["COS"] = pd.to_numeric(df_app1["COS"], errors="coerce")
    df_app1["Year"] = df_app1["Sch dep dt with time"].dt.year
    df_app1["Month"] = df_app1["Sch dep dt with time"].dt.month.astype("Int64")
    df_app1["Month_name"] = df_app1["Month"].apply(lambda x: calendar.month_abbr[int(x)] if pd.notnull(x) else "")
    df_app1["Month_name"] = pd.Categorical(df_app1["Month_name"], categories=calendar.month_abbr[1:], ordered=True)

    agg = df_app1.groupby(["Year", "Month"], as_index=False)["COS"].mean()
    agg["LF moyen"] = agg["COS"].round(2)
    agg["Mois"] = agg["Month"].apply(lambda x: calendar.month_abbr[x])

    # Création du radar chart Plotly
    fig = go.Figure()

    for year in agg["Year"].unique():
        df_year = agg[agg["Year"] == year]

        fig.add_trace(go.Scatterpolar(
            r=df_year["LF moyen"],
            theta=df_year["Mois"],
            mode='lines+markers',
            name=str(year),
            line=dict(width=2)
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=True,
        title="📊 Load Factor moyen (Radar Chart)",
        margin=dict(t=60, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Voir le tableau résumé de la Partie 1"):
        st.dataframe(agg[["Year", "Mois", "LF moyen"]])
else:
    st.info("📭 Aucune donnée disponible pour la Partie 1. Veuillez charger un fichier.")

# Section App2
st.header("📊 Partie 2 : Analyse de la Part de Classe par Mois avec Accumulation")

uploaded_file_app2 = st.file_uploader("📁 Téléversez un fichier CSV pour la Partie 2", type="csv", key="app2_upload")

if uploaded_file_app2 is not None:
    try:
        # Détection du séparateur
        sample = uploaded_file_app2.read(2048).decode('utf-8')
        uploaded_file_app2.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        sep = dialect.delimiter

        # Lecture et nettoyage du fichier
        df_app2 = pd.read_csv(uploaded_file_app2, sep=sep)
        df_app2.columns = df_app2.columns.str.strip()

        colonnes_requises = ['Sch Dep Dt', 'Rez Class', 'Total Ss Count']
        if not all(col in df_app2.columns for col in colonnes_requises):
            st.error(f"❌ Les colonnes suivantes sont requises : {colonnes_requises}")
        else:
            df_app2 = df_app2[colonnes_requises].dropna()
            df_app2 = df_app2[~df_app2['Sch Dep Dt'].astype(str).str.contains("Report|Total|<b", na=False)]

            df_app2['Sch Dep Dt'] = pd.to_datetime(df_app2['Sch Dep Dt'], dayfirst=True, errors='coerce')
            df_app2.dropna(subset=['Sch Dep Dt'], inplace=True)
            df_app2['Annee'] = df_app2['Sch Dep Dt'].dt.year
            df_app2['Mois'] = df_app2['Sch Dep Dt'].dt.month
            df_app2['Total Ss Count'] = pd.to_numeric(df_app2['Total Ss Count'], errors='coerce')
            df_app2.dropna(subset=['Total Ss Count'], inplace=True)

            # Sauvegarde permanente
            save_data_app2(df_app2)

    except Exception as e:
        st.error(f"❌ Erreur de traitement pour la Partie 2 : {e}")

# Affichage et traitement si données présentes pour la Partie 2
df_app2 = load_data_app2()

if not df_app2.empty:
    total_par_mois = df_app2.groupby(['Annee', 'Mois'])['Total Ss Count'].sum().reset_index()
    total_par_mois.rename(columns={'Total Ss Count': 'Total Mois'}, inplace=True)

    grouped = df_app2.groupby(['Annee', 'Mois', 'Rez Class'])['Total Ss Count'].sum().reset_index()
    grouped = grouped.merge(total_par_mois, on=['Annee', 'Mois'])
    grouped['Part class'] = (grouped['Total Ss Count'] / grouped['Total Mois']) * 100
    grouped['Part class'] = grouped['Part class'].round(2)

    # Affichage tableau
    st.subheader("🧾 Tableau cumulatif de la Part de Classe (%)")
    st.dataframe(grouped[['Annee', 'Mois', 'Rez Class', 'Part class']].rename(columns={'Part class': 'Part (%)'}))

    # Téléchargement
    def convert_df(df):
        output = BytesIO()
        df[['Annee', 'Mois', 'Rez Class', 'Part class']].rename(columns={'Part class': 'Part (%)'}).to_csv(output, index=False)
        return output.getvalue()

    st.download_button(
        label="📥 Télécharger les données cumulées de la Partie 2",
        data=convert_df(grouped),
        file_name="part_class_cumulee.csv",
        mime='text/csv',
    )
else:
    st.info("📭 Aucune donnée disponible pour la Partie 2. Veuillez charger un fichier.")