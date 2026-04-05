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
    def __init__(self, placeholder): # Correction __init__
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
     st.write("Onglet Demande: Produit, Marketing_Forecast, Sales_Orders")
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



        # =================================================================
        # 2. SYSTÈME DE FILTRE PAR PRODUIT (Visualisation)
        # =================================================================
        st.subheader("🔍 Analyse par Produit")
        liste_produits = ["Tous les produits"] + list(df_mkt['Produit'].unique())
        selected_prod = st.selectbox("Sélectionnez un produit pour filtrer la vue :", liste_produits)

        # Filtrage des données pour l'affichage
        if selected_prod == "Tous les produits":
            view_mkt, view_prod, view_fin = df_mkt, df_prod, df_fin
        else:
            view_mkt = df_mkt[df_mkt['Produit'] == selected_prod]
            view_prod = df_prod[df_prod['Produit'] == selected_prod]
            view_fin = df_fin[df_fin['Produit'] == selected_prod]

        # 3. KPIs DYNAMIQUES
        k1, k2, k3, k4 = st.columns(4)
        total_demand = view_mkt['Forecast'].sum()
        total_capacity = view_prod['Capacity'].sum()
        saturation = (total_demand / total_capacity * 100) if total_capacity > 0 else 0
        marge_moyenne = view_fin['Margin_Unit'].mean()

        k1.metric("Demande", f"{total_demand:,.0f} u")
        k2.metric("Capacité", f"{total_capacity:,.0f} u")
        k3.metric("Saturation", f"{saturation:.1f}%", delta=f"{saturation-100:.1f}%", delta_color="inverse")
        k4.metric("Marge Moy.", f"{marge_moyenne:.2f} €")

        # 4. GRAPHIQUES FILTRÉS
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_bal = go.Figure()
            fig_bal.add_trace(go.Bar(x=view_mkt['Produit'], y=view_mkt['Forecast'], name='Demande', marker_color='#3498db'))
            fig_bal.add_trace(go.Bar(x=view_prod['Produit'], y=view_prod['Capacity'], name='Capacité', marker_color='#e67e22'))
            fig_bal.update_layout(title="Équilibre Offre/Demande", barmode='group', height=300)
            st.plotly_chart(fig_bal, use_container_width=True)

        with col_g2:
            fig_margin = px.bar(view_fin, x='Produit', y='Margin_Unit', color='Margin_Unit', 
                                title="Marge par Produit (€)", color_continuous_scale='Greens')
            fig_margin.update_layout(height=300)
            st.plotly_chart(fig_margin, use_container_width=True)

        # 5. SCÉNARIOS (WHAT-IF)
        st.markdown("---")
        st.subheader("🎭 Simulateur de Crise")
        type_evenement = st.radio("Simulation :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"])
        
        contexte_simulation = "SITUATION NORMALE."
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()

        if type_evenement == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30)
            df_prod_sim['Capacity'] = df_prod_sim['Capacity'] * (1 - pct/100)
            contexte_simulation = f"CRISE : Capacité réduite de {pct}%."
        elif type_evenement == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 100, 40)
            df_mkt_sim['Forecast'] = df_mkt_sim['Forecast'] * (1 + pct/100)
            contexte_simulation = f"PIC : Hausse de {pct}%."
        elif type_evenement == "🟣 Personnalisé":
            txt = st.text_area("Description de l'événement :", "Ex: Grève logistique de 2 semaines...")
            contexte_simulation = f"ÉVÉNEMENT : {txt}"

        # 6. LANCEMENT IA
        st.markdown("---")
        if st.button("🚀 Lancer l'Analyse Agentique S&OP", use_container_width=True):
            col_log, col_rep = st.columns([1, 1])
            with col_log:
                st.info("🤖 Logique des agents...")
                log_placeholder = st.empty()
                redir = StreamlitRedirect(log_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir
                try:
                    # Optimisation Rate Limit (Head 15)
                    txt_mkt = df_mkt_sim[['Produit', 'Forecast']].head(15).to_string()
                    txt_prod = df_prod_sim[['Produit', 'Capacity']].head(15).to_string()
                    txt_fin = view_fin[['Produit', 'Margin_Unit']].head(15).to_string()

                    t1 = Task(description=f"Analyse: {txt_mkt}. Contexte: {contexte_simulation}", agent=SOP.marketing, expected_output="Rapport demande.")
                    t2 = Task(description="Valide les volumes.", agent=SOP.sales, expected_output="Volumes validés.")
                    t3 = Task(description=f"Vérifie prod: {txt_prod}.", agent=SOP.supply, expected_output="Faisabilité.")
                    t4 = Task(description=f"Analyse finance: {txt_fin}.", agent=SOP.finance, expected_output="Bilan financier.")
                    t5 = Task(description="Rapport S&OP Final. Arbitre selon la marge.", agent=SOP.orchestrator, expected_output="Plan S&OP Complet.")

                    crew = Crew(agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.finance, SOP.orchestrator], tasks=[t1, t2, t3, t4, t5])
                    resultat = crew.kickoff()
                    st.session_state['res_sop'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

            with col_rep:
                st.subheader("📋 Rapport de Décision")
                if 'res_sop' in st.session_state:
                    st.success("✅ Plan S&OP généré")
                    st.markdown(st.session_state['res_sop'])
                    st.download_button("📥 Télécharger", st.session_state['res_sop'], "Rapport_SOP.md")

    except Exception as e:
        st.error(f"⚠️ Erreur de traitement : {e}")
else:
    st.info("👋 Veuillez charger le fichier Excel pour commencer.")
