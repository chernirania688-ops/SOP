import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="S&OP AI Agentic", layout="wide", page_icon="🏭")

class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# 2. CHARGEMENT ET NETTOYAGE
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande'); df_prod = pd.read_excel(xls, 'Production'); df_fin = pd.read_excel(xls, 'Finance_Achats')
        for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"Erreur de fichier : {e}"); st.stop()

    st.title("🏭 Pilotage Stratégique S&OP")

    # --- FILTRE PRODUIT (Ta demande) ---
    st.markdown("---")
    liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
    selected_prod = st.selectbox("🔍 Analyser un produit spécifique :", liste_produits)

    # --- SCÉNARIOS ---
    with st.container(border=True):
        st.subheader("🎭 Gestionnaire de Scénarios")
        type_ev = st.radio("Simulation :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"], horizontal=True)
        
        df_mkt_sim = df_mkt.copy(); df_prod_sim = df_prod.copy()
        contexte_sim = "SITUATION NORMALE"

        if type_ev == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30); df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
            contexte_sim = f"CRISE : Capacité réduite de {pct}%."
        elif type_ev == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 150, 50); df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
            contexte_sim = f"PIC : Hausse demande de {pct}%."
        elif type_ev == "🟣 Personnalisé":
            contexte_sim = st.text_area("Description :", "Ex: Grève des dockers au port...")

    # --- DASHBOARD (Filtré par produit) ---
    v_mkt = df_mkt_sim if selected_prod == "Tous les produits" else df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
    v_prod = df_prod_sim if selected_prod == "Tous les produits" else df_prod_sim[df_prod_sim['Produit'] == selected_prod]
    v_fin = df_fin if selected_prod == "Tous les produits" else df_fin[df_fin['Produit'] == selected_prod]

    k1, k2, k3, k4 = st.columns(4)
    dem_v = v_mkt['Forecast'].sum(); cap_v = v_prod['Capacity'].sum()
    k1.metric("Demande", f"{dem_v:,.0f} u")
    k2.metric("Capacité", f"{cap_v:,.0f} u")
    k3.metric("Saturation", f"{(dem_v/cap_v*100):.1f}%" if cap_v > 0 else "0%")
    k4.metric("CA Potentiel", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

    # Graphiques
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
        fig.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
        fig.update_layout(title="Équilibre Offre/Demande", barmode='overlay', height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df_p = pd.merge(v_mkt, v_fin, on='Produit')
        df_p['Marge_T'] = df_p['Forecast'] * df_p['Margin_Unit']
        st.plotly_chart(px.treemap(df_p, path=['Produit'], values='Marge_T', color='Margin_Unit', title="Répartition de la Marge"), use_container_width=True)

    # --- SECTION IA (Pleine Largeur) ---
    st.markdown("---")
    st.subheader("🤖 Analyse Agentique : Cycle S&OP")

    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        st.info("🧠 Les agents analysent la situation sur toute la page...")
        log_box = st.empty()
        redir = StreamlitRedirect(log_box); sys.stdout = redir
        
        try:
            # OPTIMISATION DONNÉES (Top 5 produits pour éviter RateLimit)
            df_top = df_mkt_sim.sort_values(by='Forecast', ascending=False)
            liste_top = df_top['Produit'].tolist()
            t_mkt = df_top[['Produit', 'Forecast']].to_string()
            t_prod = df_prod_sim[df_prod_sim['Produit'].isin(liste_top)][['Produit', 'Capacity', 'Machine_Status']].to_string()
            t_fin = df_fin[df_fin['Produit'].isin(liste_top)][['Produit', 'Margin_Unit', 'Supplier_LeadTime']].to_string()

            # TACHES
            task1 = Task(description=f"Demande & Ventes: Analyse {t_mkt}. Valide la réalité terrain.", agent=SOP.demand_expert, expected_output="Rapport Marketing/Ventes.")
            task2 = Task(description=f"Ops & Achats: Vérifie {t_prod} et risques composants {t_fin}.", agent=SOP.ops_expert, expected_output="Rapport Industriel/Achats.")
            task3 = Task(description=f"Stratégie: Arbitre PIC final pour {contexte_sim}. FINIR PAR UN TABLEAU DE SYNTHÈSE.", agent=SOP.ceo_expert, expected_output="Plan S&OP Final.")

            crew = Crew(agents=[SOP.demand_expert, SOP.ops_expert, SOP.ceo_expert], tasks=[task1, task2, task3], memory=False)
            crew.kickoff()

            st.session_state['reports'] = {
                "📢 Demande & Ventes": task1.output.raw,
                "🏗️ Opérations & Achats": task2.output.raw,
                "🏆 Rapport S&OP Final": task3.output.raw
            }
            st.session_state['run_done'] = True
        finally: sys.stdout = sys.__stdout__

    # --- CONSULTATION ---
    if st.session_state.get('run_done'):
        st.markdown("---")
        choix = st.multiselect("Afficher les rapports :", options=list(st.session_state['reports'].keys()), default=["🏆 Rapport S&OP Final"])
        for r in choix:
            with st.expander(f"Consulter : {r}", expanded=True):
                st.markdown(st.session_state['reports'][r])

else:
    st.info("👋 Veuillez charger le fichier Excel.")
