import os
from crewai import Agent, LLM

# Configuration pour le Cloud (Groq) ou le Local (Ollama)
# Sur le Cloud, on récupérera la clé depuis les "Secrets" de Streamlit
api_key = os.getenv("GROQ_API_KEY") 

if api_key:
    # Configuration CLOUD (Groq) - Ultra rapide
    cerveau = LLM(
        model="groq/llama-3.3-70b-versatile", 
        api_key=api_key
    )
else:

# ... GARDEZ LE RESTE DE VOS AGENTS ICI (en utilisant 'llm=cerveau') ...
   cerveau_local = LLM(
    model="ollama/llama3.2:1b", 
    base_url="http://localhost:11434",
    timeout=2200,
    temperature=0.1
)

# 2. DÉFINITION DES 6 AGENTS
marketing = Agent(
    role='Analyste Marketing',
    goal='Extraire les tendances de l onglet Demande.',
    backstory='Tu es un expert en chiffres. Tu ne commentes que les données présentes dans le fichier.',
    llm=cerveau_local, verbose=True
)

sales = Agent(
    role='Responsable des Ventes',
    goal='Valider les volumes de vente finaux.',
    backstory='Tu compares le Forecast et les Orders. Tu donnes un chiffre ferme.',
    llm=cerveau_local, verbose=True
)

supply = Agent(
    role='Planificateur de Production',
    goal='Comparer les besoins de vente avec la capacité réelle de l usine.',
    backstory='Tu es ingénieur. Si la demande > capacité, tu dois alerter immédiatement.',
    llm=cerveau_local, verbose=True
)

purchasing = Agent(
    role='Acheteur Industriel',
    goal='Identifier les risques de rupture basés sur les délais fournisseurs.',
    backstory='Tu analyses les Lead Times. Si un délai > 30 jours, c est un risque.',
    llm=cerveau_local, verbose=True
)

finance = Agent(
    role='Contrôleur de Gestion',
    goal='Calculer la marge brute totale du plan.',
    backstory='Tu multiplies les volumes par la marge unitaire du fichier Finance.',
    llm=cerveau_local, verbose=True
)

orchestrator = Agent(
    role='Directeur S&OP',
    goal='Créer la synthèse finale équilibrée entre Vente, Production et Finance.',
    backstory='Tu es le chef. Ton rapport final doit citer des chiffres des 3 fichiers.',
    llm=cerveau_local, verbose=True
)
# Ce bloc empêche le script de se lancer tout seul lors de l'import par Streamlit
if __name__ == "__main__":
    print("Script chargé en mode bibliothèque. Utilisez app.py pour lancer l'interface.")
