import streamlit as st
from crewai import Agent, LLM

# =================================================================
# 1. DÉFINITION DU CERVEAU (Modèle 8B Instant pour Groq)
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(
        model="ollama/llama3.1:8b",
        base_url="http://localhost:11434"
    )

# =================================================================
# 2. DÉFINITION DES 6 AGENTS (Alignement Strict)
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de demande globale.',
    backstory='Expert en prévisions de ventes et tendances marché.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes finaux en comparant Forecast et Commandes.',
    backstory='Garant des objectifs commerciaux et de la réalité terrain.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

supply = Agent(
    role='Planificateur de Production',
    goal='Vérifier la faisabilité technique et la capacité usine.',
    backstory='Expert en gestion des lignes de production et goulots.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture liés aux délais fournisseurs.',
    backstory='Expert en gestion des matières premières et lead times.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Calculer la rentabilité financière globale du plan.',
    backstory='Garant de la marge et de la santé financière.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Arbitrer les conflits et valider le Plan Industriel et Commercial (PIC).',
    backstory='Décideur final. Arbitre selon la marge et la stratégie.',
    llm=cerveau_local, verbose=True, max_rpm=1
)

if __name__ == "__main__":
    print("Module SOP prêt avec 6 agents.")
