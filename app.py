# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
import re
import io

# ↑ Listes de mots-clés par type de produit animal
keywords_boeuf = [
    "boeuf", "bœuf", "veau", "entrecôte", "côte de boeuf", "viande hachée", "steak",
    "steak haché", "charolais", "limousine", "joue de boeuf", "rôti de boeuf",
    "pot-au-feu", "rumsteck", "bourguignon", "paleron", "filet boeuf"
]

keywords_porc = [
    "porc", "cochon", "jambon", "lard", "saucisse", "chipolata", "rôti de porc",
    "côte de porc", "saucisson", "andouillette", "travers de porc", "filet mignon"
]

keywords_volaille = [
    "poulet", "dinde", "canard", "oie", "pintade", "coquelet", "volaille",
    "filet de poulet", "aile de poulet", "magret", "cuisses de canard", "escalope de dinde"
]

keywords_poisson = [
    "poisson", "saumon", "cabillaud", "colin", "thon", "bar", "merlu", "lotte",
    "dorade", "truite", "espadon", "maquereau", "hareng", "filet de poisson", "morue", "lieu"
]

keywords_fruits_de_mer = [
    "crevette", "crevettes", "moule", "moules", "coquille saint-jacques", "huitre", "huîtres",
    "palourde", "crabe", "langoustine", "homard", "bulot", "tourteau", "fruits de mer"
]

# Coefficients CO2 estimés en kg CO2 / kg produit
co2_coeffs = {
    "bœuf": 27,
    "porc": 6,
    "volaille": 5,
    "poisson": 5,
    "fruits de mer": 10
}

# ↑ Extraction du type de produit

def deviner_type_viande(ligne):
    ligne = ligne.lower()
    if any(mot in ligne for mot in keywords_boeuf):
        return "bœuf"
    elif any(mot in ligne for mot in keywords_porc):
        return "porc"
    elif any(mot in ligne for mot in keywords_volaille):
        return "volaille"
    elif any(mot in ligne for mot in keywords_poisson):
        return "poisson"
    elif any(mot in ligne for mot in keywords_fruits_de_mer):
        return "fruits de mer"
    else:
        return "autre"

# ↑ Extraction du poids en kg depuis une ligne

def convertir_en_kg(ligne):
    poids = re.findall(r"(\d+[\.,]?\d*)\s?(kg|g)", ligne, re.IGNORECASE)
    total = 0.0
    for match in poids:
        nombre, unite = match
        try:
            valeur = float(nombre.replace(",", "."))
            if unite.lower() == "g":
                valeur = valeur / 1000.0
            total += valeur
        except ValueError:
            pass
    return total

# ↑ Analyse d'une facture (PDF)

def analyser_facture(pdf_file):
    reader = PdfReader(pdf_file)
    lignes = []
    for page in reader.pages:
        texte = page.extract_text()
        if texte:
            lignes.extend(texte.split("\n"))

    data = []
    for ligne in lignes:
        type_viande = deviner_type_viande(ligne)
        poids = convertir_en_kg(ligne)
        if type_viande != "autre" and poids > 0:
            data.append((type_viande, poids))

    df = pd.DataFrame(data, columns=["Type", "Poids (kg)"])
    return df.groupby("Type")["Poids (kg)"].sum().reset_index()

# ↑ Interface Streamlit

st.set_page_config(page_title="Invoicemeatreader", layout="wide")
st.title("🥩 Invoicemeatreader – Analyse de l'impact CO2 des achats alimentaires")

uploaded_file = st.file_uploader("✔ Téléverser une facture au format PDF", type="pdf")

if uploaded_file:
    st.success("Fichier bien reçu, analyse en cours...")
    df_resultats = analyser_facture(uploaded_file)

    if not df_resultats.empty:
        # Calcul CO2
        df_resultats["CO2 estimé (kg)"] = df_resultats.apply(
            lambda row: row["Poids (kg)"] * co2_coeffs.get(row["Type"], 0), axis=1
        )

        st.subheader("📊 Résultats de l'analyse")
        st.dataframe(df_resultats)

        # Graphique
        fig, ax = plt.subplots()
        ax.bar(df_resultats["Type"], df_resultats["CO2 estimé (kg)"])
        ax.set_ylabel("CO2 estimé (kg)")
        ax.set_title("Empreinte carbone estimée par type de produit")
        st.pyplot(fig)

        st.sidebar.subheader("🌍 Estimation CO2 totale")
        total_co2 = df_resultats["CO2 estimé (kg)"].sum()
        st.sidebar.metric("Total CO2 estimé", f"{total_co2:.2f} kg")

    else:
        st.warning("Aucune viande, poisson ou fruit de mer détecté.")
