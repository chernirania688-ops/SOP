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
with st.sidebar.expander("📖 Format Excel Requis", expanded=False):
     st.write("Onglet Demande: Produit, Forecast, Sales_Orders")
     st.write("Onglet Production: Produit, Capacity, Stock_Level")
     st.write("Onglet Finance_Achats: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")

uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    # --- CHARGEMENT ET NETTOYAGE ---
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')
        
        for df in [df_mkt, df_prod, df_fin]:
            df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"❌ Erreur de lecture du fichier : {e}")
        st.stop()

    # --- AJOUT DU FILTRE PRODUIT ---
    st.markdown("---")
    liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
    selected_prod = st.selectbox("🔍 Analyser un produit spécifique (Vue Dashboard) :", liste_produits)

    # --- INITIALISATION DES VARIABLES DE SIMULATION ---
    df_mkt_sim = df_mkt.copy()
    df_prod_sim = df_prod.copy()
    contexte_simulation = "SITUATION NORMALE"

    # --- SECTION 1 : SIMULATEUR DE SCÉNARIOS ---
    st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
    with st.container(border=True):
        st.subheader("🎭 Gestionnaire de Scénarios de Crise")
        col_sc1, col_sc2 = st.columns([1, 2])
        
        with col_sc1:
            type_ev = st.radio("Sélectionnez un événement :", 
                               ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"], 
                               index=0)
        
        with col_sc2:
            if type_ev == "🔴 Aléa Production":
                pct = st.slider("Baisse de capacité usine (%)", 10, 90, 30)
                df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
                contexte_simulation = f"CRISE : Capacité réduite de {pct}%."
                st.warning(contexte_simulation)
            elif type_ev == "🔵 Pic Demande":
                pct = st.slider("Hausse de la demande marché (%)", 10, 150, 50)
                df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
                contexte_simulation = f"OPPORTUNITÉ/PIC : Hausse de demande de {pct}%."
                st.info(contexte_simulation)
            elif type_ev == "🟣 Personnalisé":
                txt = st.text_area("Décrivez l'événement :", "Ex: Grève des dockers...")
                contexte_simulation = f"ÉVÉNEMENT SPÉCIFIQUE : {txt}"

    # --- SECTION 2 : DASHBOARD FILTRÉ ---
    st.markdown("---")
    st.subheader(f"📊 Diagnostic : {selected_prod}")

    # Filtrage pour la vue visuelle
    v_mkt = df_mkt_sim if selected_prod == "Tous les produits" else df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
    v_prod = df_prod_sim if selected_prod == "Tous les produits" else df_prod_sim[df_prod_sim['Produit'] == selected_prod]
    v_fin = df_fin if selected_prod == "Tous les produits" else df_fin[df_fin['Produit'] == selected_prod]

    demand_sim = v_mkt['Forecast'].sum()
    capa_sim = v_prod['Capacity'].sum()
    sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Demande", f"{demand_sim:,.0f} u")
    k2.metric("Capacité", f"{capa_sim:,.0f} u")
    k3.metric("Saturation", f"{sat_sim:.1f}%")
    k4.metric("CA Potentiel", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_bal = go.Figure()
        fig_bal.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
        fig_bal.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
        fig_bal.update_layout(title="Équilibre Offre/Demande", barmode='overlay', height=400)
        st.plotly_chart(fig_bal, use_container_width=True)

    with col_g2:
        df_profit = pd.merge(v_mkt, v_fin, on='Produit')
        df_profit['Marge_Totale'] = df_profit['Forecast'] * df_profit['Margin_Unit']
        fig_tree = px.treemap(df_profit, path=['Produit'], values='Marge_Totale', color='Margin_Unit',
                              color_continuous_scale='RdYlGn', title="Répartition de la Marge")
        st.plotly_chart(fig_tree, use_container_width=True)

    # --- SECTION 3 : ORCHESTRATION IA (Pleine Largeur + 6 Agents) ---
    st.markdown("---")
    st.subheader("🤖 Intelligence Agentique : Analyse Multi-Agents")

    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        st.info("🧠 Les 6 agents travaillent sur toute la page...")
        log_placeholder = st.empty()
        redir = StreamlitRedirect(log_placeholder)
        old_stdout = sys.stdout
        sys.stdout = redir
        
        try:
            # Optimisation data (Head 15) pour éviter RateLimit
            txt_mkt = df_mkt_sim.sort_values(by='Forecast', ascending=False).head(15)[['Produit', 'Forecast']].to_string()
            txt_prod = df_prod_sim.sort_values(by='Capacity', ascending=True).head(15)[['Produit', 'Capacity']].to_string()
            txt_fin = df_fin.head(15)[['Produit', 'Margin_Unit']].to_string()

            # DÉFINITION DES 6 TÂCHES
            t1 = Task(description=f"Marketing: Analyse demande {txt_mkt}.", agent=SOP.marketing, expected_output="Rapport demande.")
            t2 = Task(description="Ventes: Valide les volumes finaux terrain.", agent=SOP.sales, expected_output="Rapport ventes.")
            t3 = Task(description=f"Supply: Vérifie prod {txt_prod}.", agent=SOP.supply, expected_output="Rapport industriel.")
            t4 = Task(description=f"Achats: Analyse risques composants {txt_fin}.", agent=SOP.purchasing, expected_output="Rapport achats.")
            t5 = Task(description=f"Finance: Bilan rentabilité sur {txt_fin}.", agent=SOP.finance, expected_output="Bilan financier.")
            t6 = Task(description=f"Directeur: Arbitre PIC final pour {contexte_simulation}.", agent=SOP.orchestrator, expected_output="Plan S&OP Final.")

            crew = Crew(
                agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                tasks=[t1, t2, t3, t4, t5, t6]
            )
            crew.kickoff()

            # SAUVEGARDE DES 6 RAPPORTS
            st.session_state['outputs'] = {
                "📢 Marketing": t1.output.raw,
                "🤝 Ventes": t2.output.raw,
                "🏗️ Supply Chain": t3.output.raw,
                "📦 Achats / Risques": t4.output.raw,
                "💰 Finance": t5.output.raw,
                "🏆 Rapport PIC Final": t6.output.raw
            }
            st.session_state['run_done'] = True
        finally:
            sys.stdout = old_stdout

    # --- CONSULTATION DES RAPPORTS ---
    if st.session_state.get('run_done'):
        st.markdown("---")
        st.subheader("📋 Consultation des rapports détaillés")
        choix = st.multiselect(
            "Quels rapports voulez-vous afficher ?", 
            options=list(st.session_state['outputs'].keys()), 
            default=["🏆 Rapport PIC Final"]
        )
        
        for r in choix:
            with st.expander(f"Voir {r}", expanded=True):
                st.markdown(st.session_state['outputs'][r])

else:
    st.info("👋 Veuillez charger le fichier Excel pour commencer.")
