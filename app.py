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
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')
        
        # Nettoyage
        for df in [df_mkt, df_prod, df_fin]:
            df.columns = df.columns.str.strip()

        # INITIALISATION DES VARIABLES DE SIMULATION
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()
        contexte_simulation = "SITUATION NORMALE"

        # 2. FILTRE PAR PRODUIT (Visualisation uniquement)
        st.subheader("🔍 Analyse et Simulation")
        liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
        selected_prod = st.selectbox("Filtrer la vue par produit :", liste_produits)

        # 3. SCÉNARIOS (Modifient les données simulées)
        type_evenement = st.radio("Type d'événement à simuler :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"], horizontal=True)

        if type_evenement == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30)
            df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
            contexte_simulation = f"CRISE : Capacité usine réduite de {pct}%."
        elif type_evenement == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 100, 40)
            df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
            contexte_simulation = f"PIC : Hausse soudaine de la demande de {pct}%."
        elif type_evenement == "🟣 Personnalisé":
            txt = st.text_area("Description :", "Grève logistique...")
            contexte_simulation = f"ÉVÉNEMENT : {txt}"

        # Filtrage pour la vue graphique
        if selected_prod == "Tous les produits":
            view_mkt, view_prod, view_fin = df_mkt_sim, df_prod_sim, df_fin
            view_mkt_init = df_mkt # Pour le calcul du delta
        else:
            view_mkt = df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
            view_prod = df_prod_sim[df_prod_sim['Produit'] == selected_prod]
            view_fin = df_fin[df_fin['Produit'] == selected_prod]
            view_mkt_init = df_mkt[df_mkt['Produit'] == selected_prod]

        # 4. KPIs DYNAMIQUES
        demand_initial = view_mkt_init['Forecast'].sum()
        demand_sim = view_mkt['Forecast'].sum()
        capa_sim = view_prod['Capacity'].sum()
        sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0

        st.markdown("### 📊 Indicateurs de Performance")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Demande", f"{demand_sim:,.0f}", f"{demand_sim - demand_initial:,.0f}")
        k2.metric("Capacité", f"{capa_sim:,.0f}")
        k3.metric("Saturation", f"{sat_sim:.1f}%", delta=f"{sat_sim-100:.1f}%", delta_color="inverse")
        k4.metric("CA Potentiel", f"{(view_mkt['Forecast'] * view_fin['Margin_Unit']).sum():,.0f} €")

        # 5. GRAPHIQUES
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_bal = go.Figure()
            fig_bal.add_trace(go.Bar(x=view_prod['Produit'], y=view_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
            fig_bal.add_trace(go.Bar(x=view_mkt['Produit'], y=view_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
            fig_bal.update_layout(title="Capacité vs Demande", barmode='overlay', height=350)
            st.plotly_chart(fig_bal, use_container_width=True)

        with col_g2:
            df_matrix = pd.merge(view_mkt, view_fin, on='Produit')
            fig_scatter = px.scatter(df_matrix, x='Forecast', y='Margin_Unit', size='Forecast', color='Margin_Unit', 
                                   text='Produit', color_continuous_scale='RdYlGn', title="Matrice Priorisation")
            fig_scatter.update_layout(height=350)
            st.plotly_chart(fig_scatter, use_container_width=True)

        # 6. LANCEMENT IA
        st.markdown("---")
        if st.button("🚀 Lancer l'Analyse Agentique S&OP", use_container_width=True):
            col_log, col_rep = st.columns(2)
            with col_log:
                st.info("🤖 Logique des agents...")
                log_placeholder = st.empty()
                redir = StreamlitRedirect(log_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir
                try:
                    # On envoie les données SIMULÉES à l'IA
                    txt_mkt = df_mkt_sim.head(15).to_string()
                    txt_prod = df_prod_sim.head(15).to_string()
                    txt_fin = df_fin.head(15).to_string()

                    t1 = Task(description=f"Analyse demande: {txt_mkt}. Contexte: {contexte_simulation}", agent=SOP.marketing, expected_output="Analyse marketing.")
                    t2 = Task(description=f"Vérifie faisabilité prod: {txt_prod}", agent=SOP.supply, expected_output="Plan prod.")
                    t3 = Task(description=f"Calcule impact financier: {txt_fin}", agent=SOP.finance, expected_output="Bilan €.")
                    t4 = Task(description="Arbitre et crée le plan final.", agent=SOP.orchestrator, expected_output="Plan S&OP.")

                    crew = Crew(agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator], tasks=[t1, t2, t3, t4])
                    resultat = crew.kickoff()
                    st.session_state['res_sop'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

            with col_rep:
                st.subheader("📋 Rapport de Décision")
                if 'res_sop' in st.session_state:
                    st.markdown(st.session_state['res_sop'])

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
else:
    st.info("👋 Chargez un fichier Excel pour démarrer.")
