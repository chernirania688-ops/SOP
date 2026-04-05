import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re
st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")
--- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Configuration")
with st.sidebar.expander("📖 Format Excel Requis", expanded=False):
st.write("Onglet Demande: Produit, Marketing_Forecast, Sales_Orders")
st.write("Onglet Production: Produit, Capacity, Stock_Level")
st.write("Onglet Finance_Achats: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])
st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("---")
if uploaded_file is not None:
try:
# 1. LECTURE ET NETTOYAGE DES DONNÉES
xls = pd.ExcelFile(uploaded_file)
onglets_requis = ['Demande', 'Production', 'Finance_Achats']

# --- CAPTURE DES LOGS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

st.set_page_config(page_title="S&OP AI Dashboard", layout="wide", page_icon="🏭")

# --- CHARGEMENT DONNÉES ---
st.sidebar.title("📁 Configuration")
uploaded_file = st.sidebar.file_uploader("Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
    df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
    df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

    # =================================================================
    # NOUVEAU : SÉLECTEUR DE PRODUIT POUR FILTRER LA VUE
    # =================================================================
    st.title("🏭 Pilotage Stratégique S&OP")
    
    liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
    selected_prod = st.selectbox("🔍 Analyser un produit spécifique :", liste_produits)

    # Filtrage des données selon le choix
    if selected_prod == "Tous les produits":
        view_mkt = df_mkt; view_prod = df_prod; view_fin = df_fin
    else:
        view_mkt = df_mkt[df_mkt['Produit'] == selected_prod]
        view_prod = df_prod[df_prod['Produit'] == selected_prod]
        view_fin = df_fin[df_fin['Produit'] == selected_prod]

    # --- KPIs DYNAMIQUES ---
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    demande_val = view_mkt['Forecast'].sum()
    capa_val = view_prod['Capacity'].sum()
    sat_val = (demande_val / capa_val * 100) if capa_val > 0 else 0
    marge_moyenne = view_fin['Margin_Unit'].mean()

    kpi1.metric("Demande", f"{demande_val:,.0f} u")
    kpi2.metric("Capacité", f"{capa_val:,.0f} u")
    kpi3.metric("Saturation", f"{sat_val:.1f}%", delta=f"{sat_val-100:.1f}%", delta_color="inverse")
    kpi4.metric("Marge Unitaire Moy.", f"{marge_moyenne:.2f} €")

    # --- GRAPHIQUES FILTRÉS ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_bal = go.Figure()
        fig_bal.add_trace(go.Bar(x=view_mkt['Produit'], y=view_mkt['Forecast'], name='Demande', marker_color='#3498db'))
        fig_bal.add_trace(go.Bar(x=view_prod['Produit'], y=view_prod['Capacity'], name='Capacité', marker_color='#e67e22'))
        fig_bal.update_layout(title=f"Équilibre Offre/Demande : {selected_prod}", barmode='group', height=300)
        st.plotly_chart(fig_bal, use_container_width=True)

    with col_g2:
        fig_risk = px.scatter(view_fin, x='Supplier_LeadTime', y='Margin_Unit', size='Material_Cost', 
                              color='Produit', title="Analyse Risque Délais vs Rentabilité",
                              labels={'Supplier_LeadTime': 'Délai Fournisseur (jours)'})
        fig_risk.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Seuil critique")
        fig_risk.update_layout(height=300)
        st.plotly_chart(fig_risk, use_container_width=True)

   
   # 4. SIMULATEUR DE SCÉNARIOS "WHAT-IF"
    st.subheader("🎭 Simulateur de Crise et d'Opportunité")
    
    col_sc1, col_sc2 = st.columns([1, 1])
    with col_sc1:
        type_evenement = st.radio("Sélectionnez l'événement à simuler :",["🟢 Nominal (Aucun problème)", "🔴 Aléa de Production", "🔵 Pic de Demande", "🟠 Inflation des Coûts", "🟣 Événement Personnalisé"]
        )

    with col_sc2:
        contexte_simulation = "SITUATION NORMALE : Aucun problème particulier."
        
        if type_evenement == "🔴 Aléa de Production":
            pct_baisse = st.slider("Baisse de capacité usine (%)", 10, 100, 30)
            contexte_simulation = f"CRISE PRODUCTION : La capacité totale de l'usine est réduite de {pct_baisse}%. L'agent Supply doit impérativement alerter sur les manques et l'Orchestrateur doit sacrifier des produits."
            st.warning(f"⚠️ Simulation : Perte de {pct_baisse}% de capacité.")
        
        elif type_evenement == "🔵 Pic de Demande":
            pct_hausse = st.slider("Hausse soudaine de la demande (%)", 10, 200, 50)
            contexte_simulation = f"PIC DEMANDE : La demande augmente de {pct_hausse}%. L'agent Marketing doit l'intégrer et la Supply Chain doit dire si c'est fabricable."
            st.info(f"📈 Simulation : Hausse des ventes de {pct_hausse}%.")
            
        elif type_evenement == "🟠 Inflation des Coûts":
            pct_infl = st.slider("Hausse des coûts matières (%)", 10, 100, 20)
            contexte_simulation = f"INFLATION : Les coûts d'achat (Material_Cost) augmentent de {pct_infl}%. La Finance doit recalculer la marge à la baisse."
            st.error(f"💰 Simulation : Inflation de {pct_infl}%.")
            
        elif type_evenement == "🟣 Événement Personnalisé":
            txt_libre = st.text_area("Décrivez la situation :", "Ex: Grève des dockers, retard fournisseur de 3 semaines...")
            contexte_simulation = f"ÉVÉNEMENT SPÉCIFIQUE : {txt_libre}. Les agents doivent s'adapter à cette situation exacte."

    # --- BOUTON DE LANCEMENT IA ---
    if st.button("🚀 Lancer l'Analyse Agentique (Plan S&OP)", use_container_width=True):
        col_log, col_res = st.columns([1, 1])
        
        with col_log:
            st.info("🤖 **Réflexion des agents...**")
            log_placeholder = st.empty()
            sys.stdout = StreamlitRedirect(log_placeholder)

            # Les tâches reçoivent la donnée complète pour décider de l'arbitrage
            t1 = Task(description=f"Analyse : {df_mkt_sim.to_string()}. Scenario : {contexte}", agent=SOP.marketing, expected_output="Rapport demande.")
            t2 = Task(description=f"Vérifie la prod : {df_prod_sim.to_string()}.", agent=SOP.supply, expected_output="Rapport industriel.")
            t3 = Task(description="Calcule la marge totale finale.", agent=SOP.finance, expected_output="Bilan financier.")
            t4 = Task(description="Rédige le Plan Industriel et Commercial (PIC) final. Arbitre en faveur des produits à forte marge.", 
                      agent=SOP.orchestrator, expected_output="Rapport S&OP complet.")

            crew = Crew(agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator], tasks=[t1, t2, t3, t4])
            result = crew.kickoff()
            sys.stdout = sys.__stdout__

        with col_res:
            st.success("✅ Arbitrage Terminé")
            st.markdown(result)
            st.download_button("📥 Télécharger le Plan", str(result), "Plan_SOP.md")

else:
    st.info("👋 Veuillez charger le fichier Excel pour activer le dashboard.")
