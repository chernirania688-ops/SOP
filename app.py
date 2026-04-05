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

st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Configuration")
with st.sidebar.expander("📖 Format Excel Requis", expanded=False):
    st.write("Onglet **Demande**: Produit, Marketing_Forecast, Sales_Orders")
    st.write("Onglet **Production**: Produit, Capacity, Stock_Level")
    st.write("Onglet **Finance_Achats**: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")

uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("---")

if uploaded_file is not None:
    try:
        # 1. LECTURE ET NETTOYAGE DES DONNÉES
        xls = pd.ExcelFile(uploaded_file)
        onglets_requis = ['Demande', 'Production', 'Finance_Achats']
        
        if not all(sheet in xls.sheet_names for sheet in onglets_requis):
            st.error(f"❌ Structure incorrecte ! Onglets requis : {onglets_requis}")
            st.stop()

        df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
        df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
        df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

        # 2. KPIs ANALYTIQUES
        st.subheader("📊 Indicateurs Clés de Performance (Situation Initiale)")
        total_demand = df_mkt['Forecast'].sum()
        total_capacity = df_prod['Capacity'].sum()
        saturation = (total_demand / total_capacity) * 100 if total_capacity > 0 else 0
        alertes_achats = df_fin[df_fin['Supplier_LeadTime'] > 30].shape[0]

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Demande Globale", f"{total_demand:,.0f} u")
        kpi2.metric("Capacité Usine", f"{total_capacity:,.0f} u")
        kpi3.metric("Taux de Saturation", f"{saturation:.1f} %", delta=f"{saturation-100:.1f}%", delta_color="inverse")
        kpi4.metric("Risques Achats (>30j)", f"{alertes_achats} alertes")

        # 3. GRAPHIQUES PLOTLY
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(x=df_mkt['Produit'], y=df_mkt['Forecast'], name='Demande', marker_color='#007bff'))
            fig_comp.add_trace(go.Bar(x=df_prod['Produit'], y=df_prod['Capacity'], name='Capacité', marker_color='#ff7f0e'))
            fig_comp.update_layout(title="Équilibre Offre vs Demande par Produit", barmode='group', height=350)
            st.plotly_chart(fig_comp, use_container_width=True)

        with col_v2:
            fig_margin = px.bar(df_fin, x='Produit', y='Margin_Unit', color='Margin_Unit', 
                                title="Marge Unitaire par Produit (€)", color_continuous_scale='Greens', height=350)
            st.plotly_chart(fig_margin, use_container_width=True)

        st.markdown("---")

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

        # 5. ORCHESTRATION AGENTIQUE
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
                    txt_mkt = df_mkt.to_string(); txt_prod = df_prod.to_string(); txt_fin = df_fin.to_string()

                    # INJECTION DU SCÉNARIO DANS LES TÂCHES
                    t1 = Task(description=f"CONTEXTE: {contexte_simulation}. Analyse l'onglet Demande: {txt_mkt}.", expected_output="Rapport demande.", agent=SOP.marketing)
                    t2 = Task(description=f"CONTEXTE: {contexte_simulation}. Valide les volumes finaux.", expected_output="Volumes validés.", agent=SOP.sales)
                    t3 = Task(description=f"CONTEXTE: {contexte_simulation}. Compare avec Production: {txt_prod}. Identifie les goulots d'étranglement.", expected_output="Faisabilité usine.", agent=SOP.supply)
                    t4 = Task(description=f"CONTEXTE: {contexte_simulation}. Analyse Achats et risques délais: {txt_fin}.", expected_output="Risques fournisseurs.", agent=SOP.purchasing)
                    t5 = Task(description=f"CONTEXTE: {contexte_simulation}. Calcule la rentabilité totale avec Finance_Achats: {txt_fin}.", expected_output="Bilan financier.", agent=SOP.finance)
                    t6 = Task(description=f"""CONTEXTE: {contexte_simulation}. Rédige le Rapport Stratégique Final. 
                              Il DOIT contenir: 1. Décisions sur les volumes. 2. Actions face à l'événement simulé. 3. Rentabilité finale.""", 
                              expected_output="Plan S&OP Final.", agent=SOP.orchestrator)

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
                    st.success("✅ Plan S&OP généré avec succès !")
                    st.markdown(st.session_state['resultat_sop'])

    except Exception as e:
        st.error(f"⚠️ Erreur de traitement : {e}")

else:
    st.info("👋 Bienvenue ! Importez le fichier Excel dans le menu de gauche pour démarrer le simulateur.")
