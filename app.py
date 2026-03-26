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

st.set_page_config(page_title="Dashboard S&OP Intelligent", layout="wide", page_icon="📈")

# --- BARRE LATÉRALE ---
st.sidebar.title("🚀 Configuration")
with st.sidebar.expander("📖 Format Excel Requis"):
    st.write("- **Demande**: Produit, Forecast, Sales_Orders")
    st.write("- **Production**: Produit, Capacity, Stock_Level")
    st.write("- **Finance_Achats**: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")

uploaded_file = st.sidebar.file_uploader("Charger le fichier S&OP (.xlsx)", type=['xlsx'])

# --- LOGIQUE PRINCIPALE ---
st.title("🏭 Pilotage Stratégique S&OP par IA Agentique")

if uploaded_file is not None:
    try:
        # 1. Lecture et Nettoyage des données
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande'); df_mkt.columns = df_mkt.columns.str.strip()
        df_prod = pd.read_excel(xls, 'Production'); df_prod.columns = df_prod.columns.str.strip()
        df_fin = pd.read_excel(xls, 'Finance_Achats'); df_fin.columns = df_fin.columns.str.strip()

       # --- SECTION KPI SÉCURISÉE ---
        st.subheader("📊 Indicateurs Clés de Performance (Analytique)")
        
        # On vérifie si les colonnes existent avant de calculer
        if 'Marketing_Forecast' in df_mkt.columns and 'Capacity' in df_prod.columns:
            total_demand = df_mkt['Marketing_Forecast'].sum()
            total_cap = df_prod['Capacity'].sum()
            saturation = (total_demand / total_cap) * 100 if total_cap > 0 else 0
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Demande Totale", f"{total_demand} u")
            kpi2.metric("Capacité Totale", f"{total_cap} u")
            kpi3.metric("Taux de Saturation", f"{saturation:.1f} %")
        else:
            st.error("❌ Erreur : Colonne 'Marketing_Forecast' ou 'Capacity' introuvable dans l'Excel.")
            st.write("Colonnes présentes dans Demande :", df_mkt.columns.tolist())
            st.write("Colonnes présentes dans Production :", df_prod.columns.tolist())

        # 3. Visualisation Plotly
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_mkt['Produit'], y=df_mkt['Marketing_Forecast'], name='Demande', marker_color='#007bff'))
            fig.add_trace(go.Bar(x=df_prod['Produit'], y=df_prod['Capacity'], name='Capacité', marker_color='#ff7f0e'))
            fig.update_layout(title="Équilibre Offre vs Demande", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            fig2 = px.pie(df_fin, values='Margin_Unit', names='Produit', title="Répartition des Marges Unitaires", hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        # 4. Orchestration IA
        col_ia_cmd, col_ia_res = st.columns([1, 1])

        with col_ia_cmd:
            st.subheader("🤖 Intelligence Agentique")
            if st.button("🚀 Lancer l'Orchestration des Agents"):
                log_area = st.empty()
                redir = StreamlitRedirect(log_area)
                old_stdout = sys.stdout
                sys.stdout = redir

                try:
                    # Conversion des données en texte pour l'IA
                    txt_mkt = df_mkt.to_string(); txt_prod = df_prod.to_string(); txt_fin = df_fin.to_string()

                    t1 = Task(description=f"Analyse Demande: {txt_mkt}", expected_output="Rapport demande", agent=SOP.marketing)
                    t2 = Task(description="Valide les volumes finaux.", expected_output="Volumes validés", agent=SOP.sales)
                    t3 = Task(description=f"Vérifie Production: {txt_prod}", expected_output="Faisabilité", agent=SOP.supply)
                    t4 = Task(description=f"Vérifie Achats: {txt_fin}", expected_output="Risques délais", agent=SOP.purchasing)
                    t5 = Task(description=f"Calcule Finance: {txt_fin}", expected_output="Marge totale", agent=SOP.finance)
                    t6 = Task(description="Rédige le Rapport Stratégique S&OP Final complet et structuré en français.", 
                              expected_output="Rapport PIC Final", agent=SOP.orchestrator)

                    crew = Crew(agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                                tasks=[t1, t2, t3, t4, t5, t6], process=Process.sequential)

                    resultat = crew.kickoff()
                    st.session_state['res_sop'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

        with col_ia_res:
            st.subheader("📋 Rapport de Décision Final")
            if 'res_sop' in st.session_state:
                st.markdown(st.session_state['res_sop'])
                st.download_button("📥 Télécharger le Plan (.txt)", st.session_state['res_sop'], "Rapport_SOP.txt")

    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("👋 Veuillez charger votre fichier Excel pour activer le Dashboard.")
