import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Task
import SOP
import sys
import re

# --- CLASSE POUR CAPTURER LA DISCUSSION DES AGENTS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        # Nettoyage des codes couleurs ANSI pour l'affichage Streamlit
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="S&OP AI Strategic Copilot", layout="wide", page_icon="🏭")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# --- BARRE LATÉRALE ---
st.sidebar.title("⚙️ Configuration Système")
uploaded_file = st.sidebar.file_uploader("📥 Charger les données S&OP (Excel)", type=['xlsx'])

if uploaded_file is None:
    st.info("👋 Bienvenue ! Veuillez charger votre fichier Excel S&OP dans la barre latérale pour activer le simulateur.")
    st.stop()

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

# --- INITIALISATION DES VARIABLES DE SIMULATION ---
df_mkt_sim = df_mkt.copy()
df_prod_sim = df_prod.copy()
contexte_simulation = "SITUATION NORMALE"

# --- SECTION 1 : SIMULATEUR DE SCÉNARIOS ---
st.title("🏭 S&OP Agentic AI Simulator")
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
            txt = st.text_area("Décrivez l'événement :", "Ex: Retard livraison fournisseur de 4 semaines...")
            contexte_simulation = f"ÉVÉNEMENT SPÉCIFIQUE : {txt}"

# --- SECTION 2 : DASHBOARD ANALYTIQUE ---
st.markdown("---")
st.subheader("📊 Diagnostic de la Situation")

# KPIs de haut niveau
demand_initial = df_mkt['Forecast'].sum()
demand_sim = df_mkt_sim['Forecast'].sum()
capa_sim = df_prod_sim['Capacity'].sum()
sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Demande Totale", f"{demand_sim:,.0f} u", f"{demand_sim - demand_initial:,.0f} u", delta_color="inverse")
k2.metric("Capacité Totale", f"{capa_sim:,.0f} u", f"{capa_sim - df_prod['Capacity'].sum():,.0f} u")
k3.metric("Taux Saturation", f"{sat_sim:.1f}%", f"{sat_sim - 100:.1f}%", delta_color="inverse")
k4.metric("CA Potentiel", f"{(df_mkt_sim['Forecast'] * df_fin['Margin_Unit']).sum():,.0f} €")

# Visualisations Avancées
col_g1, col_g2 = st.columns(2)

with col_g1:
    # Graphique Capacité vs Demande (Overlay)
    fig_bal = go.Figure()
    fig_bal.add_trace(go.Bar(x=df_prod_sim['Produit'], y=df_prod_sim['Capacity'], name='Capacité Usine', marker_color='#2ecc71', opacity=0.6))
    fig_bal.add_trace(go.Bar(x=df_mkt_sim['Produit'], y=df_mkt_sim['Forecast'], name='Demande Client', marker_color='#e74c3c', width=0.4))
    fig_bal.update_layout(title="<b>Équilibre Offre/Demande par Produit</b>", barmode='overlay', height=400)
    st.plotly_chart(fig_bal, use_container_width=True)

with col_g2:
    # Treemap de la Marge
    df_profit = pd.merge(df_mkt_sim, df_fin, on='Produit')
    df_profit['Marge_Totale'] = df_profit['Forecast'] * df_profit['Margin_Unit']
    fig_tree = px.treemap(df_profit, path=['Produit'], values='Marge_Totale', color='Margin_Unit',
                          color_continuous_scale='RdYlGn', title="<b>Répartition de la Marge (Poids Économique)</b>")
    fig_tree.update_layout(height=400)
    st.plotly_chart(fig_tree, use_container_width=True)

# Ligne de classement
col_rank1, col_rank2 = st.columns(2)
with col_rank1:
    top_demand = df_mkt_sim.sort_values(by='Forecast', ascending=False).head(10)
    fig_top = px.bar(top_demand, x='Forecast', y='Produit', orientation='h', title="<b>Top 10 Produits les plus demandés</b>", color_discrete_sequence=['#3498db'])
    st.plotly_chart(fig_top, use_container_width=True)

with col_rank2:
    df_sat = pd.merge(df_mkt_sim, df_prod_sim, on='Produit')
    df_sat['Sat_%'] = (df_sat['Forecast'] / df_sat['Capacity'] * 100)
    df_sat = df_sat.sort_values(by='Sat_%', ascending=False).head(10)
    fig_sat = px.bar(df_sat, x='Sat_%', y='Produit', orientation='h', title="<b>Top 10 Goulots d'Étranglement (%)</b>", color='Sat_%', color_continuous_scale='Reds')
    fig_sat.add_vline(x=100, line_dash="dash", line_color="red")
    st.plotly_chart(fig_sat, use_container_width=True)

# --- SECTION 3 : ORCHESTRATION AGENTIQUE ---
st.markdown("---")
st.subheader("🤖 Intelligence Agentique : Résolution & Arbitrage")

if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
    col_log, col_rep = st.columns([1, 1])
    
    with col_log:
        st.info("🧠 **Pensée des Agents en temps réel :**")
        log_placeholder = st.empty()
        redir = StreamlitRedirect(log_placeholder)
        old_stdout = sys.stdout
        sys.stdout = redir
        
        try:
            # Préparation des données texte pour les agents
            txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(20).to_string()
            txt_prod = df_prod_sim[['Produit', 'Capacity']].head(20).to_string()
            txt_fin = df_fin[['Produit', 'Margin_Unit', 'Material_Cost']].head(20).to_string()

            # Définition des tâches
            t1 = Task(description=f"Analyser la demande client : {txt_mkt}. Contexte : {contexte_simulation}", 
                      agent=SOP.marketing, expected_output="Rapport de demande priorisée.")
            
            t2 = Task(description=f"Vérifier la faisabilité industrielle : {txt_prod}. Identifier les ruptures.", 
                      agent=SOP.supply, expected_output="Plan de production contraint.")
            
            t3 = Task(description=f"Calculer l'impact financier et la profitabilité : {txt_fin}", 
                      agent=SOP.finance, expected_output="Analyse de rentabilité du scénario.")
            
            t4 = Task(description="""Rédiger le Plan S&OP Final. 
                      Arbitrer les conflits entre Marketing et Production en privilégiant la marge brute. 
                      Donner des recommandations claires sur quel produit réduire.""", 
                      agent=SOP.orchestrator, expected_output="Rapport Stratégique S&OP Complet.")

            # Création du Crew
            crew = Crew(
                agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator],
                tasks=[t1, t2, t3, t4],
                process="sequential"
            )
            
            resultat = crew.kickoff()
            st.session_state['res_sop'] = str(resultat)
            
        except Exception as e:
            st.error(f"Erreur IA : {e}")
        finally:
            sys.stdout = old_stdout

    with col_rep:
        st.success("✅ Analyse Terminée")
        if 'res_sop' in st.session_state:
            st.markdown(st.session_state['res_sop'])
            st.download_button("📥 Exporter le Rapport S&OP", st.session_state['res_sop'], file_name="Rapport_SOP_IA.md")
