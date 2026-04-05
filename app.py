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
       # --- CALCULS AVANT/APRÈS ---
        demand_initial = df_mkt['Forecast'].sum()
        demand_sim = df_mkt_sim['Forecast'].sum()
        capa_initial = df_prod['Capacity'].sum()
        capa_sim = df_prod_sim['Capacity'].sum()
        
        # --- AFFICHAGE DES KPIs AMÉLIORÉS ---
        st.subheader("📊 Indicateurs de Performance (Impact Scénario)")
        k1, k2, k3, k4 = st.columns(4)
        
        # KPI Demande avec delta
        k1.metric(
            label="Demande Totale", 
            value=f"{demand_sim:,.0f} u", 
            delta=f"{demand_sim - demand_initial:,.0f} u",
            delta_color="inverse" if demand_sim > demand_initial else "normal"
        )
        
        # KPI Capacité avec delta
        k2.metric(
            label="Capacité Usine", 
            value=f"{capa_sim:,.0f} u", 
            delta=f"{capa_sim - capa_initial:,.0f} u",
            delta_color="normal"
        )
        
        # KPI Saturation avec jauge de couleur
        sat_sim = (demand_sim / capa_sim * 100) if capa_sim > 0 else 0
        k3.metric(
            label="Taux de Saturation", 
            value=f"{sat_sim:.1f}%", 
            delta=f"{sat_sim - 100:.1f}% au-dessus" if sat_sim > 100 else "Sous contrôle",
            delta_color="inverse"
        )
        
        # Valeur du stock ou Marge Risquée
        marge_totale = (view_fin['Margin_Unit'] * view_mkt['Forecast']).sum()
        k4.metric(label="Chiffre d'Affaires Potentiel", value=f"{marge_totale:,.0f} €")
        with col_g1:
            # Création d'un graphique comparatif empilé
            fig_bal = go.Figure()
            
            # Barre Capacité
            fig_bal.add_trace(go.Bar(
                x=view_prod['Produit'], y=view_prod['Capacity'],
                name='Capacité Maximale', marker_color='#2ecc71',
                opacity=0.6
            ))
            
            # Barre Demande
            fig_bal.add_trace(go.Bar(
                x=view_mkt['Produit'], y=view_mkt['Forecast'],
                name='Demande Client', marker_color='#e74c3c',
                width=0.4 # Barre plus fine pour être "dans" l'autre
            ))
        
            fig_bal.update_layout(
                title="<b>Capacité vs Demande</b>",
                barmode='overlay', # Superposition pour bien voir le dépassement
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=60, b=20),
                height=350
            )
            st.plotly_chart(fig_bal, use_container_width=True)
            st.subheader("🎯 Aide à la Décision : Matrice Volume vs Marge")
        
        # On fusionne les données pour le graphique
        df_matrix = pd.merge(view_mkt, view_fin, on='Produit')
        
        fig_scatter = px.scatter(
            df_matrix, 
            x='Forecast', 
            y='Margin_Unit',
            size='Forecast', 
            color='Margin_Unit',
            hover_name='Produit',
            text='Produit',
            color_continuous_scale='RdYlGn',
            title="Où couper en priorité ? (Haut-Droit = Priorité absolue)"
        )
        
        fig_scatter.update_traces(textposition='top center')
        fig_scatter.add_hline(y=df_matrix['Margin_Unit'].mean(), line_dash="dot", annotation_text="Marge Moyenne")

      st.plotly_chart(fig_scatter, use_container_width=True)

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
