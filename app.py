import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")

# 2. CAPTURE DES LOGS AGENTS
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# 3. BARRE LATÉRALE
st.sidebar.title("🛠️ Configuration")
with st.sidebar.expander("📖 Format Excel Requis", expanded=False):
    st.write("Onglets requis :")
    st.write("- **Demande**: Produit, Forecast, Sales_Orders")
    st.write("- **Production**: Produit, Capacity, Stock_Level")
    st.write("- **Finance_Achats**: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")

uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

# 4. CONTENU PRINCIPAL
st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("---")

if uploaded_file is not None:
    try:
        # --- LECTURE DES DONNÉES ---
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
        df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
        df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

        # --- FILTRE PAR PRODUIT (POUR LA VUE DASHBOARD) ---
        liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
        selected_prod = st.selectbox("🔍 Analyser un produit spécifique (Vue Dashboard) :", liste_produits)

        if selected_prod == "Tous les produits":
            view_mkt, view_prod, view_fin = df_mkt, df_prod, df_fin
        else:
            view_mkt = df_mkt[df_mkt['Produit'] == selected_prod]
            view_prod = df_prod[df_prod['Produit'] == selected_prod]
            view_fin = df_fin[df_fin['Produit'] == selected_prod]

        # --- AFFICHAGE DES KPIs ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        demande_val = view_mkt['Forecast'].sum()
        capa_val = view_prod['Capacity'].sum()
        sat_val = (demande_val / capa_val * 100) if capa_val > 0 else 0
        marge_moyenne = view_fin['Margin_Unit'].mean()

        kpi1.metric("Demande", f"{demande_val:,.0f} u")
        kpi2.metric("Capacité", f"{capa_val:,.0f} u")
        kpi3.metric("Saturation", f"{sat_val:.1f}%", delta=f"{sat_val-100:.1f}%", delta_color="inverse")
        kpi4.metric("Marge Moy.", f"{marge_moyenne:.2f} €")

        # --- GRAPHIQUES ---
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_bal = go.Figure()
            fig_bal.add_trace(go.Bar(x=view_mkt['Produit'], y=view_mkt['Forecast'], name='Demande', marker_color='#3498db'))
            fig_bal.add_trace(go.Bar(x=view_prod['Produit'], y=view_prod['Capacity'], name='Capacité', marker_color='#e67e22'))
            fig_bal.update_layout(title="Équilibre Offre/Demande", barmode='group', height=300)
            st.plotly_chart(fig_bal, use_container_width=True)

        with col_g2:
            fig_risk = px.scatter(view_fin, x='Supplier_LeadTime', y='Margin_Unit', size='Material_Cost', 
                                  color='Produit', title="Risque Délais vs Rentabilité")
            st.plotly_chart(fig_risk, use_container_width=True)

        # --- SIMULATEUR DE SCÉNARIOS (WHAT-IF) ---
        st.markdown("---")
        st.subheader("🎭 Simulateur de Crise et d'Opportunité")
        
        col_sc1, col_sc2 = st.columns([1, 1])
        with col_sc1:
            type_evenement = st.radio(
                "Sélectionnez l'événement à simuler :", 
                ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic de Demande", "🟠 Inflation Coûts", "🟣 Événement Personnalisé"]
            )

        # Initialisation des copies pour la simulation IA
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()
        df_fin_sim = df_fin.copy()
        contexte_simulation = "SITUATION NORMALE."

        with col_sc2:
            if type_evenement == "🔴 Aléa Production":
                pct = st.slider("Baisse de capacité (%)", 10, 90, 30)
                df_prod_sim['Capacity'] = df_prod_sim['Capacity'] * (1 - pct/100)
                contexte_simulation = f"CRISE : Baisse de {pct}% de la capacité de production."
            elif type_evenement == "🔵 Pic de Demande":
                pct = st.slider("Hausse de demande (%)", 10, 100, 40)
                df_mkt_sim['Forecast'] = df_mkt_sim['Forecast'] * (1 + pct/100)
                contexte_simulation = f"OPPORTUNITÉ : Hausse de {pct}% de la demande marché."
            elif type_evenement == "🟠 Inflation Coûts":
                pct = st.slider("Hausse des coûts (%)", 10, 100, 20)
                df_fin_sim['Margin_Unit'] = df_fin_sim['Margin_Unit'] * (1 - pct/100)
                contexte_simulation = f"ALERTE : Inflation réduisant les marges de {pct}%."
            elif type_evenement == "🟣 Événement Personnalisé":
                txt_libre = st.text_area("Décrivez la situation :", "Ex: Grève des dockers, retard fournisseur de 3 semaines...")
                contexte_simulation = f"ÉVÉNEMENT SPÉCIFIQUE : {txt_libre}."

        # --- 5. ORCHESTRATION AGENTIQUE ---
        st.markdown("---")
        st.subheader("⚙️ Lancement de l'Intelligence Artificielle")
        
        if st.button("🚀 Analyser et Générer le Plan S&OP", use_container_width=True):
            col_log, col_rep = st.columns([1, 1])
            
            with col_log:
                st.info("🤖 **Logique des agents en temps réel :**")
                log_placeholder = st.empty()
                redir = StreamlitRedirect(log_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir

                try:
                    # OPTIMISATION DES DONNÉES (Pour éviter Rate Limit)
                    txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(15).to_string()
                    txt_prod = df_prod_sim[['Produit', 'Capacity']].head(15).to_string()
                    txt_fin = df_fin_sim[['Produit', 'Margin_Unit', 'Supplier_LeadTime']].head(15).to_string()

                    # DÉFINITION DES TÂCHES
                    t1 = Task(description=f"CONTEXTE: {contexte_simulation}. Analyse demande: {txt_mkt}.", agent=SOP.marketing, expected_output="Analyse demande.")
                    t2 = Task(description=f"Valide les volumes de ventes finaux.", agent=SOP.sales, expected_output="Volumes validés.")
                    t3 = Task(description=f"Vérifie la prod: {txt_prod}.", agent=SOP.supply, expected_output="Rapport industriel.")
                    t4 = Task(description=f"Analyse risques délais: {txt_fin}.", agent=SOP.purchasing, expected_output="Rapport achats.")
                    t5 = Task(description="Calcule la marge totale finale.", agent=SOP.finance, expected_output="Bilan financier.")
                    t6 = Task(description=f"Rédige le Plan S&OP Final face à : {contexte_simulation}. Arbitre selon la marge.", agent=SOP.orchestrator, expected_output="Rapport S&OP complet.")

                    crew = Crew(
                        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                        tasks=[t1, t2, t3, t4, t5, t6],
                        process=Process.sequential
                    )

                    resultat = crew.kickoff()
                    st.session_state['resultat_sop'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

            with col_rep:
                st.subheader("📋 Rapport de Décision S&OP")
                if 'resultat_sop' in st.session_state:
                    st.success("✅ Plan S&OP généré !")
                    st.markdown(st.session_state['resultat_sop'])
                    st.download_button("📥 Télécharger", st.session_state['resultat_sop'], "Rapport_SOP.md")

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")

else:
    st.info("👋 Bienvenue ! Importez le fichier Excel dans le menu de gauche pour démarrer.")
