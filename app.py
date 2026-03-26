import streamlit as st
import pandas as pd
from crewai import Crew, Process, Task
import SOP 

st.set_page_config(page_title="S&OP AI System", layout="wide")

st.title("🏭 Système S&OP Multi-Agents")

# --- CHARGEMENT DU FICHIER ---
st.sidebar.header("📁 Importation")
uploaded_file = st.sidebar.file_uploader("Fichier SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        
        # Extraction stricte des 3 sources de données
        data_mkt = pd.read_excel(xls, 'Demande').to_string()
        data_prod = pd.read_excel(xls, 'Production').to_string()
        data_fin = pd.read_excel(xls, 'Finance_Achats').to_string()

        st.sidebar.success("3 Onglets chargés avec succès")

        if st.button("🚀 Lancer l'analyse globale"):
            with st.spinner("Analyse des 3 fichiers en cours..."):
                
                # --- TÂCHES STRICTES ---
                
                # Tâche 1 & 2 : Utilise l'onglet DEMANDE
                t1 = Task(description=f"Analyse l onglet DEMANDE suivant : {data_mkt}. Liste les volumes par produit.", 
                          expected_output="Résumé de la demande brute.", agent=SOP.marketing)
                
                t2 = Task(description=f"Basé sur l analyse marketing, valide un plan de vente final (en unités).", 
                          expected_output="Plan de vente validé.", agent=SOP.sales)

                # Tâche 3 : Utilise l'onglet PRODUCTION
                t3 = Task(description=f"Prends le plan de vente et compare-le à la CAPACITÉ dans : {data_prod}. Identifie les produits en surcharge.", 
                          expected_output="Rapport de faisabilité usine.", agent=SOP.supply)

                # Tâche 4 : Utilise l'onglet FINANCE_ACHATS (Partie Achats)
                t4 = Task(description=f"Vérifie les SUPPLIER_LEADTIME dans : {data_fin}. Quels produits risquent une rupture ?", 
                          expected_output="Analyse des risques achats.", agent=SOP.purchasing)

                # Tâche Finance plus précise
t5 = Task(
    description=f"""Calcule l'impact financier total en utilisant les volumes de l'agent Sales 
    et les données de Finance_Achats : {data_fin}.
    CALCUL OBLIGATOIRE : (Volume Alpha_Phone_15 * 350) + (Volume Alpha_Phone_14 * 150) + ... 
    Donne le Chiffre d'Affaires total et la Marge Totale Globale.""", 
    expected_output="Bilan financier chiffré et détaillé.", 
    agent=SOP.finance
)

# Tâche Orchestrateur avec un Template imposé
t6 = Task(
    description=f"""Rédige le Rapport Stratégique S&OP Final en suivant EXACTEMENT ce plan :
    1. EXÉCUTIF SUMMARY : Résumé de la situation en 3 phrases.
    2. ANALYSE DE LA DEMANDE : Tableau des volumes validés vs prévisions.
    3. CONTRAINTES OPÉRATIONNELLES : Liste des goulots (Production) et risques (Achats). 
       Calcule le taux d'utilisation de l'usine (Demande / Capacité).
    4. BILAN FINANCIER : Chiffre d'Affaires total et Marge bénéficiaire totale.
    5. PLAN D'ACTION (PIC) : Décisions précises pour le mois prochain.
    
    Sois factuel, utilise des puces et des tableaux Markdown.""", 
    expected_output="Rapport S&OP Expert de haute qualité.", 
    agent=SOP.orchestrator
)
                # Exécution
                equipe = Crew(
                    agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                    tasks=[t1, t2, t3, t4, t5, t6],
                    process=Process.sequential
                )

                resultat = equipe.kickoff()
                st.markdown("### 📋 Rapport Stratégique Final (Synthèse des 3 fichiers)")
                st.write(str(resultat))

    except Exception as e:
        st.error(f"Erreur : {e}. Vérifiez que les onglets 'Demande', 'Production' et 'Finance_Achats' existent.")
else:
    st.info("Veuillez importer le fichier Excel pour commencer.")
