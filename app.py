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

st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("---")

if uploaded_file is not None:
    try:
        # 1. LECTURE DES DONNÉES
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
        df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
        df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

        # 2. SCÉNARIOS (WHAT-IF) - Placé avant pour impacter les graphes
        with st.container(border=True):
            st.subheader("🎭 Gestionnaire de Scénarios")
            col_sc1, col_sc2 = st.columns([1, 2])
            with col_sc1:
                type_ev = st.radio("Simulation :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"])
            
            df_mkt_sim = df_mkt.copy()
            df_prod_sim = df_prod.copy()
            contexte_sim = "SITUATION NORMALE"

            with col_sc2:
                if type_ev == "🔴 Aléa Production":
                    pct = st.slider("Baisse capacité (%)", 10, 90, 30)
                    df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
                    contexte_sim = f"CRISE : Capacité -{pct}%"
                elif type_ev == "🔵 Pic Demande":
                    pct = st.slider("Hausse demande (%)", 10, 150, 50)
                    df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
                    contexte_sim = f"PIC : Demande +{pct}%"
                elif type_ev == "🟣 Personnalisé":
                    txt = st.text_area("Description :", "Ex: Grève logistique...")
                    contexte_sim = f"ÉVÉNEMENT : {txt}"

        # 3. DASHBOARD ET KPIs
        st.markdown("---")
        st.subheader("📊 Diagnostic de la Situation")
        
        demand_sim = df_mkt_sim['Forecast'].sum()
        capa_sim = df_prod_sim['Capacity'].sum()
        sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0
        profit_pot = (df_mkt_sim['Forecast'] * df_fin['Margin_Unit']).sum()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Demande Totale", f"{demand_sim:,.0f} u")
        k2.metric("Capacité Totale", f"{capa_sim:,.0f} u")
        k3.metric("Saturation", f"{sat_sim:.1f}%", f"{sat_sim-100:.1f}%", delta_color="inverse")
        k4.metric("Profit Potentiel", f"{profit_pot:,.0f} €")

        # 4. GRAPHIQUES AVANCÉS
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            # Graphe Overlay (Offre vs Demande)
            fig_bal = go.Figure()
            fig_bal.add_trace(go.Bar(x=df_prod_sim['Produit'], y=df_prod_sim['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
            fig_bal.add_trace(go.Bar(x=df_mkt_sim['Produit'], y=df_mkt_sim['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
            fig_bal.update_layout(title="Équilibre Offre/Demande (Overlay)", barmode='overlay', height=350)
            st.plotly_chart(fig_bal, use_container_width=True)

        with col_g2:
            # Treemap de Profit
            df_profit = pd.merge(df_mkt_sim, df_fin, on='Produit')
            df_profit['Profit_Total'] = df_profit['Forecast'] * df_profit['Margin_Unit']
            fig_tree = px.treemap(df_profit, path=['Produit'], values='Profit_Total', color='Margin_Unit',
                                  color_continuous_scale='RdYlGn', title="Poids Économique par Produit")
            st.plotly_chart(fig_tree, use_container_width=True)

        # Rankings
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            top_d = df_mkt_sim.sort_values(by='Forecast', ascending=False).head(10)
            st.plotly_chart(px.bar(top_d, x='Forecast', y='Produit', orientation='h', title="Top 10 Demande", color_discrete_sequence=['#3498db']), use_container_width=True)
        with col_r2:
            df_sat = pd.merge(df_mkt_sim, df_prod_sim, on='Produit')
            df_sat['Sat_%'] = (df_sat['Forecast'] / df_sat['Capacity'] * 100)
            top_s = df_sat.sort_values(by='Sat_%', ascending=False).head(10)
            st.plotly_chart(px.bar(top_s, x='Sat_%', y='Produit', orientation='h', title="Top 10 Goulots (%)", color='Sat_%', color_continuous_scale='Reds'), use_container_width=True)

        # 5. Lancement IA
        st.markdown("---")
        if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
            col_log, col_rep = st.columns([1, 1])
            with col_log:
                st.info("🤖 Logique des agents...")
                log_placeholder = st.empty()
                sys.stdout = StreamlitRedirect(log_placeholder)
                  try:
                    # On ne garde que les 10 produits les plus importants pour l'analyse
                    # Cela réduit la consommation de tokens de 80%
                    txt_mkt = df_mkt_sim.sort_values(by='Forecast', ascending=False).head(10)[['Produit', 'Forecast']].to_string()
                    txt_prod = df_prod_sim.sort_values(by='Capacity', ascending=True).head(10)[['Produit', 'Capacity']].to_string()
                    txt_fin = df_fin.sort_values(by='Margin_Unit', ascending=False).head(10)[['Produit', 'Margin_Unit']].to_string()


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

        # 6. FILTRE DE VUE DES RÉPONSES (VOTRE BOUTON)
        if st.session_state.get('run_done'):
            st.markdown("---")
            st.subheader("📋 Consultation des rapports")
            choix = st.multiselect("Quels rapports voulez-vous afficher ?", 
                                   options=list(st.session_state['outputs'].keys()), 
                                   default=["🏆 Rapport Final"])
            
            for r in choix:
                with st.expander(f"Voir {r}", expanded=True):
                    st.markdown(st.session_state['outputs'][r])

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
else:
    st.info("👋 Veuillez charger le fichier Excel.")
