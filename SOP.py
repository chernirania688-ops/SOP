import streamlit as st
from crewai import Agent, LLM

# =================================================================
# 1. DÉFINITION DU CERVEAU (Variable : cerveau_local)
# =================================================================

# Cette logique permet de basculer entre Groq (Cloud) et Ollama (Local)
if "GROQ_API_KEY" in st.secrets:
    # Si on est sur Streamlit Cloud (Utilise Groq)
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant"
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    # Si on est sur votre PC (Utilise Ollama)
    cerveau_local = LLM(
        model="ollama/llama3.1:8b",
        base_url="http://localhost:11434"
    )

# =================================================================
# 2. DÉFINITION DES AGENTS (Vérifiez qu'ils utilisent bien cerveau_local)
# =================================================================

marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de l onglet Demande.',
    backstory='Tu es un expert en chiffres. Réponds toujours en français.',
    llm=cerveau_local,
    max_rpm=2,
    verbose=True
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes de vente finaux.',
    backstory='Tu compares le Forecast et les Orders. Réponds toujours en français.',
    llm=cerveau_local,
    max_rpm=2,
    verbose=True
)

supply = Agent(
    role='Planificateur de Production',
    goal='Comparer les besoins de vente avec la capacité réelle de l usine.',
    backstory='Tu es ingénieur en production. Réponds toujours en français.',
    llm=cerveau_local,
    max_rpm=2,
    verbose=True
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture basés sur les délais fournisseurs.',
    backstory='Tu analyses les Lead Times. Réponds toujours en français.',
    llm=cerveau_local,
    max_rpm=2,
    verbose=True
)

finance = Agent(
    role='Contrôleur de Gestion Industriel',
    goal='Calculer la rentabilité financière globale (Volume x Marge).',
    backstory="""Tu es un expert en calcul de coûts. Tu ne te contentes pas d'additionner les marges unitaires. 
    Tu multiplies CHAQUE volume validé par sa marge unitaire pour donner le profit total en euros. 
    Tu es très précis avec les chiffres.""",
    llm=cerveau_local,
    max_rpm=2,
    verbose=True
)

orchestrator = Agent(
    role='Directeur S&OP (COO)',
    goal='Piloter la performance globale et valider le Plan Industriel et Commercial (PIC).',
    backstory="""Tu es le garant de la stratégie. Ton rapport final doit être structuré, 
    professionnel et inclure des indicateurs clés (KPIs). Tu arbitres les conflits en favorisant 
    les produits à plus forte marge quand la capacité manque.""",
    llm=cerveau_local, verbose=True
)
# Empêche l'exécution automatique lors de l'import
if __name__ == "__main__":
    print("Le module SOP est prêt.")
