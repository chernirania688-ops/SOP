import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from crewai import Crew, Task
import SOP
import sys
import re

# --- CLASSE POUR CAPTURER LA DISCUSSION DES AGENTS ---
class StreamlitRedirect:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output = ""
    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        self.output += clean_text
        self.placeholder.code(self.output)
    def flush(self): pass

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="S&OP AI Simulator", layout="wide", page_icon="🏭")

# --- BARRE LATÉRALE ---
st.sidebar.title("⚙️ Configuration")
uploaded_file = st.sidebar.file_uploader("📥 Charger SOP_Data.xlsx", type=['xlsx'])

st.title("🏭 Pilotage Stratégique & Simulateur S&OP Agentic")
st.markdown("---")

if uploaded_file is not None:
    try:
        # 1. LECTURE DES DONNÉES
        xls = pd.ExcelFile(uploaded_file)
        df_mkt = pd.read_excel(xls, 'Demande')
        df_prod = pd.read_excel(xls, 'Production')
        df_fin = pd.read_excel(xls, 'Finance_Achats')
        
        for df in [df_mkt, df_prod, df_fin]:
            df.columns = df.columns.str.strip()

        # INITIALISATION DES VERSIONS SIMULÉES
        df_mkt_sim = df_mkt.copy()
        df_prod_sim = df_prod.copy()
        contexte_simulation = "SITUATION NORMALE"

        # =================================================================
        # 2. SYSTÈME DE FILTRE ET SIMULATION
        # =================================================================
        col_ctrl1, col_ctrl2 = st.columns([1, 2])
        
        with col_ctrl1:
            st.subheader("🔍 Filtre Vue")
            liste_prods = ["Tous les produits"] + list(df_mkt['Produit'].unique())
            selected_prod = st.selectbox("Choisir un produit :", liste_prods)

        with col_ctrl2:
            st.subheader("🎭 Simulateur de Crise")
            type_ev = st.radio("Scénario :", ["🟢 Nominal", "🔴 Aléa Production", "🔵 Pic Demande"], horizontal=True)
            
            if type_ev == "🔴 Aléa Production":
                pct = st.slider("Baisse capacité (%)", 10, 90, 30)
                df_prod_sim['Capacity'] = df_prod['Capacity'] * (1 - pct/100)
                contexte_simulation = f"ALÉA : Capacité réduite de {pct}%."
            elif type_ev == "🔵 Pic Demande":
                pct = st.slider("Hausse demande (%)", 10, 100, 40)
                df_mkt_sim['Forecast'] = df_mkt['Forecast'] * (1 + pct/100)
                contexte_simulation = f"PIC : Demande en hausse de {pct}%."

        # Application du filtre pour l'affichage
        if selected_prod == "Tous les produits":
            v_mkt, v_prod, v_fin = df_mkt_sim, df_prod_sim, df_fin
        else:
            v_mkt = df_mkt_sim[df_mkt_sim['Produit'] == selected_prod]
            v_prod = df_prod_sim[df_prod_sim['Produit'] == selected_prod]
            v_fin = df_fin[df_fin['Produit'] == selected_prod]

        # 3. KPIs ET GRAPHIQUES
        st.markdown("---")
        k1, k2, k3, k4 = st.columns(4)
        dem_tot = v_mkt['Forecast'].sum()
        cap_tot = v_prod['Capacity'].sum()
        sat = (dem_tot / cap_tot * 100) if cap_tot > 0 else 0
        
        k1.metric("Demande", f"{dem_tot:,.0f} u")
        k2.metric("Capacité", f"{cap_tot:,.0f} u")
        k3.metric("Saturation", f"{sat:.1f}%", delta=f"{sat-100:.1f}%", delta_color="inverse")
        k4.metric("Marge Potentielle", f"{(v_mkt['Forecast'] * v_fin['Margin_Unit']).sum():,.0f} €")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=v_prod['Produit'], y=v_prod['Capacity'], name='Capacité', marker_color='#2ecc71', opacity=0.6))
            fig.add_trace(go.Bar(x=v_mkt['Produit'], y=v_mkt['Forecast'], name='Demande', marker_color='#e74c3c', width=0.4))
            fig.update_layout(title="Équilibre Offre/Demande", barmode='overlay', height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col_g2:
            df_p = pd.merge(v_mkt, v_fin, on='Produit')
            fig_tree = px.treemap(df_p, path=['Produit'], values='Forecast', color='Margin_Unit', 
                                  color_continuous_scale='RdYlGn', title="Poids des Produits (Volume vs Marge)")
            st.plotly_chart(fig_tree, use_container_width=True)

        # 4. LANCEMENT IA AVEC ONGLETS
        st.markdown("---")
        if st.button("🚀 Lancer l'Analyse Multi-Agents", use_container_width=True):
            col_log, col_rep = st.columns([1, 2])
            
            with col_log:
                st.info("🧠 Pensée des Agents...")
                log_placeholder = st.empty()
                redir = StreamlitRedirect(log_placeholder)
                old_stdout = sys.stdout
                sys.stdout = redir
                
                try:
                    # Préparation données texte
                    t_mkt = df_mkt_sim.head(20).to_string()
                    t_prd = df_prod_sim.head(20).to_string()
                    t_fin = df_fin.head(20).to_string()

                    tasks = [
                        Task(description=f"Analyse demande: {t_mkt}. Context: {contexte_simulation}", agent=SOP.marketing, expected_output="Rapport Marketing."),
                        Task(description=f"Vérifie prod: {t_prd}", agent=SOP.supply, expected_output="Plan Production."),
                        Task(description=f"Impact financier: {t_fin}", agent=SOP.finance, expected_output="Bilan financier."),
                        Task(description="Arbitre et crée le rapport final.", agent=SOP.orchestrator, expected_output="Plan S&OP Final.")
                    ]
                    
                    crew = Crew(agents=[SOP.marketing, SOP.supply, SOP.finance, SOP.orchestrator], tasks=tasks)
                    result = crew.kickoff()
                    
                    # Sauvegarde pour l'affichage
                    st.session_state['full_res'] = result
                finally:
                    sys.stdout = old_stdout

            with col_rep:
                if 'full_res' in st.session_state:
                    res = st.session_state['full_res']
                    # SYSTÈME D'ONGLETS POUR VOIR CHAQUE AGENT
                    t_final, t_mkt, t_sup, t_fin = st.tabs(["📄 RAPPORT FINAL", "📢 Marketing", "🏭 Supply Chain", "💰 Finance"])
                    
                    with t_final:
                        st.success("### Décision S&OP Consolidée")
                        st.markdown(res.raw)
                    
                    with t_mkt:
                        st.markdown("### Analyse de l'Agent Marketing")
                        st.info(res.tasks_output[0].raw)
                        
                    with t_sup:
                        st.markdown("### Analyse de l'Agent Supply")
                        st.warning(res.tasks_output[1].raw)
                        
                    with t_fin:
                        st.markdown("### Analyse de l'Agent Finance")
                        st.success(res.tasks_output[2].raw)

    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("👋 Chargez le fichier Excel pour commencer.")
