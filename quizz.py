import streamlit as st
import pandas as pd
import plotly.graph_objects as go


@st.cache_data
def load_questions():
    df = pd.read_csv("questions.csv", sep=";", quotechar='"', on_bad_lines="skip")
    df.columns = ["category", "topic", "question", "1", "2", "3", "4", "5"]
    df = df.dropna(subset=["question"])
    for col in ["1", "2", "3", "4", "5"]:
        df[col] = df[col].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    return df.reset_index(drop=True)[:3]


@st.cache_data
def load_benchmark():
    df = pd.read_csv("benchmark.csv", sep=";", quotechar='"', on_bad_lines="skip")
    for col in df.columns[1:]:
        df[col] = df[col].str.rstrip("%").astype(float)
    return df


def load_sectors():
    df = pd.read_csv("benchmark.csv", sep=";", quotechar='"', on_bad_lines="skip")
    sectors = list(df.columns)[1:]
    sectors.append("Other")
    return sectors


def main():
    st.title("Marketing Maturity Benchmark")

    df = load_questions()
    sectors = load_sectors()
    total = len(df)

    # Initialisation
    if "sector" not in st.session_state:
        st.session_state.sector = None
    if "company" not in st.session_state:
        st.session_state.company = None
    if "current" not in st.session_state:
        st.session_state.current = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    # Étape 1 — choix du secteur
    if st.session_state.sector is None:
        st.subheader("Company information")
        company = st.text_input("Company name")
        sector = st.selectbox("Sector", sectors)
        custom_sector = None
        if sector == "Other":
            custom_sector = st.text_input("Please specify your sector")
        if st.button("Start", disabled=not company or (sector == "Other" and not custom_sector)):
            st.session_state.company = company
            st.session_state.sector = custom_sector if sector == "Other" else sector
            st.session_state.is_other = sector == "Other"
            st.rerun()
        return

    # Étape 2 — questions une par une
    i = st.session_state.current
    if i < total:
        row = df.iloc[i]
        st.caption(f"Question {i + 1} / {total}  —  {row['category']}")
        st.subheader(row["question"])

        options = [f"{s} — {row[str(s)]}" for s in range(1, 6) if row[str(s)]]
        chosen = st.radio("Select your answer", options, index=None, key=f"q_{i}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Back"):
                if i == 0:
                    st.session_state.sector = None
                else:
                    st.session_state.current -= 1
                st.rerun()
        with col2:
            if st.button("Next" if i < total - 1 else "Submit", disabled=chosen is None):
                st.session_state.answers[i] = int(chosen[0])
                st.session_state.current += 1
                st.rerun()
        return

    # Étape 3 — résultats
    sector = st.session_state.sector
    st.subheader("Results")
    st.write(f"Sector: **{sector}**")

    # Calcul des scores utilisateur par topic et par catégorie
    topic_scores = {}
    cat_scores = {}
    for i, row in df.iterrows():
        score_pct = st.session_state.answers[i] / 5 * 100
        topic_scores[row["topic"]] = score_pct
        cat_scores.setdefault(row["category"], []).append(score_pct)

    user_cat_means = {cat: round(sum(v) / len(v)) for cat, v in cat_scores.items()}

    if sector != "Other":
        bench = load_benchmark()
        bench_topic = dict(zip(bench["Topic"], bench[sector]))
        topic_to_cat = dict(zip(df["topic"], df["category"]))

        # Moyenne benchmark par catégorie (uniquement pour les topics répondus)
        bench_cat = {}
        for topic in topic_scores:
            cat = topic_to_cat[topic]
            bench_cat.setdefault(cat, []).append(bench_topic.get(topic, 0))
        bench_cat_means = {cat: round(sum(v) / len(v)) for cat, v in bench_cat.items()}

        # Tableau comparatif
        result_df = pd.DataFrame({
            "Your Score": {cat: f"{v}%" for cat, v in user_cat_means.items()},
            f"{sector} Benchmark": {cat: f"{bench_cat_means.get(cat, 'N/A')}%" for cat in user_cat_means},
        })
        st.table(result_df)

        # Radar chart par topic
        topics = list(topic_scores.keys())
        user_vals = [topic_scores[t] for t in topics]
        bench_vals = [bench_topic.get(t, 0) for t in topics]

        # Fermeture du radar
        topics_c = topics + [topics[0]]
        user_c = user_vals + [user_vals[0]]
        bench_c = bench_vals + [bench_vals[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=user_c, theta=topics_c, name="Your Score", fill="toself"))
        fig.add_trace(go.Scatterpolar(r=bench_c, theta=topics_c, name=sector, fill="toself"))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=True)
        st.plotly_chart(fig)

    else:
        result_df = pd.DataFrame({
            "Your Score": {cat: f"{v}%" for cat, v in user_cat_means.items()},
        })
        st.table(result_df)

    if st.button("Start over"):
        st.session_state.sector = None
        st.session_state.current = 0
        st.session_state.answers = {}
        st.rerun()


if __name__ == "__main__":
    main()
