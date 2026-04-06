import streamlit as st
from crewai import Agent, LLM

# --- 1. DÉFINITION DU CERVEAU ---
if "GROQ_API_KEY" in st.secrets:
    cerveau_local = LLM(
        model="groq/llama-3.1-8b-instant", 
        api_key=st.secrets["GROQ_API_KEY"]
    )
else:
    cerveau_local = LLM(model="ollama/llama3.1:8b", base_url="http://localhost:11434")

# --- 2. DÉFINITION DES 6 AGENTS ---
marketing = Agent(
    role='Directeur Marketing Stratégique',
    goal='Analyser la demande et définir les priorités de marque.',
    backstory="Tu es le gardien de l'image de marque. On ne supprime JAMAIS les Smartphones.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

sales = Agent(
    role='Directeur Commercial',
    goal='Valider la réalité des ventes.',
    backstory="Tu compares le Forecast et les Sales_Orders.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

supply = Agent(
    role='Directeur Industriel',
    goal='Résoudre les goulots d étranglement.',
    backstory="Si Machine_Status est Goulot, tu proposes des solutions.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

purchasing = Agent(
    role='Responsable Achats',
    goal='Sécuriser les composants.',
    backstory="Tu proposes des fournisseurs alternatifs.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

finance = Agent(
    role='CFO (Directeur Financier)',
    goal='Maximiser le profit net.',
    backstory="Tu es obsédé par le Profit Total.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

orchestrator = Agent(
    role='Directeur S&OP',
    goal='Rédiger le PIC final et trancher les conflits.',
    backstory="Tu dois obligatoirement produire un Tableau de Synthèse final.",
    llm=cerveau_local, verbose=True, max_rpm=1
)

if __name__ == "__main__":
    print("Module SOP prêt.")
