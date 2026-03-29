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
    def flush(self): pass

st.set_page_config(page_title="S&OP Strategy Simulator", layout="wide", page_icon="🧪")

st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
st.markdown("### Orchestration Multi-Agents avec Gestion d'Événements Imprévus")

# --- BARRE LATÉRALE ---
st.sidebar.header("📂 1. Données Source")
uploaded_file = st.sidebar.file_uploader("Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        data_mkt = pd.read_excel(xls, 'Demande').to_string()
        data_prod = pd.read_excel(xls, 'Production').to_string()
        data_fin = pd.read_excel(xls, 'Finance_Achats').to_string()
        st.sidebar.success("✅ Données chargées")

        # --- ZONE DE SÉLECTION DU SCÉNARIO (LA NOUVEAUTÉ) ---
        st.subheader("🎭 2. Paramétrage du Scénario")
        
        col_sc1, col_sc2 = st.columns([2, 1])
        
        with col_sc1:
            liste_scenarios = [
                "🟢 Situation Nominale (Aucun imprévu)",
                "🔴 Crise Logistique (Grève des ports : Délais fournisseurs doublés)",
                "🔴 Aléa de Production (Panne majeure : Capacité réduite de 30%)",
                "🔵 Opportunité Marketing (Campagne virale : Demande augmentée de 50%)",
                "🟠 Tension Économique (Inflation : Coûts matières augmentés de 20%)"
            ]
            scenario_choisi = st.selectbox("Sélectionnez un événement à simuler :", liste_scenarios)
        
        with col_sc2:
            st.write("---")
            st.info(f"**Contexte actuel :** {scenario_choisi}")

        # --- ZONE D'ACTION ---
        col_cmd, col_res = st.columns([1, 1])

        with col_cmd:
            st.subheader("⚙️ 3. Lancement")
            if st.button("🚀 Lancer l'Analyse Agentique"):
                st.info("🤖 **Discussion des agents (Analyse sous contrainte) :**")
                terminal_placeholder = st.empty()
                redir = StreamlitRedirect(terminal_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir

                try:
                    # On injecte le scénario dans la description de chaque tâche
                    contexte = f"CONTEXTE DE SIMULATION : {scenario_choisi}."

                    t1 = Task(description=f"{contexte} Analyse DEMANDE : {data_mkt}.", 
                              expected_output="Note marketing adaptée au scénario.", agent=SOP.marketing)
                    
                    t2 = Task(description=f"{contexte} Valide les volumes finaux.", 
                              expected_output="Volumes validés.", agent=SOP.sales)

                    t3 = Task(description=f"{contexte} Compare avec PRODUCTION : {data_prod}. Identifie les goulots créés par cet événement.", 
                              expected_output="Faisabilité technique.", agent=SOP.supply)

                    t4 = Task(description=f"{contexte} Analyse ACHATS : {data_fin}. Quel est l'impact de l'événement sur l'approvisionnement ?", 
                              expected_output="Analyse de risque.", agent=SOP.purchasing)

                    t5 = Task(description=f"{contexte} Calcul FINANCE : {data_fin}. Quel est l'impact de cet événement sur le profit global ?", 
                              expected_output="Bilan financier.", agent=SOP.finance)

                    t6 = Task(description=f"""{contexte} Rédige le Rapport Stratégique Final. 
                              Explique CLAIREMENT comment l'entreprise doit s'adapter à cet événement spécifique.""", 
                              expected_output="Plan S&OP de Crise / Opportunité.", agent=SOP.orchestrator)

                    equipe = Crew(
                        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
                        tasks=[t1, t2, t3, t4, t5, t6],
                        process=Process.sequential
                    )

                    resultat = equipe.kickoff()
                    st.session_state['res_final'] = str(resultat)
                finally:
                    sys.stdout = old_stdout

        with col_res:
            st.subheader("📋 4. Rapport Stratégique Final")
            if 'res_final' in st.session_state:
                st.success("Simulation terminée !")
                st.markdown(st.session_state['res_final'])
                st.download_button("📥 Télécharger le Plan de simulation", st.session_state['res_final'], "Simulation_SOP.txt")

    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("👋 Veuillez importer votre fichier Excel pour activer le simulateur.")
