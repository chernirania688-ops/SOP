import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Process, Task
import SOP 
import sys
import re

# --- REDIRECTION DES LOGS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")
# --- BARRE LATÉRALE ---
with st.sidebar.expander("📖 Format Excel Requis", expanded=False):
    st.write("Onglet **Demande**: Produit, Marketing_Forecast, Sales_Orders")
    st.write("Onglet **Production**: Produit, Capacity, Stock_Level")
    st.write("Onglet **Finance_Achats**: Produit, Material_Cost, Margin_Unit, Supplier_LeadTime")

uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])


# --- SIDEBAR ET CHARGEMENT ---
st.sidebar.title("🛠️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')
        for df in [df_mkt, df_prod, df_fin]: df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"❌ Erreur : {e}"); st.stop()

    st.title("🏭 Pilotage Stratégique & Simulateur S&OP")
    
    # --- FILTRE PRODUIT ---
    selected_prod = st.selectbox("🔍 Analyser un produit spécifique :", ["Tous les produits"] + list(df_mkt['Produit'].unique()))
    
    df_mkt_sim = df_mkt.copy(); df_prod_sim = df_prod.copy(); df_fin_sim = df_fin.copy()
    contexte_sim = "SITUATION NORMALE"

    # --- SIMULATEUR ---
    with st.container(border=True):
        st.subheader("🎭 Gestionnaire de Scénarios")
        type_ev = st.radio("Sélectionnez un événement :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande", "🟣 Personnalisé"], horizontal=True)
        if type_ev == "🔴 Aléa Production":
            pct = st.slider("Baisse capacité (%)", 10, 90, 30)
            df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
            contexte_sim = f"CRISE : Capacité réduite de {pct}%."
        elif type_ev == "🔵 Pic Demande":
            pct = st.slider("Hausse demande (%)", 10, 150, 50)
            df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
            contexte_sim = f"PIC : Hausse demande de {pct}%."
        elif type_ev == "🟣 Personnalisé":
            txt = st.text_area("Description :", "Ex: Grève des dockers...")
            contexte_sim = f"ÉVÉNEMENT : {txt}"

    # --- DASHBOARD (KPIs & GRAPHES) ---
    v_mkt = df_mkt_sim if selected_prod == "Tous les produits" else df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
    v_prod = df_prod_sim if selected_prod == "Tous les produits" else df_prod_sim[df_prod_sim['Produit'] == selected_prod]
    v_fin = df_fin_sim if selected_prod == "Tous les produits" else df_fin_sim[df_fin_sim['Produit'] == selected_prod]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Demande", f"{v_mkt['Forecast'].sum():,.0f}")
    k2.metric("Capacité", f"{v_prod['Capacity'].sum():,.0f}")
    k3.metric("Saturation", f"{(v_mkt['Forecast'].sum()/v_prod['Capacity'].sum()*100):.1f}%" if v_prod['Capacity'].sum()>0 else "0%")
    k4.metric("Profit", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_bal = go.Figure()
        fig_bal.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
        fig_bal.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
        fig_bal.update_layout(title="Équilibre Offre/Demande", barmode='overlay', height=400)
        st.plotly_chart(fig_bal, use_container_width=True)

    with col_g2:
        df_profit = pd.merge(v_mkt, v_fin, on='Produit')
        df_profit['Marge_Totale'] = df_profit['Forecast'] * df_profit['Margin_Unit']
        fig_tree = px.treemap(df_profit, path=['Produit'], values='Marge_Totale', color='Margin_Unit',
                              color_continuous_scale='RdYlGn', title="Répartition de la Marge")
        st.plotly_chart(fig_tree, use_container_width=True)

    # --- LANCEMENT IA (Pleine Largeur) ---
    st.markdown("---")
    if st.button("🚀 Lancer le Processus S&OP Collaboratif", use_container_width=True):
        st.info("🧠 Les 6 agents négocient sur toute la page...")
        log_placeholder = st.empty()
        redir = StreamlitRedirect(log_placeholder); sys.stdout = redir
        
        try:
            # Réduction data pour Rate Limit
            t_m = df_mkt_sim.head(10).to_string(); t_p = df_prod_sim.head(10).to_string(); t_f = df_fin.head(10).to_string()

            t1 = Task(description=f"Marketing: Analyse la Demande {t_m}.Identifie les produits stratégique.", agent=SOP.marketing, expected_output="Analyse.")
            t2 = Task(description="Ventes: Valide volumes.Signale les risques de perte de CA.", agent=SOP.sales, expected_output="Ventes.")
            t3 = Task(description=f"Supply: Gère goulots {t_p}.Pour chaque 'Goulot' ou 'Maintenance',propose une solution concréte.", agent=SOP.supply, expected_output="Production.")
            t4 = Task(description=f"Achats: Risques {t_f}.Liste les 3 plus gros risques fournisseurs.", agent=SOP.purchasing, expected_output="Achats.")
            t5 = Task(description=f"Finance:  Calcule le profit {t_f}.", agent=SOP.finance, expected_output="Finance.")
            t6 = Task(
                        description=f"""Directeur S&OP: Rédige la décision finale pour le scénario pour {contexte_sim}.
                        TU DOIS ABSOLUMENT SUIVRE CE PLAN :
                        1. SYNTHÈSE DE LA SITUATION : Rappelle le scénario et le risque majeur.
                        2. ANALYSE OFFRE/DEMANDE : Résume les points bloquants (Goulots, Lead Times).
                        3. IMPACT FINANCIER : Chiffre la perte ou le gain potentiel.
                        4. TABLEAU DE DÉCISION : Fais un tableau Markdown avec les colonnes 
                           | Produit | Décision | Action Supply | Impact Marge |
                        5. Décisions sur les volumes.
                        6. Actions face à l'événement simulé.
                        7. Rentabilité finale.
                        8. CONCLUSION : Donne ton feu vert ou tes réserves sur le plan.""",
                        agent=SOP.orchestrator, 
                        expected_output="Plan S&OP Final structuré en 5 points avec tableau."
            )
            crew = Crew(agents=[SOP.marketing, SOP.sales, SOP.supply, SOP.purchasing, SOP.finance, SOP.orchestrator], tasks=[t1,t2,t3,t4,t5,t6],
                       memory=False, 
                       cache=False,  
                       verbose=True)
            crew.kickoff()

            st.session_state['outputs'] = {
                "📢 Marketing": t1.output.raw, "🤝 Ventes": t2.output.raw, "🏗️ Supply": t3.output.raw,
                "📦 Achats": t4.output.raw, "💰 Finance": t5.output.raw, "🏆 Rapport Final": t6.output.raw
            }
            st.session_state['run_done'] = True
        finally: sys.stdout = sys.__stdout__

    # --- CONSULTATION DES RAPPORTS ---
    if st.session_state.get('run_done'):
        st.markdown("---")
        choix = st.multiselect("Afficher les rapports :", options=list(st.session_state['outputs'].keys()), default=["🏆 Rapport Final"])
        for r in choix:
            with st.expander(f"Consulter {r}", expanded=True):
                st.markdown(st.session_state['outputs'][r])
else:
    st.info("👋 Veuillez charger le fichier Excel.")
