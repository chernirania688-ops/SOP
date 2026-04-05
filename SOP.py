import streamlit as st
from crewai import Agent, LLM
from langchain_experimental.utilities import PythonREPL

# =================================================================
# 1. DÉFINITION DU CERVEAU (Variable : cerveau_local)
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    # Si on est sur Streamlit Cloud (Utilise Groq)
    cerveau_local = LLM(
        model="groq/llama-3.3-70b-versatile", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    # Si on est sur votre PC (Utilise Ollama) - Correction de l'indentation ici
    cerveau_local = LLM(
        model="ollama/llama3.2:1b",
        base_url="http://localhost:11434"
    )

# Outil de calcul pour la Finance
def python_repl_tool(code: str):
    """Exécute du code python pour des calculs précis de marge et volume."""
    return PythonREPL().run(code)

# =================================================================
# 2. DÉFINITION DES AGENTS
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de demande et ajuster selon le contexte de marché.',
    backstory='Expert en prévisions de ventes. Tu analyses les besoins clients.',
    llm=cerveau_local, 
    verbose=True, 
    allow_delegation=False
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes de vente finaux.',
    backstory='Tu compares le Forecast et les Orders. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True
)

supply = Agent(
    role='Planificateur de Production / Supply Chain',
    goal='Vérifier la faisabilité technique et les stocks.',
    backstory='Garant des machines et des matières premières. Tu alertes si on ne peut pas produire.',
    llm=cerveau_local, 
    verbose=True, 
    allow_delegation=False
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture basés sur les délais fournisseurs.',
    backstory='Tu analyses les Lead Times. Réponds toujours en français.',
    llm=cerveau_local,
    verbose=True
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Garantir la rentabilité du plan S&OP.',
    backstory='Tu es un expert en calcul de coûts. Tu utilises des outils de calcul pour valider la marge.',
    llm=cerveau_local, 
    verbose=True,
    tools=[python_repl_tool] # L'outil est maintenant activé
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Piloter la performance globale et valider le Plan Industriel et Commercial (PIC).',
    backstory="""Tu es le garant de la stratégie. Ton rapport final doit être structuré,
    professionnel et inclure des indicateurs clés (KPIs). Tu arbitres les conflits en favorisant
    les produits à plus forte marge quand la capacité manque.""",
    llm=cerveau_local, 
    verbose=True
)

# =================================================================
# 3. PROTECTION DE L'IMPORT
# =================================================================
# Empêche l'exécution automatique lors de l'importation par l'app principale
if __name__ == "__main__":
    print("Le module SOP est prêt.")
