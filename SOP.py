import streamlit as st
from crewai import Agent, LLM

# =================================================================
# 1. DÉFINITION DU CERVEAU (Modèle 8B Instant pour Groq)
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    # Utilisation du modèle exact supporté par Groq
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    # Option locale si vous utilisez Ollama
    cerveau_local = LLM(
        model="ollama/llama3.1:8b",
        base_url="http://localhost:11434"
    )

# =================================================================
# 2. DÉFINITION DES AGENTS
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de demande.',
    backstory='Expert en prévisions de ventes. Réponds toujours en français.',
    llm=cerveau_local, 
    verbose=True,
    max_rpm=2
)

supply = Agent(
    role='Planificateur de Production',
    goal='Vérifier la faisabilité technique.',
    backstory='Garant des machines et des capacités. Réponds toujours en français.',
    llm=cerveau_local, 
    verbose=True,
    max_rpm=2
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Garantir la rentabilité du plan S&OP.',
    backstory='Expert en calcul de coûts. Réponds toujours en français.',
    llm=cerveau_local, 
    verbose=True,
    max_rpm=2
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Arbitrer les conflits et valider le PIC.',
    backstory='Garant de la stratégie globale. Réponds toujours en français.',
    llm=cerveau_local, 
    verbose=True,
    max_rpm=2
)

# Protection pour l'importation
if __name__ == "__main__":
    print("Le module SOP est prêt.")
