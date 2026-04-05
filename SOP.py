import streamlit as st
from crewai import Agent, LLM

# =================================================================
# 1. DÉFINITION DU CERVEAU (Optimisé pour Groq)
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    # Utilisation du modèle 8b pour éviter les Rate Limits
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant",
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(
        model="ollama/llama3.2:1b",
        base_url="http://localhost:11434"
    )

# =================================================================
# 2. DÉFINITION DES AGENTS
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de l onglet Demande.',
    backstory='Tu es un expert en chiffres. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes de vente finaux.',
    backstory='Tu compares le Forecast et les Orders. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

supply = Agent(
    role='Planificateur de Production',
    goal='Comparer les besoins de vente avec la capacité réelle de l usine.',
    backstory='Tu es ingénieur en production. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture basés sur les délais fournisseurs.',
    backstory='Tu analyses les Lead Times. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

finance = Agent(
    role='Contrôleur de Gestion Industriel',
    goal='Calculer la rentabilité financière globale.',
    backstory='Tu es un expert en calcul de coûts. Précis avec les chiffres.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Piloter la performance globale et valider le PIC.',
    backstory='Tu es le garant de la stratégie. Tu arbitres les conflits.',
    llm=cerveau_local,
    verbose=True,
    max_rpm=1
)

# Empêche l'exécution automatique lors de l'import
if __name__ == "__main__":
    print("Le module SOP est prêt.")
