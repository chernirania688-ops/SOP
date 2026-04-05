import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP
import sys
import re

# --- CLASSE POUR CAPTURER LA DISCUSSION DES AGENTS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("---")

if uploaded_file is not None:
    try:
        # 1. LECTURE DES DONNÉES
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
        df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
        df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

        # 2. KPIs
        st.subheader("📊 Indicateurs Clés")
        k1, k2, k3 = st.columns(3)
        total_demand = df_mkt['Forecast'].sum()
        total_capacity = df_prod['Capacity'].sum()
        k1.metric("Demande", f"{total_demand:,.0f}")
        k2.metric("Capacité", f"{total_capacity:,.0f}")
        k3.metric("Saturation", f"{(total_demand/total_capacity*100):.1f}%")

        # 3. SCÉNARIOS
        st.markdown("---")
        type_evenement = st.radio("Simulation :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"])
        
        contexte_simulation = "SITUATION NORMALE."
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()

        if type_evenement == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30)
            df_prod_sim['Capacity'] = df_prod_sim['Capacity'] * (1 - pct/100)
            contexte_simulation = f"CRISE : Capacité réduite de {pct}%."
        elif type_evenement == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 100, 40)
            df_mkt_sim['Forecast'] = df_mkt_sim['Forecast'] * (1 + pct/100)
            contexte_simulation = f"PIC : Hausse de {pct}%."
        elif type_evenement == "🟣 Personnalisé":
            txt = st.text_area("Description :", "Grève logistique...")
            contexte_simulation = f"ÉVÉNEMENT : {txt}"

        # 4. LANCEMENT IA
        st.markdown("---")
        if st.button("🚀 Analyser le Plan S&OP", use_container_width=True):
            col_log, col_rep = st.columns([1, 1])
            with col_log:
                st.info("🤖 Logique des agents...")
                log_placeholder = st.empty()
                redir = StreamlitRedirect(log_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir
                try:
                    # Optimisation Rate Limit (Head 15)
                    txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(15).to_string()
                    txt_prod = df_prod_sim[['Produit', 'Capacity']].head(15).to_string()
                    txt_fin = df_fin[['Produit', 'Margin_Unit']].head(15).to_string()

                    t1 = Task(description=f"Analyse: {txt_mkt}. Contexte: {contexte_simulation}", agent=SOP.marketing, expected_output="Rapport demande.")
                    t2 = Task(description="Valide volumes.", agent=SOP.sales, expected_output="Volumes validés.")
                    t3 = Task(description=f"Vérifie prod: {txt_prod}.", agent=SOP.supply, expected_output="Faisabilité.")
                    t4 = Task(description="Analyse achats.", agent=SOP.purchasing, expected_output="Risques.")
                    t5 = Task(description=f"Finance: {txt_fin}.", agent=SOP.finance, expected_output="Bilan.")
                    t6 = Task(description="Rapport Final. Arbitre selon marge.", agent=SOP.orchestrator, expected_output="Plan S&OP.")

                    crew = Crew(agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator], tasks=[t1, t2, t3, t4, t5, t6])
                    resultat = crew.kickoff()
                    st.session_state['res'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

            with col_rep:
                if 'res' in st.session_state:
                    st.success("✅ Rapport généré")
                    st.markdown(st.session_state['res'])

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
else:
    st.info("👋 Veuillez charger le fichier Excel.")
