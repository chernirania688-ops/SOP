import streamlit as st
from crewai import Agent, LLM
from langchain.tools import tool # Import important
from langchain_experimental.utilities import PythonREPL

# =================================================================
# 1. DÉFINITION DU CERVEAU
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(
        model="groq/llama-3.3-70b-versatile", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(
        model="ollama/llama3.2:1b",
        base_url="http://localhost:11434"
    )

# =================================================================
# 2. DÉFINITION DE L'OUTIL (Correction ici)
# =================================================================

@tool("python_repl_tool")
def python_repl_tool(code: str):
    """
    Exécute du code python pour des calculs précis de marge et volume.
    L'entrée doit être du code Python valide (ex: print(1250 * 45)).
    """
    return PythonREPL().run(code)

# =================================================================
# 3. DÉFINITION DES AGENTS
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de demande.',
    backstory='Expert en prévisions de ventes.',
    llm=cerveau_local, 
    verbose=True, 
    allow_delegation=False
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes de vente finaux.',
    backstory='Tu compares le Forecast et les Orders.',
    llm=cerveau_local,
    verbose=True
)

supply = Agent(
    role='Planificateur de Production',
    goal='Vérifier la faisabilité technique et les stocks.',
    backstory='Garant des machines et des matières premières.',
    llm=cerveau_local, 
    verbose=True, 
    allow_delegation=False
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture.',
    backstory='Tu analyses les Lead Times.',
    llm=cerveau_local,
    verbose=True
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Garantir la rentabilité du plan S&OP.',
    backstory='Expert en calcul de coûts. Tu utilises des outils de calcul pour valider la marge.',
    llm=cerveau_local, 
    verbose=True,
    tools=[python_repl_tool] # Maintenant c'est un objet tool valide
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Piloter la performance globale et valider le PIC.',
    backstory='Tu es le garant de la stratégie. Ton rapport final doit être structuré.',
    llm=cerveau_local, 
    verbose=True
)

if __name__ == "__main__":
    print("Le module SOP est prêt.")
