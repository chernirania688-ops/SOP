import streamlit as st
import pandas as pd
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# --- CLASSE TECHNIQUE POUR REDIRIGER LE TERMINAL VERS STREAMLIT ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""

    def write(self, text):
        # Nettoyage des codes couleurs du terminal (ANSI) pour que le texte soit propre
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        # On affiche le texte dans un bloc de type "code" pour garder le format terminal
        self.placeholder.code(self.output)

    def flush(self):
        pass

st.set_page_config(page_title="IA Agentique S&OP Pro", layout="wide", page_icon="📊")

st.title("🏭 Pilotage Stratégique S&OP")
st.markdown("### Orchestration Multi-Agents en temps réel")

# --- BARRE LATÉRALE ---
st.sidebar.header("📂 Gestion des Données")
uploaded_file = st.sidebar.file_uploader("Charger le fichier SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        onglet = st.sidebar.selectbox("Visualiser les données", xls.sheet_names)
        st.sidebar.write(pd.read_excel(xls, onglet))

        # Extraction des données
        data_mkt = pd.read_excel(xls, 'Demande').to_string()
        data_prod = pd.read_excel(xls, 'Production').to_string()
        data_fin = pd.read_excel(xls, 'Finance_Achats').to_string()

        # --- ZONE CENTRALE ---
        col_cmd, col_res = st.columns([1, 1])

        with col_cmd:
            st.subheader("⚙️ Panneau de Contrôle")
            if st.button("🚀 Lancer le Cycle S&OP"):
                st.info("🤖 **Discussion des agents en direct :**")
                
                # Zone où la discussion va défiler
                terminal_placeholder = st.empty()
                
                # Activation de la redirection
                redir = StreamlitRedirect(terminal_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir

                try:
                    # Définition des tâches (on utilise les agents de SOP.py)
                    t1 = Task(description=f"Analyse DEMANDE : {data_mkt}", expected_output="Analyse marketing", agent=SOP.marketing)
                    t2 = Task(description=f"Valide volumes : {data_mkt}", expected_output="Ventes validées", agent=SOP.sales)
                    t3 = Task(description=f"Compare PROD : {data_prod}", expected_output="Saturation usine", agent=SOP.supply)
                    t4 = Task(description=f"Analyse ACHATS : {data_fin}", expected_output="Risques supply", agent=SOP.purchasing)
                    t5 = Task(description=f"Calcul FINANCE : {data_fin}", expected_output="Bilan financier", agent=SOP.finance)
                    t6 = Task(description="Rédige le Rapport Final PIC.", expected_output="Rapport S&OP Final", agent=SOP.orchestrator)

                    equipe = Crew(
                        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                        tasks=[t1, t2, t3, t4, t5, t6],
                        process=Process.sequential
                    )

                    resultat = equipe.kickoff()
                    st.session_state['resultat_sop'] = str(resultat)
                
                finally:
                    # On remet le terminal à la normale
                    sys.stdout = old_stdout

        with col_res:
            st.subheader("📋 Rapport Stratégique Final")
            if 'resultat_sop' in st.session_state:
                st.success("Analyse terminée !")
                st.markdown(st.session_state['resultat_sop'])
            else:
                st.write("Le rapport final s'affichera ici après la discussion des agents.")

    except Exception as e:
        st.error(f"⚠️ Erreur : {e}")
else:
    st.info("👋 Importez votre fichier Excel pour commencer.")
