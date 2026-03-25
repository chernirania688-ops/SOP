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

                # Tâche 5 : Utilise l'onglet FINANCE_ACHATS (Partie Finance)
                t5 = Task(description=f"Utilise MARGIN_UNIT dans : {data_fin} pour calculer le profit total du plan validé.", 
                          expected_output="Bilan financier (Marge totale).", agent=SOP.finance)

                # Tâche 6 : SYNTHÈSE TOTALE (L'Orchestrateur)
                t6 = Task(description="""Rédige le rapport S&OP final. 
                          Tu DOIS inclure ces 3 points obligatoirement :
                          1. Volumes validés (issus de l onglet Demande)
                          2. Alertes Capacités (issues de l onglet Production)
                          3. Rentabilité et Risques Achats (issus de l onglet Finance_Achats)
                          REMARQUE : Ne parle pas de musique ou de cinéma, reste sur les données techniques.""", 
                          expected_output="Plan Industriel et Commercial (PIC) Final.", agent=SOP.orchestrator)

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