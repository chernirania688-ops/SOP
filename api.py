from fastapi import FastAPI
from pydantic import BaseModel
import SOP # Importe tes agents de SOP.py
from crewai import Crew, Process, Task

app = FastAPI()

# Modèle de données que Power Apps va envoyer
class SOPInput(BaseModel):
    marketing_txt: str
    production_txt: str
    finance_txt: str

@app.get("/")
def home():
    return {"status": "Serveur S&OP en ligne"}

@app.post("/analyser")
async def run_analysis(data: SOPInput):
    # Création dynamique des tâches avec les données reçues de Power Apps
    t1 = Task(description=f"Analyse Demande: {data.marketing_txt}", expected_output="Rapport", agent=SOP.marketing)
    t2 = Task(description="Valide volumes.", expected_output="Ventes", agent=SOP.sales)
    t3 = Task(description=f"Vérifie PROD: {data.production_txt}", expected_output="Capacité", agent=SOP.supply)
    t4 = Task(description=f"Analyse ACHATS: {data.finance_txt}", expected_output="Risques", agent=SOP.purchasing)
    t5 = Task(description=f"Calcul FINANCE: {data.finance_txt}", expected_output="Marge", agent=SOP.finance)
    t6 = Task(description="Rapport Final PIC complet en français.", expected_output="Rapport S&OP", agent=SOP.orchestrator)

    # Lancement du Crew
    crew = Crew(
        agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator],
        tasks=[t1, t2, t3, t4, t5, t6],
        process=Process.sequential
    )

    resultat = crew.kickoff()
    return {"plan_final": str(resultat)}