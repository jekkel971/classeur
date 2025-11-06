import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Analyse Matchs & Mise", layout="wide")
st.title("⚽ Analyse Matchs et Calcul de Mise")
st.caption("Ajoute tes matchs, analyse leur sécurité et calcule la mise optimale selon ton budget")

# ---------------------------
# Initialisation session_state
# ---------------------------
if "matches_df" not in st.session_state:
    columns = ["home_team","away_team","cote_home","cote_away",
               "home_wins","home_draws","home_losses","home_goals_scored","home_goals_against",
               "away_wins","away_draws","away_losses","away_goals_scored","away_goals_against"]
    st.session_state.matches_df = pd.DataFrame(columns=columns)

# ---------------------------
# Formulaire pour ajouter un match
# ---------------------------
st.header("Ajouter un match")
with st.form("match_form", clear_on_submit=True):
    st.subheader("Équipes et Cotes")
    home_team = st.text_input("Équipe Domicile")
    away_team = st.text_input("Équipe Extérieur")
    cote_home = st.number_input("Cote Domicile", 1.01, 10.0, 1.5, key="cote_home")
    cote_away = st.number_input("Cote Extérieur", 1.01, 10.0, 1.5, key="cote_away")

    st.subheader("Historique Domicile")
    home_wins = st.number_input("Victoires domicile", 0, 50, 0, key="home_wins")
    home_draws = st.number_input("Nuls domicile", 0, 50, 0, key="home_draws")
    home_losses = st.number_input("Défaites domicile", 0, 50, 0, key="home_losses")
    home_goals_scored = st.number_input("Buts marqués domicile", 0, 200, 0, key="home_goals_scored")
    home_goals_against = st.number_input("Buts encaissés domicile", 0, 200, 0, key="home_goals_against")

    st.subheader("Historique Extérieur")
    away_wins = st.number_input("Victoires extérieur", 0, 50, 0, key="away_wins")
    away_draws = st.number_input("Nuls extérieur", 0, 50, 0, key="away_draws")
    away_losses = st.number_input("Défaites extérieur", 0, 50, 0, key="away_losses")
    away_goals_scored = st.number_input("Buts marqués extérieur", 0, 200, 0, key="away_goals_scored")
    away_goals_against = st.number_input("Buts encaissés extérieur", 0, 200, 0, key="away_goals_against")

    submitted = st.form_submit_button("Ajouter le match")
    if submitted:
        new_row = pd.DataFrame([{
            "home_team": home_team,
            "away_team": away_team,
            "cote_home": cote_home,
            "cote_away": cote_away,
            "home_wins": home_wins,
            "home_draws": home_draws,
            "home_losses": home_losses,
            "home_goals_scored": home_goals_scored,
            "home_goals_against": home_goals_against,
            "away_wins": away_wins,
            "away_draws": away_draws,
            "away_losses": away_losses,
            "away_goals_scored": away_goals_scored,
            "away_goals_against": away_goals_against
        }])
        st.session_state.matches_df = pd.concat([st.session_state.matches_df, new_row], ignore_index=True)
        st.success(f"Match {home_team} vs {away_team} ajouté !")

# ---------------------------
# Fonction analyse stable
# ---------------------------
def calculate_score_and_prob(df):
    df = df.copy()
    numeric_cols = ["cote_home","cote_away","home_wins","home_draws","home_losses",
                    "home_goals_scored","home_goals_against","away_wins","away_draws","away_losses",
                    "away_goals_scored","away_goals_against"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["diff_cote"] = abs(df["cote_home"] - df["cote_away"])
    df["home_form"] = df["home_wins"]*3 + df["home_draws"] - df["home_losses"]
    df["away_form"] = df["away_wins"]*3 + df["away_draws"] - df["away_losses"]
    df["goal_diff"] = (df["home_goals_scored"] - df["home_goals_against"]) - (df["away_goals_scored"] - df["away_goals_against"])

    df["score_securite"] = (1 - df["diff_cote"]/10)*50 + ((df["home_form"] - df["away_form"])/20)*30 + ((df["goal_diff"]+10)/20)*20
    df["score_securite"] = pd.to_numeric(df["score_securite"], errors="coerce").fillna(0)

    df["prob_home"] = np.exp(df["score_securite"]) / (np.exp(df["score_securite"]) + np.exp(100 - df["score_securite"]))
    df["prob_away"] = 1 - df["prob_home"]
    df["Winner"] = np.where(df["prob_home"] > df["prob_away"], df["home_team"], df["away_team"])
    return df

# ---------------------------
# Bouton Analyse
# ---------------------------
if st.button("Analyser 🧠"):
    if st.session_state.matches_df.empty:
        st.warning("Veuillez ajouter au moins un match")
    else:
        df_analysis = calculate_score_and_prob(st.session_state.matches_df)
        st.session_state.df_analysis = df_analysis

        st.header("Résultats des matchs")
        st.dataframe(df_analysis.sort_values(by="score_securite", ascending=False))

        st.subheader("🏆 Top 3–4 Matchs les plus sûrs")
        top = df_analysis.sort_values(by="score_securite", ascending=False).head(4)
        st.dataframe(top[["home_team","away_team","Winner","score_securite","prob_home","prob_away"]])

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

        st.subheader("Score de sécurité vs Vainqueur probable")
        chart2 = alt.Chart(df_analysis).mark_bar().encode(
            x=alt.X("score_securite:Q", title="Score de sécurité"),
            y=alt.Y("home_team:N", sort="-x"),
            color=alt.Color("Winner:N", title="Vainqueur probable")
        )
        st.altair_chart(chart2, use_container_width=True)

        st.download_button(
            "📥 Télécharger les résultats CSV",
            df_analysis.to_csv(index=False).encode("utf-8"),
            "matchs_prédictifs.csv",
            "text/csv"
        )

        # ---------------------------
        # Calcul de mise selon Kelly Criterion simplifié
        # ---------------------------
        st.subheader("💰 Recommandation de mise")
        budget_total = st.number_input("Budget total (€)", 1, 10000, 100, step=10)

        df = df_analysis.copy()
        # Calcul b, probabilité du vainqueur
        df["b"] = df.apply(lambda row: row["cote_home"]-1 if row["Winner"]==row["home_team"] else row["cote_away"]-1, axis=1)
        df["p"] = df.apply(lambda row: row["prob_home"] if row["Winner"]==row["home_team"] else row["prob_away"], axis=1)
        df["q"] = 1 - df["p"]
        df["f_star"] = ((df["b"] * df["p"] - df["q"]) / df["b"]).clip(lower=0)  # fraction optimale
        df["Mise (€)"] = (df["f_star"] * budget_total).round(2)

        st.dataframe(df[["home_team","away_team","Winner","p","b","Mise (€)"]])
