import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

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

    # --- SCÉNARIOS WHAT-IF ---
    st.markdown("---")
    st.subheader("🎭 Simulateur de Crise")
    col_sc1, col_sc2 = st.columns([1, 1])
    
    with col_sc1:
        type_event = st.radio("Événement :", ["Normal", "🔴 Rupture Machine (-40% Capacité)", "🔵 Pic Promo (+50% Demande)"])
    
    # On applique les modifications sur les données réelles AVANT de les donner aux agents
    df_mkt_sim = df_mkt.copy(); df_prod_sim = df_prod.copy()
    contexte = "Situation normale."

    if "Rupture Machine" in type_event:
        df_prod_sim['Capacity'] = df_prod_sim['Capacity'] * 0.6
        contexte = "ALERTE : Une machine est en panne sur les lignes principales !"
    elif "Pic Promo" in type_event:
        df_mkt_sim['Forecast'] = df_mkt_sim['Forecast'] * 1.5
        contexte = "MARKETING : Une campagne virale booste la demande de 50% !"

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
