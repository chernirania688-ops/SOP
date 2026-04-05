import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# 1. CONFIGURATION
st.set_page_config(page_title="S&OP Agentic AI Platform", layout="wide", page_icon="🏭")

class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# 2. BARRE LATÉRALE
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file:
    # --- CHARGEMENT ET NETTOYAGE ---
    xls = pd.ExcelFile(uploaded_file)
    df_mkt = pd.read_excel(xls, 'Demande'); df_prod = pd.read_excel(xls, 'Production'); df_fin = pd.read_excel(xls, 'Finance_Achats')
    for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()

    st.title("🏭 Pilotage Stratégique S&OP")

    # --- SECTION 1 : SIMULATEUR DE SCÉNARIOS (WHAT-IF) ---
    with st.container(border=True):
        st.subheader("🎭 Gestionnaire de Scénarios")
        col_sc1, col_sc2 = st.columns([1, 2])
        
        with col_sc1:
            type_ev = st.radio("Événement :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"])
        
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()
        contexte_sim = "SITUATION NORMALE"

        with col_sc2:
            if type_ev == "🔴 Aléa Production":
                pct = st.slider("Baisse capacité (%)", 10, 90, 30)
                df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
                contexte_sim = f"CRISE : Capacité -{pct}%"
                st.warning(contexte_sim)
            elif type_ev == "🔵 Pic Demande":
                pct = st.slider("Hausse demande (%)", 10, 150, 50)
                df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
                contexte_sim = f"PIC : Demande +{pct}%"
                st.info(contexte_sim)
            elif type_ev == "🟣 Personnalisé":
                txt = st.text_area("Décrivez l'événement :", "Ex: Grève des dockers...")
                contexte_sim = f"ÉVÉNEMENT : {txt}"

    # --- SECTION 2 : LE DASHBOARD ET LES KPIs (CE QUE VOUS CHERCHIEZ) ---
    st.markdown("---")
    st.subheader("📊 Diagnostic Visuel (Impact du Scénario)")
    
    # Calculs KPIs
    demand_sim = df_mkt_sim['Forecast'].sum()
    capa_sim = df_prod_sim['Capacity'].sum()
    sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0
    profit_pot = (df_mkt_sim['Forecast'] * df_fin['Margin_Unit']).sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Demande Totale", f"{demand_sim:,.0f} u")
    k2.metric("Capacité Totale", f"{capa_sim:,.0f} u")
    k3.metric("Saturation", f"{sat_sim:.1f}%", f"{sat_sim-100:.1f}%", delta_color="inverse")
    k4.metric("Profit Potentiel", f"{profit_pot:,.0f} €")

    # Graphiques
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        # Comparaison Offre/Demande
        fig_bal = go.Figure()
        fig_bal.add_trace(go.Bar(x=df_mkt_sim['Produit'], y=df_mkt_sim['Forecast'], name='Demande', marker_color='#e74c3c'))
        fig_bal.add_trace(go.Bar(x=df_prod_sim['Produit'], y=df_prod_sim['Capacity'], name='Capacité', marker_color='#2ecc71'))
        fig_bal.update_layout(title="Équilibre Offre/Demande par Produit", barmode='group', height=350)
        st.plotly_chart(fig_bal, use_container_width=True)

    with col_g2:
        # Treemap Profit
        df_profit = pd.merge(df_mkt_sim, df_fin, on='Produit')
        df_profit['Profit_Total'] = df_profit['Forecast'] * df_profit['Margin_Unit']
        fig_tree = px.treemap(df_profit, path=['Produit'], values='Profit_Total', color='Margin_Unit',
                              color_continuous_scale='RdYlGn', title="Poids Économique par Produit")
        st.plotly_chart(fig_tree, use_container_width=True)

    # --- SECTION 3 : ORCHESTRATION IA ---
    st.markdown("---")
    st.subheader("🤖 Analyse Agentique : Arbitrage & Décision")

    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        col_log, col_rep = st.columns([1, 1])
        
        with col_log:
            st.info("🧠 Pensée des Agents...")
            log_placeholder = st.empty()
            sys.stdout = StreamlitRedirect(log_placeholder)
            
            try:
                # Optimisation data pour Groq (Head 15)
                txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(15).to_string()
                txt_prod = df_prod_sim[['Produit', 'Capacity']].head(15).to_string()
                txt_fin = df_fin[['Produit', 'Margin_Unit']].head(15).to_string()

                # Tâches
                t_mkt = Task(description=f"Analyse demande: {txt_mkt}. Contexte: {contexte_sim}", agent=SOP.marketing, expected_output="Rapport demande.")
                t_supply = Task(description=f"Vérifie prod: {txt_prod}. Contexte: {contexte_sim}", agent=SOP.supply, expected_output="Faisabilité.")
                t_finance = Task(description=f"Finance sur: {txt_fin}.", agent=SOP.finance, expected_output="Bilan financier.")
                t_final = Task(description="Plan S&OP Final. Arbitre selon la marge.", agent=SOP.orchestrator, expected_output="Plan S&OP Stratégique.")

                crew = Crew(agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator], tasks=[t_mkt, t_supply, t_finance, t_final])
                crew.kickoff()

                st.session_state['outputs'] = {
                    "📢 Marketing": t_mkt.output.raw,
                    "🏗️ Supply": t_supply.output.raw,
                    "💰 Finance": t_finance.output.raw,
                    "🏆 Rapport Final": t_final.output.raw
                }
                st.session_state['run_done'] = True
            finally:
                sys.stdout = sys.__stdout__

    # --- CONSULTATION DES RÉSULTATS ---
    if st.session_state.get('run_done'):
        choix = st.multiselect("Rapports à consulter :", options=list(st.session_state['outputs'].keys()), default=["🏆 Rapport Final"])
        for r in choix:
            with st.expander(f"Voir {r}", expanded=True):
                st.markdown(st.session_state['outputs'][r])

else:
    st.info("👋 Veuillez charger le fichier Excel pour commencer.")
