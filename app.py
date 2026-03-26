import streamlit as st
import pandas as pd
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# --- CLASSE POUR CAPTURER LA DISCUSSION ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self):
        pass

st.set_page_config(page_title="S&OP Intelligent Dashboard", layout="wide", page_icon="📈")

# --- BARRE LATÉRALE ---
st.sidebar.title("📖 Guide & Import")
with st.sidebar.expander("Format Excel Requis"):
    st.write("3 Onglets : **Demande**, **Production**, **Finance_Achats**")

uploaded_file = st.sidebar.file_uploader("Charger le fichier SOP_Data.xlsx", type=['xlsx'])

# --- ZONE PRINCIPALE ---
st.title("🏭 Pilotage Stratégique S&OP par IA")

if uploaded_file is not None:
    try:
        # 1. LECTURE DES DONNÉES
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')

        # 2. CALCUL DES KPIs (Partie Ingénierie)
        total_demand = df_mkt['Marketing_Forecast'].sum()
        total_capacity = df_prod['Capacity'].sum()
        avg_margin = df_fin['Margin_Unit'].mean()
        critical_leads = df_fin[df_fin['Supplier_LeadTime'] > 30].shape[0]

        # 3. AFFICHAGE DES MÉTRIQUES (KPIs)
        st.subheader("📊 Indicateurs Clés de Performance (KPIs)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        kpi1.metric("Demande Totale", f"{total_demand} u")
        kpi2.metric("Capacité Totale", f"{total_capacity} u", f"{total_capacity - total_demand} écart")
        kpi3.metric("Marge Moyenne", f"{avg_margin:.0f} €")
        kpi4.metric("Risques Achats", f"{critical_leads} alertes", delta_color="inverse")

        st.divider()

        # 4. VISUALISATION GRAPHIQUE
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.write("### 📈 Offre vs Demande par Produit")
            # Fusion pour comparer demande et capacité
            comparison_df = df_mkt.merge(df_prod, on='Produit')
            st.bar_chart(comparison_df.set_index('Produit')[['Marketing_Forecast', 'Capacity']])

        with col_chart2:
            st.write("### 💰 Rentabilité par Produit")
            st.line_chart(df_fin.set_index('Produit')['Margin_Unit'])

        st.divider()

        # 5. ZONE IA
        col_cmd, col_res = st.columns([1, 1])

        with col_cmd:
            st.subheader("🤖 Orchestration IA")
            if st.button("🚀 Lancer l'Analyse des Agents"):
                terminal_placeholder = st.empty()
                redir = StreamlitRedirect(terminal_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir

                try:
                    # On passe les données en texte aux agents
                    txt_mkt = df_mkt.to_string()
                    txt_prod = df_prod.to_string()
                    txt_fin = df_fin.to_string()

                    t1 = Task(description=f"Analyse DEMANDE : {txt_mkt}", expected_output="Note marketing", agent=SOP.marketing)
                    t2 = Task(description=f"Valide volumes : {txt_mkt}", expected_output="Ventes validées", agent=SOP.sales)
                    t3 = Task(description=f"Compare PROD : {txt_prod}. Calcule le taux d'utilisation.", expected_output="Alerte goulots", agent=SOP.supply)
                    t4 = Task(description=f"Analyse ACHATS : {txt_fin}", expected_output="Risques délais", agent=SOP.purchasing)
                    t5 = Task(description=f"Calcul FINANCE : {txt_fin}", expected_output="Marge totale", agent=SOP.finance)
                    t6 = Task(description="Rédige le Rapport Final PIC complet en français.", expected_output="Rapport S&OP Final", agent=SOP.orchestrator)

                    equipe = Crew(
                        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                        tasks=[t1, t2, t3, t4, t5, t6],
                        process=Process.sequential
                    )

                    resultat = equipe.kickoff()
                    st.session_state['resultat_sop'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

        with col_res:
            st.subheader("📋 Rapport de Décision Final")
            if 'resultat_sop' in st.session_state:
                st.success("Analyse terminée !")
                st.markdown(st.session_state['resultat_sop'])
            else:
                st.info("Lancez l'IA pour obtenir le plan d'action stratégique.")

    except Exception as e:
        st.error(f"Erreur de traitement : {e}")
else:
    st.info("👋 Veuillez importer votre fichier Excel pour générer le dashboard et l'analyse.")
