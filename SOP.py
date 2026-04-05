import streamlit as st
from crewai import Agent, LLM
from langchain_experimental.utilities import PythonREPL

# =================================================================
# 1. DÉFINITION DU CERVEAU (Variable : cerveau_local)
# =================================================================
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(model="groq/llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"])
else:
    # Note : Pour l'orchestration, llama3.1:8b est recommandé si votre PC le permet
    cerveau_local = LLM(model="ollama/llama3.1:8b", base_url="http://localhost:11434")

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
    llm=cerveau_local, verbose=True, allow_delegation=False
)

supply = Agent(
    role='Planificateur de Production / Supply Chain',
    goal='Vérifier la faisabilité technique et les stocks.',
    backstory='Garant des machines et des matières premières. Tu alertes si on ne peut pas produire.',
    llm=cerveau_local, verbose=True, allow_delegation=False
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Garantir la rentabilité du plan S&OP.',
    backstory='Tu utilises des outils de calcul pour valider que le chiffre d affaire et la marge sont exacts.',
    llm=cerveau_local, verbose=True, allow_delegation=False,
    tools=[python_repl_tool]
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Arbitrer les conflits entre Ventes et Production pour maximiser le profit.',
    backstory='Décideur final. Tu privilégies les produits stratégiques en cas de manque de capacité.',
    llm=cerveau_local, verbose=True
)
