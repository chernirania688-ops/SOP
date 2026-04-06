import streamlit as st
from crewai import Agent, LLM

# --- 1. DÉFINITION DU CERVEAU (Modèle 8B pour supporter 6 agents) ---
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(model="ollama/llama3.1:8b", base_url="http://localhost:11434")

# --- 2. DÉFINITION DES 6 AGENTS ---

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de demande.',
    backstory='Expert en prévisions et image de marque.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes finaux terrain.',
    backstory='Garant de la réalité commerciale et des commandes.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

supply = Agent(
    role='Planificateur de Production',
    goal='Vérifier la faisabilité technique et la capacité.',
    backstory='Garant des lignes de production et des goulots.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques fournisseurs et délais.',
    backstory='Expert en approvisionnements et lead times.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Calculer la rentabilité financière globale.',
    backstory='Garant de la marge et de la santé financière.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Arbitrer les conflits et valider le PIC final.',
    backstory='Décideur final stratégique. Arbitre selon la marge.',
    llm=cerveau_local, verbose=True, allow_delegation=False, max_rpm=1
)
# Empêche l'exécution automatique lors de l'import
if __name__ == "__main__":
    print("Le module SOP est prêt.")
