import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# 1. CONFIGURATION (Pleine page)
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

# 2. CHARGEMENT DONNÉES
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file:
    # Lecture initiale
    xls = pd.ExcelFile(uploaded_file)
    df_mkt = pd.read_excel(xls, 'Demande'); df_prod = pd.read_excel(xls, 'Production'); df_fin = pd.read_excel(xls, 'Finance_Achats')
    for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()

    st.title("🏭 Pilotage Stratégique S&OP")

    # --- BARRE DE FILTRE PRODUIT (Nouveau) ---
    st.markdown("---")
    liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
    selected_prod = st.selectbox("🔍 Filtrer la vue Dashboard par produit :", liste_produits)

    # --- SIMULATEUR DE SCÉNARIO ---
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

    # --- DASHBOARD KPI & GRAPHIQUES (Filtré par Produit) ---
    st.markdown("---")
    st.subheader(f"📊 Diagnostic : {selected_prod}")
    
    # Filtrage des données pour le visuel uniquement
    v_mkt = df_mkt_sim if selected_prod == "Tous les produits" else df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
    v_prod = df_prod_sim if selected_prod == "Tous les produits" else df_prod_sim[df_prod_sim['Produit'] == selected_prod]
    v_fin = df_fin if selected_prod == "Tous les produits" else df_fin[df_fin['Produit'] == selected_prod]

    k1, k2, k3, k4 = st.columns(4)
    dem_val = v_mkt['Forecast'].sum(); cap_val = v_prod['Capacity'].sum()
    k1.metric("Demande", f"{dem_val:,.0f} u")
    k2.metric("Capacité", f"{cap_val:,.0f} u")
    k3.metric("Saturation", f"{(dem_val/cap_val*100):.1f}%" if cap_val > 0 else "0%")
    k4.metric("CA Potentiel", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

    # Graphe Overlay Pleine Largeur
    fig_bal = go.Figure()
    fig_bal.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
    fig_bal.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
    fig_bal.update_layout(title="Équilibre Offre/Demande", barmode='overlay', height=400)
    st.plotly_chart(fig_bal, use_container_width=True)

    # --- SECTION 5 : ORCHESTRATION IA (Pleine Largeur) ---
    st.markdown("---")
    st.subheader("🤖 Analyse Agentique S&OP (Cycle Complet 6 Agents)")

    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        # Utilisation de toute la largeur pour les logs
        st.info("🧠 Les 6 agents négocient le plan final...")
        log_box = st.empty()
        redir = StreamlitRedirect(log_box)
        sys.stdout = redir
        
        try:
            # Réduction data (Head 15) pour éviter Rate Limit
            txt_mkt = df_mkt_sim.sort_values(by='Forecast', ascending=False).head(15)[['Produit', 'Forecast']].to_string()
            txt_prod = df_prod_sim.sort_values(by='Capacity', ascending=True).head(15)[['Produit', 'Capacity']].to_string()
            txt_fin = df_fin.head(15)[['Produit', 'Margin_Unit', 'Supplier_LeadTime']].to_string()

            # TACHES
            t1 = Task(description=f"Marketing: Analyse demande {txt_mkt}.", agent=SOP.marketing, expected_output="Rapport demande.")
            t2 = Task(description=f"Ventes: Valide les volumes finaux terrain.", agent=SOP.sales, expected_output="Rapport ventes.")
            t3 = Task(description=f"Supply: Vérifie faisabilité prod {txt_prod}.", agent=SOP.supply, expected_output="Rapport industriel.")
            t4 = Task(description=f"Achats: Analyse risques composants {txt_fin}.", agent=SOP.purchasing, expected_output="Rapport achats.")
            t5 = Task(description=f"Finance: Bilan rentabilité sur {txt_fin}.", agent=SOP.finance, expected_output="Bilan financier.")
            t6 = Task(description=f"Directeur: Arbitre PIC final pour {contexte_sim}.", agent=SOP.orchestrator, expected_output="Plan S&OP Final.")

            crew = Crew(
                agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                tasks=[t1, t2, t3, t4, t5, t6]
            )
            crew.kickoff()

            # Sauvegarde des 6 rapports
            st.session_state['reports'] = {
                "📢 Analyse Marketing": t1.output.raw,
                "🤝 Analyse Ventes": t2.output.raw,
                "🏗️ Analyse Supply Chain": t3.output.raw,
                "📦 Analyse Achats / Risks": t4.output.raw,
                "💰 Bilan Financier": t5.output.raw,
                "🏆 Plan S&OP Final (Arbitrage)": t6.output.raw
            }
            st.session_state['done'] = True
        finally:
            sys.stdout = sys.__stdout__

    # --- SECTION 6 : CONSULTATION DES RAPPORTS (Multi-choix) ---
    if st.session_state.get('done'):
        st.markdown("---")
        st.subheader("📋 Consultation des rapports par Département")
        choix = st.multiselect(
            "Sélectionnez les rapports à afficher :", 
            options=list(st.session_state['reports'].keys()), 
            default=["🏆 Plan S&OP Final (Arbitrage)"]
        )

        for r in choix:
            with st.expander(f"Consulter : {r}", expanded=True):
                st.markdown(st.session_state['reports'][r])
                st.download_button(f"📥 Télécharger {r}", st.session_state['reports'][r], f"{r}.md")

else:
    st.info("👋 Veuillez charger le fichier Excel pour commencer.")
