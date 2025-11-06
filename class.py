import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Analyse Matchs Prédictive", layout="wide")
st.title("⚽ Analyse Prédictive des Matchs")
st.caption("Entrez vos matchs, cotes et statistiques pour obtenir les matchs les plus sûrs avec probabilités de victoire")

# ---------------------------
# Initialisation
# ---------------------------
if "matches_df" not in st.session_state:
    columns = ["home_team","away_team","cote_home","cote_away",
               "home_wins","home_draws","home_losses","home_goals_scored","home_goals_against",
               "away_wins","away_draws","away_losses","away_goals_scored","away_goals_against"]
    st.session_state.matches_df = pd.DataFrame(columns=columns)

# ---------------------------
# Saisie via tableau interactif
# ---------------------------
st.header("Entrer vos matchs")
st.info("Remplissez le tableau avec tous vos matchs. Vous pouvez ajuster les cotes pour simuler différents scénarios.")
edited_df = st.experimental_data_editor(st.session_state.matches_df, num_rows="dynamic")
st.session_state.matches_df = edited_df

# ---------------------------
# Calcul des scores et probabilités
# ---------------------------
def calculate_score_and_prob(df):
    df = df.copy()
    df["diff_cote"] = abs(df["cote_home"] - df["cote_away"])
    df["home_form"] = df["home_wins"]*3 + df["home_draws"] - df["home_losses"]
    df["away_form"] = df["away_wins"]*3 + df["away_draws"] - df["away_losses"]
    df["goal_diff"] = (df["home_goals_scored"] - df["home_goals_against"]) - (df["away_goals_scored"] - df["away_goals_against"])
    
    # Score combiné pondéré
    df["score_securite"] = (1 - df["diff_cote"]/10)*50 + ((df["home_form"] - df["away_form"])/20)*30 + ((df["goal_diff"]+10)/20)*20
    
    # Probabilités de victoire
    df["prob_home"] = np.exp(df["score_securite"])/ (np.exp(df["score_securite"]) + np.exp(100 - df["score_securite"]))
    df["prob_away"] = 1 - df["prob_home"]
    
    # Vainqueur probable
    df["Winner"] = np.where(df["prob_home"] > df["prob_away"], df["home_team"], df["away_team"])
    
    return df

# ---------------------------
# Analyse
# ---------------------------
if st.button("Analyser 🧠"):
    if st.session_state.matches_df.empty:
        st.warning("Veuillez entrer au moins un match pour l'analyse")
    else:
        df_analysis = calculate_score_and_prob(st.session_state.matches_df)
        st.session_state.df_analysis = df_analysis

        # Résultats complets
        st.header("Résultats des matchs")
        st.dataframe(
            df_analysis.sort_values(by="score_securite", ascending=False)
        )

        # Top 3–4 matchs les plus sûrs
        st.subheader("🏆 Top 3–4 Matchs les plus sûrs")
        top = df_analysis.sort_values(by="score_securite", ascending=False).head(4)
        st.dataframe(
            top[["home_team","away_team","Winner","score_securite","prob_home","prob_away"]]
        )

        # Graphique probabilités
        st.subheader("Graphique des probabilités de victoire")
        chart = alt.Chart(df_analysis).transform_fold(
            ["prob_home","prob_away"],
            as_=["Équipe","Probabilité"]
        ).mark_bar().encode(
            x=alt.X("Probabilité:Q"),
            y=alt.Y("home_team:N", sort="-x"),
            color=alt.Color("Équipe:N")
        )
        st.altair_chart(chart, use_container_width=True)

        # Graphique Score sécurité vs Winner
        st.subheader("Score de sécurité vs Vainqueur probable")
        chart2 = alt.Chart(df_analysis).mark_bar().encode(
            x=alt.X("score_securite:Q", title="Score de sécurité"),
            y=alt.Y("home_team:N", sort="-x"),
            color=alt.Color("Winner:N", title="Vainqueur probable")
        )
        st.altair_chart(chart2, use_container_width=True)

        # Télécharger CSV
        st.download_button(
            "📥 Télécharger les résultats CSV",
            df_analysis.to_csv(index=False).encode("utf-8"),
            "matchs_prédictifs.csv",
            "text/csv"
        )
