import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
from io import BytesIO
import matplotlib.pyplot as plt
from collections import defaultdict

# --------------------- CONFIGURATION ---------------------
st.set_page_config(
    page_title="Invoicemeatreader – Analyse de viande",
    page_icon="🥩",
    layout="centered"
)

# --------------------- CONSTANTES ------------------------
VIANDE_KEYWORDS = [
    "viande", "bœuf", "boeuf", "porc", "poulet", "agneau", "dinde", "canard",
    "saucisse", "steak", "jambon", "charcuterie", "côte", "côtelette", "filet",
    "haché", "hachée", "hachées", "hachés", "viande hachée", "préparation hachée",
    "nuggets", "brochette", "rôti", "ribs", "bacon", "lardons", "chipolata", "merguez"
]

FACTEUR_CO2 = {
    "bœuf": 27,
    "porc": 12,
    "volaille": 7,
    "autre": 10
}

LISTE_MAGASINS = [
    "vds", "biofresh", "terra", "terroirist", "le bon pain",
    "intermarché", "restofrais", "vendsyssel"
]

# ------------------ UTILITAIRES --------------------------
def convertir_en_kg(texte):
    total = 0.0
    matches = re.findall(r'([\d\.,]+)\s*(kg|g)', texte.lower())
    for nombre, unite in matches:
        try:
            nombre = float(nombre.replace(",", "."))
        except ValueError:
            continue
        if unite == "g":
            total += nombre / 1000.0
        elif unite == "kg":
            total += nombre
    return total

def deviner_type_viande(ligne):
    ligne = ligne.lower()
    if any(x in ligne for x in ["bœuf", "boeuf", "rumsteck", "entrecôte", "steak", "haché", "veau", "charolais"]):
        return "bœuf"
    elif any(x in ligne for x in ["porc", "saucisse", "jambon", "lardons", "ribs", "filet mignon"]):
        return "porc"
    elif any(x in ligne for x in ["poulet", "volaille", "dinde", "canard", "nuggets", "aiguillette"]):
        return "volaille"
    else:
        return "autre"

def detecter_magasin(texte):
    lignes = texte.strip().split("\n")
    for ligne in lignes[:10]:
        ligne_lower = ligne.lower()
        for magasin in LISTE_MAGASINS:
            if magasin in ligne_lower:
                return magasin.capitalize()
    return "Magasin inconnu"

def analyser_facture(uploaded_file):
    reader = PdfReader(uploaded_file)
    texte_complet = ""
    for page in reader.pages:
        texte_complet += page.extract_text() + "\n"

    nom_magasin = detecter_magasin(texte_complet)
    poids_total = 0.0
    contient_viande = False
    co2_par_type = defaultdict(float)

    for ligne in texte_complet.split("\n"):
        ligne_lower = ligne.lower()
        if any(mot in ligne_lower for mot in VIANDE_KEYWORDS):
            contient_viande = True
            poids_ligne = convertir_en_kg(ligne_lower)
            type_viande = deviner_type_viande(ligne_lower)
            co2_par_type[type_viande] += poids_ligne * FACTEUR_CO2[type_viande]
            poids_total += poids_ligne

    return nom_magasin, contient_viande, round(poids_total, 2), dict(co2_par_type)

# ------------------ INTERFACE ----------------------------
st.markdown("""
    <h1 style='text-align: center;'>🥩 Invoicemeatreader</h1>
    <div style='text-align: center; font-size: 18px; color: # 555;'>
        Analyse automatique de vos factures PDF pour détecter la viande et estimer l'impact carbone
    </div>
    <br>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("📂 Déposez vos factures PDF ici", type="pdf", accept_multiple_files=True)

if uploaded_files:
    resultats = []
    co2_total_par_type = defaultdict(float)

    for fichier in uploaded_files:
        magasin, contient, poids, co2_par_type = analyser_facture(fichier)
        resultats.append({
            "Magasin": magasin,
            "Facture": fichier.name,
            "Contient viande": "Oui" if contient else "Non",
            "Poids total viande (kg)": poids
        })
        for type_viande, co2 in co2_par_type.items():
            co2_total_par_type[type_viande] += co2

    df = pd.DataFrame(resultats)
    st.success("Analyse terminée avec succès ✅")
    st.dataframe(df)

    # ---------- Graphique par magasin ------------
    st.subheader("📊 Poids total de viande par magasin")
    df_viande = df[df["Poids total viande (kg)"] > 0]

    if not df_viande.empty:
        poids_par_magasin = df_viande.groupby("Magasin")["Poids total viande (kg)"].sum().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(poids_par_magasin.index, poids_par_magasin.values, color="#a30000")
        ax.set_ylabel("Poids (kg)")
        ax.set_xlabel("Magasin")
        ax.set_title("Poids total de viande détecté par magasin")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Aucune viande détectée dans les factures téléchargées.")

    # ----------- Sidebar CO2 ---------
    with st.sidebar:
        st.header("🌍 Empreinte carbone estimée")
        total_co2 = sum(co2_total_par_type.values())

        if total_co2 == 0:
            st.info("Aucune viande détectée.")
        else:
            for type_v, co2 in co2_total_par_type.items():
                st.markdown(f"**{type_v.capitalize()}** : {co2:.1f} kg CO₂e")
            st.markdown("---")
            st.success(f"**Total estimé : {total_co2:.1f} kg CO₂e**")
            st.caption("Source : estimations ADEME")

    # ---------- Export Excel -----------
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    st.download_button(
        label="📅 Télécharger le rapport Excel",
        data=output.getvalue(),
        file_name="viande_factures.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Téléversez une ou plusieurs factures PDF pour commencer.")
