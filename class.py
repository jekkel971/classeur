import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Analyse Matchs & Mise - Forme Récente", layout="wide")
st.title("⚽ Analyse Matchs avec Forme Récente et Analyse Textuelle")

# ---------------------------
# Initialisation
# ---------------------------
if "matches_df" not in st.session_state:
    columns = [
        "home_team","away_team","cote_home","cote_away",
        "home_wins","home_draws","home_losses","home_goals_scored","home_goals_against",
        "away_wins","away_draws","away_losses","away_goals_scored","away_goals_against",
        "home_last5_wins","home_last5_draws","home_last5_losses",
        "away_last5_wins","away_last5_draws","away_last5_losses"
    ]
    st.session_state.matches_df = pd.DataFrame(columns=columns)

# ---------------------------
# Formulaire d’entrée
# ---------------------------
st.header("Ajouter un match")
with st.form("match_form", clear_on_submit=True):
    st.subheader("Équipes et Cotes")
    home_team = st.text_input("Équipe Domicile")
    away_team = st.text_input("Équipe Extérieur")
    cote_home = st.number_input("Cote Domicile", 1.01, 10.0, 1.5)
    cote_away = st.number_input("Cote Extérieur", 1.01, 10.0, 1.5)

    st.subheader("Historique global Domicile")
    home_wins = st.number_input("Victoires domicile", 0, 50, 0)
    home_draws = st.number_input("Nuls domicile", 0, 50, 0)
    home_losses = st.number_input("Défaites domicile", 0, 50, 0)
    home_goals_scored = st.number_input("Buts marqués domicile", 0, 200, 0)
    home_goals_against = st.number_input("Buts encaissés domicile", 0, 200, 0)

    st.subheader("Forme récente (5 derniers matchs) Domicile")
    home_last5_wins = st.number_input("Victoires (5 derniers)", 0, 5, 0)
    home_last5_draws = st.number_input("Nuls (5 derniers)", 0, 5, 0)
    home_last5_losses = st.number_input("Défaites (5 derniers)", 0, 5, 0)

    st.subheader("Historique global Extérieur")
    away_wins = st.number_input("Victoires extérieur", 0, 50, 0)
    away_draws = st.number_input("Nuls extérieur", 0, 50, 0)
    away_losses = st.number_input("Défaites extérieur", 0, 50, 0)
    away_goals_scored = st.number_input("Buts marqués extérieur", 0, 200, 0)
    away_goals_against = st.number_input("Buts encaissés extérieur", 0, 200, 0)

    st.subheader("Forme récente (5 derniers matchs) Extérieur")
    away_last5_wins = st.number_input("Victoires (5 derniers)", 0, 5, 0)
    away_last5_draws = st.number_input("Nuls (5 derniers)", 0, 5, 0)
    away_last5_losses = st.number_input("Défaites (5 derniers)", 0, 5, 0)

    submitted = st.form_submit_button("Ajouter le match")
    if submitted:
        new_row = pd.DataFrame([{
            "home_team": home_team, "away_team": away_team,
            "cote_home": cote_home, "cote_away": cote_away,
            "home_wins": home_wins, "home_draws": home_draws, "home_losses": home_losses,
            "home_goals_scored": home_goals_scored, "home_goals_against": home_goals_against,
            "away_wins": away_wins, "away_draws": away_draws, "away_losses": away_losses,
            "away_goals_scored": away_goals_scored, "away_goals_against": away_goals_against,
            "home_last5_wins": home_last5_wins, "home_last5_draws": home_last5_draws, "home_last5_losses": home_last5_losses,
            "away_last5_wins": away_last5_wins, "away_last5_draws": away_last5_draws, "away_last5_losses": away_last5_losses
        }])
        st.session_state.matches_df = pd.concat([st.session_state.matches_df, new_row], ignore_index=True)
        st.success(f"Match {home_team} vs {away_team} ajouté !")

# ---------------------------
# Fonctions d’analyse
# ---------------------------
def calculate_score_and_prob(df):
    df = df.copy().fillna(0)
    
    df["diff_cote"] = abs(df["cote_home"] - df["cote_away"])
    df["home_form"] = df["home_wins"]*3 + df["home_draws"] - df["home_losses"]
    df["away_form"] = df["away_wins"]*3 + df["away_draws"] - df["away_losses"]
    df["goal_diff"] = (df["home_goals_scored"] - df["home_goals_against"]) - (df["away_goals_scored"] - df["away_goals_against"])

    df["home_recent_form"] = (df["home_last5_wins"]*3 + df["home_last5_draws"]) / 15
    df["away_recent_form"] = (df["away_last5_wins"]*3 + df["away_last5_draws"]) / 15

    df["score_securite"] = (
        (1 - df["diff_cote"]/10)*40 +
        ((df["home_form"] - df["away_form"])/20)*25 +
        ((df["goal_diff"]+10)/20)*15 +
        ((df["home_recent_form"] - df["away_recent_form"])*100)*20
    ).clip(0, 100)

    df["prob_home"] = np.exp(df["score_securite"]) / (np.exp(df["score_securite"]) + np.exp(100 - df["score_securite"]))
    df["prob_away"] = 1 - df["prob_home"]
    df["Winner"] = np.where(df["prob_home"] > df["prob_away"], df["home_team"], df["away_team"])
    
    # 🧩 Analyse textuelle de la forme récente
    def analyse_forme(equipe, wins, draws, losses):
        total = wins + draws + losses
        if total == 0:
            return f"{equipe} n’a pas encore joué récemment."
        ratio_victoire = wins / total
        if ratio_victoire >= 0.8:
            return f"{equipe} est en très grande forme ({wins}V sur les {total} derniers matchs) 🔥"
        elif ratio_victoire >= 0.6:
            return f"{equipe} est en bonne forme ({wins}V sur les {total} derniers matchs)."
        elif ratio_victoire >= 0.4:
            return f"{equipe} est en forme moyenne ({wins}V sur les {total} derniers matchs)."
        else:
            return f"{equipe} est en difficulté ({wins}V sur les {total} derniers matchs)."

    df["analyse_home"] = df.apply(lambda r: analyse_forme(r["home_team"], r["home_last5_wins"], r["home_last5_draws"], r["home_last5_losses"]), axis=1)
    df["analyse_away"] = df.apply(lambda r: analyse_forme(r["away_team"], r["away_last5_wins"], r["away_last5_draws"], r["away_last5_losses"]), axis=1)
    return df

# ---------------------------
# Analyse et affichage
# ---------------------------
if st.button("Analyser 🧠"):
    if st.session_state.matches_df.empty:
        st.warning("Veuillez ajouter au moins un match.")
    else:
        df_analysis = calculate_score_and_prob(st.session_state.matches_df)

        st.subheader("🏆 Analyse complète des matchs")
        st.dataframe(df_analysis[["home_team","away_team","Winner","score_securite","prob_home","prob_away"]]
                     .sort_values(by="score_securite", ascending=False))

        st.subheader("🧩 Analyse textuelle de la forme des équipes")
        for _, row in df_analysis.iterrows():
            st.markdown(f"**{row['home_team']} vs {row['away_team']}**")
            st.write(f"🏠 {row['analyse_home']}")
            st.write(f"🚗 {row['analyse_away']}")
            st.write(f"👉 **Vainqueur probable : {row['Winner']}** (sécurité : {row['score_securite']:.1f}%)")
            st.markdown("---")

        st.subheader("Graphique de la sécurité")
        chart = alt.Chart(df_analysis).mark_bar().encode(
            x="score_securite:Q",
            y="home_team:N",
            color="Winner:N"
        )
        st.altair_chart(chart, use_container_width=True)
