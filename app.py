import streamlit as st
import pandas as pd
from crewai import Crew, Process, Task
import SOP  # Importation des agents depuis SOP.py

st.set_page_config(page_title="IA Agentique S&OP Pro", layout="wide", page_icon="📊")

# --- STYLE ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Pilotage Stratégique S&OP")
st.markdown("### Orchestration Multi-Agents & Optimisation de la Performance")

# --- BARRE LATÉRALE ---
st.sidebar.header("📂 Gestion des Données")
uploaded_file = st.sidebar.file_uploader("Charger le fichier SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        # 1. Lecture du fichier
        xls = pd.ExcelFile(uploaded_file)
        
        # 2. Aperçu des onglets
        onglet = st.sidebar.selectbox("Visualiser les données", xls.sheet_names)
        df_preview = pd.read_excel(xls, onglet)
        st.sidebar.write(df_preview)

        # 3. Extraction des données pour les agents
        data_mkt = pd.read_excel(xls, 'Demande').to_string()
        data_prod = pd.read_excel(xls, 'Production').to_string()
        data_fin = pd.read_excel(xls, 'Finance_Achats').to_string()

        # --- ZONE CENTRALE ---
        col_cmd, col_res = st.columns([1, 2])

        with col_cmd:
            st.success("✅ Fichier Excel prêt")
            if st.button("🚀 Générer le Rapport S&OP"):
                with st.spinner("🧠 Collaboration des agents en cours..."):
                    
                    # --- DÉFINITION DES TÂCHES AMÉLIORÉES (NIVEAU EXPERT) ---
                    
                    t1 = Task(description=f"Analyse DEMANDE : {data_mkt}. Liste les volumes par produit.", 
                              expected_output="Résumé précis de la demande.", agent=SOP.marketing)
                    
                    t2 = Task(description=f"Valide les volumes de vente finaux à partir de : {data_mkt}.", 
                              expected_output="Chiffres de ventes validés.", agent=SOP.sales)

                    t3 = Task(description=f"Compare ventes vs PRODUCTION : {data_prod}. Calcule le TAUX D'UTILISATION (Demande/Capacité).", 
                              expected_output="Analyse de saturation usine.", agent=SOP.supply)

                    t4 = Task(description=f"Analyse ACHATS : {data_fin}. Alerte sur les délais > 30 jours.", 
                              expected_output="Rapport de risques supply.", agent=SOP.purchasing)

                    t5 = Task(description=f"Calcul FINANCE : Utilise {data_fin}. CALCULE : (Volume x Marge unitaire) pour chaque produit. Donne le PROFIT TOTAL.", 
                              expected_output="Bilan financier chiffré.", agent=SOP.finance)

                    t6 = Task(description=f"""Rédige le Rapport Stratégique S&OP Final en suivant ce plan :
                              1. EXÉCUTIF SUMMARY (3 phrases)
                              2. TABLEAU DE LA DEMANDE (Volumes validés)
                              3. ANALYSE CAPACITÉ (Taux d'utilisation et Goulots)
                              4. PERFORMANCE FINANCIÈRE (Profit total calculé)
                              5. PLAN D'ACTION (3 décisions clés)
                              Utilise un format professionnel avec des titres et du gras.""", 
                              expected_output="Rapport S&OP de haute qualité.", agent=SOP.orchestrator)

                    # Exécution du Crew
                    equipe = Crew(
                        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                        tasks=[t1, t2, t3, t4, t5, t6],
                        process=Process.sequential
                    )

                    resultat = equipe.kickoff()
                    st.session_state['resultat_sop'] = str(resultat)

        with col_res:
            st.subheader("📋 Rapport de Décision")
            if 'resultat_sop' in st.session_state:
                st.markdown(st.session_state['resultat_sop'])
                st.download_button("📥 Télécharger le Plan PIC", st.session_state['resultat_sop'], "Rapport_SOP_Expert.txt")
            else:
                st.info("Cliquez sur le bouton vert pour lancer l'analyse.")

    except Exception as e:
        # C'est ce bloc 'except' qui manquait dans votre code précédent !
        st.error(f"⚠️ Erreur système : {e}")
        st.warning("Assurez-vous que votre fichier contient les onglets : Demande, Production, Finance_Achats")

else:
    st.info("👋 Bienvenue ! Veuillez importer votre fichier Excel dans la barre latérale pour démarrer le cycle S&OP.")

st.divider()
st.caption("Projet PFA - Orchestration Agentic AI - Propulsé par Groq & CrewAI")
