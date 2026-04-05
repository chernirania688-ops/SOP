import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# 1. CONFIGURATION
st.set_page_config(page_title="S&OP Agentic AI", layout="wide", page_icon="🏭")

class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# 2. CHARGEMENT DES DONNÉES
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    df_mkt = pd.read_excel(xls, 'Demande'); df_prod = pd.read_excel(xls, 'Production'); df_fin = pd.read_excel(xls, 'Finance_Achats')
    for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()

    # --- SIMULATION ---
    st.title("🏭 S&OP Agentic AI Simulator")
    type_ev = st.radio("Scénario :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"])
    
    # Initialisation data sim
    df_mkt_sim = df_mkt.copy()
    df_prod_sim = df_prod.copy()
    contexte_sim = "SITUATION NORMALE"

    if type_ev == "🔴 Aléa Production":
        pct = st.slider("Baisse capacité (%)", 10, 90, 30)
        df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
        contexte_sim = f"CRISE : Capacité -{pct}%"
    elif type_ev == "🔵 Pic Demande":
        pct = st.slider("Hausse demande (%)", 10, 150, 50)
        df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
        contexte_sim = f"PIC : Demande +{pct}%"
    elif type_ev == "🟣 Personnalisé":
        contexte_sim = st.text_area("Description :", "Ex: Grève...")

    # --- SECTION 3 : ORCHESTRATION AGENTIQUE ---
    st.markdown("---")
    st.subheader("🤖 Intelligence Agentique : Analyse Multi-Agents")

    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        col_log, col_rep = st.columns([1, 1])
        
        with col_log:
            st.info("🧠 **Pensée des Agents en temps réel :**")
            log_placeholder = st.empty()
            sys.stdout = StreamlitRedirect(log_placeholder)
            
            try:
                # Préparation data
                txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(20).to_string()
                txt_prod = df_prod_sim[['Produit', 'Capacity']].head(20).to_string()
                txt_fin = df_fin[['Produit', 'Margin_Unit']].head(20).to_string()

                # DÉFINITION DES TÂCHES (On les nomme pour extraire les sorties)
                task_mkt = Task(description=f"Analyse demande: {txt_mkt}. Contexte: {contexte_sim}", agent=SOP.marketing, expected_output="Rapport Marketing détaillé.")
                task_supply = Task(description=f"Vérifie prod: {txt_prod}. Contexte: {contexte_sim}", agent=SOP.supply, expected_output="Rapport Supply Chain détaillé.")
                task_finance = Task(description=f"Analyse profit: {txt_fin}. Contexte: {contexte_sim}", agent=SOP.finance, expected_output="Analyse financière détaillée.")
                task_final = Task(description="Rédige le Plan S&OP Final. Arbitre selon la marge.", agent=SOP.orchestrator, expected_output="Rapport S&OP Stratégique Complet.")

                crew = Crew(
                    agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator], 
                    tasks=[task_mkt, task_supply, task_finance, task_final],
                    process=Process.sequential
                )

                # Exécution
                crew.kickoff()

                # STOCKAGE DES RÉSULTATS INDIVIDUELS
                st.session_state['outputs'] = {
                    "📢 Analyse Marketing": task_mkt.output.raw,
                    "🏗️ Analyse Supply Chain": task_supply.output.raw,
                    "💰 Analyse Financière": task_finance.output.raw,
                    "🏆 Rapport Final (PIC)": task_final.output.raw
                }
                st.session_state['run_done'] = True

            finally:
                sys.stdout = sys.__stdout__

    # --- AFFICHAGE FILTRÉ DES RÉSULTATS ---
    if st.session_state.get('run_done'):
        st.markdown("---")
        st.subheader("📋 Consultation des rapports")
        
        # Filtre multi-choix
        choix = st.multiselect(
            "Quels rapports souhaitez-vous consulter ?",
            options=list(st.session_state['outputs'].keys()),
            default=["🏆 Rapport Final (PIC)"]
        )

        # Affichage dynamique sous forme d'expanders
        for rapport in choix:
            with st.expander(f"Voir {rapport}", expanded=True):
                st.markdown(st.session_state['outputs'][rapport])
                # Option de téléchargement par rapport
                st.download_button(
                    label=f"📥 Télécharger {rapport}",
                    data=st.session_state['outputs'][rapport],
                    file_name=f"{rapport.replace(' ', '_')}.md",
                    key=f"dl_{rapport}"
                )

else:
    st.info("👋 Veuillez charger le fichier Excel pour commencer.")
