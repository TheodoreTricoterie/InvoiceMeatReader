import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
from io import BytesIO

VIANDE_KEYWORDS = [
    # génériques
    "viande", "viandes", "produits carnés",

    # types de viande
    "boeuf", "bœuf", "veau", "porc", "poulet", "dinde", "canard", "agneau", "lapin", "gibier",
    "cheval", "chevreau", "cailles", "pintade", "cochon", "charcuterie", "volaille", "volailles", "scampi"

    # morceaux courants
    "entrecôte", "côte", "côtelette", "filet", "rumsteck", "bavette", "aiguillette", "collier",
    "jarret", "épaule", "jambon", "tranche", "steak", "escalope", "tournedos", "roti", "rôti",
    "merguez", "chipolata", "saucisse", "saucisson", "lardon", "lardons", "andouillette", "boudin",

    # préparations
    "haché", "hachée", "hachées", "hachés", "viande hachée", "préparation hachée",
    "boulettes", "burger", "pâté", "terrine", "mousse de foie", "foie", "rillettes", "bolognaise",
    "cordon bleu", "nuggets", "pané", "panés", "panée", "brochette", "brochettes", "grillade",

    # abréviations ou usages pros
    "vh", "vhachée", "v. hachée", "v. haché", "b haché", "p haché", "ssteak", "steack", "bsteak",

    # anglais (si tu reçois des factures étrangères)
    "beef", "pork", "chicken", "lamb", "duck", "goose", "ham", "bacon", "sausage", "meat",
    "turkey", "minced meat", "ground beef", "ground meat", "cold cuts"

        # génériques
    "viande", "viandes", "produits carnés",

    # types de viande
    "boeuf", "bœuf", "veau", "porc", "poulet", "dinde", "canard", "agneau", "lapin", "gibier",
    "cheval", "chevreau", "cailles", "pintade", "cochon", "charcuterie", "volaille", "volailles",

    # morceaux courants
    "entrecôte", "côte", "côtelette", "filet", "rumsteck", "bavette", "aiguillette", "collier",
    "jarret", "épaule", "jambon", "tranche", "steak", "escalope", "tournedos", "roti", "rôti",
    "merguez", "chipolata", "saucisse", "saucisson", "lardon", "lardons", "andouillette", "boudin",

    # préparations
    "haché", "hachée", "hachées", "hachés", "viande hachée", "préparation hachée",
    "boulettes", "burger", "pâté", "terrine", "mousse de foie", "foie", "rillettes", "bolognaise",
    "cordon bleu", "nuggets", "pané", "panés", "panée", "brochette", "brochettes", "grillade",

    # abréviations ou usages pros
    "vh", "vhachée", "v. hachée", "v. haché", "b haché", "p haché", "ssteak", "steack", "bsteak",

    # anglais (si tu reçois des factures étrangères)
    "beef", "pork", "chicken", "lamb", "duck", "goose", "ham", "bacon", "sausage", "meat",
    "turkey", "minced meat", "ground beef", "ground meat", "cold cuts"

    # génériques
    "vlees", "vleeswaren", "vleesproduct", "vleesproducten", "vers vlees",

    # types d’animaux
    "rund", "rundvlees", "kalfs", "kalfsvlees", "varken", "varkensvlees",
    "kip", "kippenvlees", "kalkoen", "eend", "gans", "lam", "lamsvlees", "wild", "konijn", "paard",

    # morceaux et types
    "biefstuk", "entrecote", "filet", "kotelet", "koteletten", "ribstuk", "schenkel",
    "karbonade", "rib", "gehakt", "gehaktbal", "hamburger", "lapje", "vleeslap", "vleesschijf",
    "varkenshaasje", "ossenhaas", "braadstuk", "rollade", "stoofvlees", "stooflapje",

    # préparations et charcuterie
    "worst", "worsten", "saucijs", "saucijzen", "rookworst", "grillworst", "bloedworst",
    "leverworst", "salami", "ham", "hesp", "hespen", "bacon", "spek", "spekreepjes", "lardons",
    "paté", "terrine", "fricandon", "frikandel", "rundgehakt", "kipgehakt", "varkensgehakt",

    # produits transformés
    "kipnuggets", "cordon bleu", "kroket", "vleeskroket", "schnitzel", "spies", "brochette",
    "vleesbrood", "stoofpot", "goulash", "vleessaus",

    # abréviations ou termes commerciaux
    "v gehakt", "r gehakt", "vlees gemengd", "g vlees", "mixgehakt", "vleesmix",

    # anglais sur factures néerlandaises internationales
    "beef", "pork", "chicken", "ham", "bacon", "sausage", "meat", "ground beef", "minced meat"
]




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


def analyser_facture(uploaded_file):
    reader = PdfReader(uploaded_file)
    texte_complet = ""
    for page in reader.pages:
        texte_complet += page.extract_text() + "\n"

    poids_total = 0.0
    contient_viande = False

    for ligne in texte_complet.split("\n"):
        ligne_lower = ligne.lower()
        if any(mot in ligne_lower for mot in VIANDE_KEYWORDS):
            contient_viande = True
            poids_total += convertir_en_kg(ligne_lower)

    return contient_viande, round(poids_total, 2)

st.title("🧾 Analyse de factures : détection de viande et poids total")
st.markdown("Déposez ici vos factures PDF pour détecter automatiquement la viande et calculer le poids total.")

uploaded_files = st.file_uploader("Choisissez une ou plusieurs factures", type="pdf", accept_multiple_files=True)

if uploaded_files:
    resultats = []
    for fichier in uploaded_files:
        contient, poids = analyser_facture(fichier)
        resultats.append({
            "Facture": fichier.name,
            "Contient viande": "Oui" if contient else "Non",
            "Poids total viande (kg)": poids
        })

    df = pd.DataFrame(resultats)
    st.success("Analyse terminée ✅")
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=output.getvalue(),
        file_name="résumé_viande.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
