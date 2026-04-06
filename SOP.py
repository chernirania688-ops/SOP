import streamlit as st
from crewai import Agent, LLM

# --- 1. DÉFINITION DU LLM (8B-Instant pour la stabilité) ---
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(model="ollama/llama3.1:8b", base_url="http://localhost:11434")

# --- 2. DÉFINITION DES 3 SUPER-AGENTS ---
# On fusionne les rôles pour réduire les appels API

demand_expert = Agent(
    role='Directeur Demande et Ventes',
    goal='Analyser les tendances marketing et valider les volumes de ventes terrain.',
    backstory='Tu es l expert qui réconcilie les prévisions marketing et la réalité des commandes.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

ops_expert = Agent(
    role='Directeur des Opérations et Achats',
    goal='Optimiser la production usine et sécuriser les approvisionnements fournisseurs.',
    backstory='Tu gères les goulots d usine et les risques de rupture matières premières.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

ceo_expert = Agent(
    role='Directeur Stratégique et Financier (CFO/COO)',
    goal='Arbitrer le plan final pour maximiser le profit et rédiger le rapport PIC.',
    backstory='Tu décides des arbitrages finaux en fonction de la rentabilité et de la stratégie.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

if __name__ == "__main__":
    print("Module SOP prêt avec Super-Agents.")
