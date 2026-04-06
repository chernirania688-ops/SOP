import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# --- REDIRECTION DES LOGS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")

# --- SIDEBAR ET CHARGEMENT ---
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')
        for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"❌ Erreur : {e}"); st.stop()

    st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
    
    # --- FILTRE PRODUIT ---
    selected_prod = st.selectbox("🔍 Analyser un produit spécifique :", ["Tous les produits"] + list(df_mkt['Produit'].unique()))
    
    df_mkt_sim = df_mkt.copy(); df_prod_sim = df_prod.copy(); df_fin_sim = df_fin.copy()
    contexte_sim = "SITUATION NORMALE"

    # --- SIMULATEUR ---
    with st.container(border=True):
        st.subheader("🎭 Gestionnaire de Scénarios")
        type_ev = st.radio("Sélectionnez un événement :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"], horizontal=True)
        if type_ev == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30)
            df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
            contexte_sim = f"CRISE : Capacité réduite de {pct}%."
        elif type_ev == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 150, 50)
            df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
            contexte_sim = f"PIC : Hausse demande de {pct}%."
        elif type_ev == "🟣 Personnalisé":
            txt = st.text_area("Description :", "Ex: Grève des dockers...")
            contexte_sim = f"ÉVÉNEMENT : {txt}"

    # --- DASHBOARD (KPIs & GRAPHES) ---
    v_mkt = df_mkt_sim if selected_prod == "Tous les produits" else df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
    v_prod = df_prod_sim if selected_prod == "Tous les produits" else df_prod_sim[df_prod_sim['Produit'] == selected_prod]
    v_fin = df_fin_sim if selected_prod == "Tous les produits" else df_fin_sim[df_fin_sim['Produit'] == selected_prod]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Demande", f"{v_mkt['Forecast'].sum():,.0f}")
    k2.metric("Capacité", f"{v_prod['Capacity'].sum():,.0f}")
    k3.metric("Saturation", f"{(v_mkt['Forecast'].sum()/v_prod['Capacity'].sum()*100):.1f}%" if v_prod['Capacity'].sum()>0 else "0%")
    k4.metric("Profit", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
        fig.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
        fig.update_layout(title="Équilibre Offre/Demande", barmode='overlay')
        st.plotly_chart(fig, use_container_width=True)
    with col_g2:
        df_p = pd.merge(v_mkt, v_fin, on='Produit'); df_p['M_Totale'] = df_p['Forecast'] * df_p['Margin_Unit']
        st.plotly_chart(px.treemap(df_p, path=['Produit'], values='M_Totale', title="Répartition Marge"), use_container_width=True)

    # --- LANCEMENT IA (Pleine Largeur) ---
    st.markdown("---")
    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        st.info("🧠 Les 6 agents négocient sur toute la page...")
        log_placeholder = st.empty()
        redir = StreamlitRedirect(log_placeholder); sys.stdout = redir
        
        try:
            # Réduction data pour Rate Limit
            t_m = df_mkt_sim.head(10).to_string(); t_p = df_prod_sim.head(10).to_string(); t_f = df_fin.head(10).to_string()

            t1 = Task(description=f"Marketing: Analyse {t_m}.", agent=SOP.marketing, expected_output="Analyse.")
            t2 = Task(description="Ventes: Valide volumes.", agent=SOP.sales, expected_output="Ventes.")
            t3 = Task(description=f"Supply: Gère goulots {t_p}.", agent=SOP.supply, expected_output="Production.")
            t4 = Task(description=f"Achats: Risques {t_f}.", agent=SOP.purchasing, expected_output="Achats.")
            t5 = Task(description=f"Finance: Profit {t_f}.", agent=SOP.finance, expected_output="Finance.")
            t6 = Task(description=f"Directeur: Arbitre PIC pour {contexte_sim}. FINIR PAR UN TABLEAU.", agent=SOP.orchestrator, expected_output="Plan Final.")

            crew = Crew(agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator], tasks=[t1,t2,t3,t4,t5,t6])
            crew.kickoff()

            st.session_state['outputs'] = {
                "📢 Marketing": t1.output.raw, "🤝 Ventes": t2.output.raw, "🏗️ Supply": t3.output.raw,
                "📦 Achats": t4.output.raw, "💰 Finance": t5.output.raw, "🏆 Rapport Final": t6.output.raw
            }
            st.session_state['run_done'] = True
        finally: sys.stdout = sys.__stdout__

    # --- CONSULTATION DES RAPPORTS ---
    if st.session_state.get('run_done'):
        st.markdown("---")
        choix = st.multiselect("Afficher les rapports :", options=list(st.session_state['outputs'].keys()), default=["🏆 Rapport Final"])
        for r in choix:
            with st.expander(f"Consulter {r}", expanded=True):
                st.markdown(st.session_state['outputs'][r])
else:
    st.info("👋 Veuillez charger le fichier Excel.")
