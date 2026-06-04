import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime
from dotenv import load_dotenv
from mistralai import Mistral
import os

load_dotenv()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])

@st.cache_data
def load_questions():
    df = pd.read_csv("questions.csv", sep=";", quotechar='"', on_bad_lines="skip")
    df.columns = ["category", "topic", "question", "1", "2", "3", "4", "5"]
    df = df.dropna(subset=["question"])
    for col in ["1", "2", "3", "4", "5"]:
        df[col] = df[col].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    return df.reset_index(drop=True)


@st.cache_data
def load_benchmark():
    df = pd.read_csv("benchmark.csv", sep=";", quotechar='"', on_bad_lines="skip")
    for col in df.columns[1:]:
        df[col] = df[col].str.rstrip("%").astype(float)
    return df

@st.cache_data
def load_sectors():
    df = pd.read_csv("benchmark.csv", sep=";", quotechar='"', on_bad_lines="skip")
    sectors = list(df.columns)[1:]
    sectors.append("Other")
    return sectors


def plot_matrix(user_cat_means, sector, bench_cat_means=None):
    data = {"Your Score": user_cat_means}
    if bench_cat_means:
        data[f"{sector} Benchmark"] = {cat: bench_cat_means.get(cat, 0) for cat in user_cat_means}
    df = pd.DataFrame(data)

    def color_vs_bench(row):
        if f"{sector} Benchmark" not in row.index:
            return [""] * len(row)
        diff = row["Your Score"] - row[f"{sector} Benchmark"]
        color = "color: #1a7a3f" if diff >= 0 else "color: #a0192a"
        return [color, ""]

    st.dataframe(df.style.apply(color_vs_bench, axis=1).format("{}%"))


def plot_radar_graph(topic_scores, sector, bench_topic=None):
    topics = list(topic_scores.keys())
    user_vals = [topic_scores[t] for t in topics]
    topics_c = topics + [topics[0]]
    user_c = user_vals + [user_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=user_c, theta=topics_c, name="Your Score", fill="toself"))
    if bench_topic:
        bench_vals = [bench_topic.get(t, 0) for t in topics]
        bench_c = bench_vals + [bench_vals[0]]
        fig.add_trace(go.Scatterpolar(r=bench_c, theta=topics_c, name=sector, fill="toself"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), showlegend=True)
    st.plotly_chart(fig)

def save_to_csv(company, sector, is_other, answers, total):
    row = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "company": company,
        "sector": sector,
        "sector_is_other": is_other,
    }
    for i in range(total):
        row[f"answer{i + 1}"] = answers.get(i)

    df_row = pd.DataFrame([row])
    filepath = "responses.csv"

    if os.path.exists(filepath):
        df_row.to_csv(filepath, mode="a", header=False, index=False)
    else:
        df_row.to_csv(filepath, mode="w", header=True, index=False)

@st.cache_data
def build_insight_prompt(topic_scores, bench_topic, sector, topic_to_cat):
    lines = []
    for topic, score in topic_scores.items():
        cat = topic_to_cat.get(topic, "")
        if bench_topic:
            bench = bench_topic.get(topic, None)
            gap = f", gap vs benchmark = {round(score - bench):+}%" if bench is not None else ""
            lines.append(f"- [{cat}] {topic}: {round(score)}%{gap} (benchmark: {round(bench)}%)")
        else:
            lines.append(f"- [{cat}] {topic}: {round(score)}%")

    scores_text = "\n".join(lines)

    benchmark_instruction = (
        f"The scores are compared to the {sector} sector benchmark."
        if bench_topic
        else "No sector benchmark is available."
    )

    return f"""You are a marketing strategy consultant. A company has completed a marketing maturity assessment.

{benchmark_instruction} Here are their scores by topic (grouped by category):

{scores_text}

Write 3 strategic insights for this company. Each insight should focus on a specific topic or a coherent group of topics where one of the following situations stands out:
- a strong gap (positive or negative) between the company and the benchmark
- a notably low score, especially if consistent across topics in the same category
- a notable strength, especially if consistent across topics in the same category

Guidelines:
- Do not structure the insights as a fixed template (no "Strength / Gap / Recommendation" pattern)
- Write each insight as a short natural paragraph (3 sentences max)
- Be specific: name the topics, quote the scores, reference the benchmark when relevant
- Prioritize the most striking or actionable findings
- Use a professional but accessible tone, in English
- Do not be dramatic or use superlatives. Be factual and constructive."""

def main():
    st.title("Marketing Maturity Benchmark")
    st.logo("SIA_Logo_Black.png")
    df = load_questions()
    sectors = load_sectors()
    total = len(df)

    # Initialisation
    if "sector" not in st.session_state:
        st.session_state.sector = None
    if "sector" not in st.session_state:
        st.session_state.sector_other = None
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
            st.session_state.sector =  sector
            st.session_state.sector_other = custom_sector if sector=='Other' else ""
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
                if i == total - 1:
                    save_to_csv(
                        st.session_state.company,
                        st.session_state.sector,
                        st.session_state.sector_other,
                        st.session_state.answers,
                        total,
                    )
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
    topic_to_cat = dict(zip(df["topic"], df["category"]))
    if sector != "Other":
        bench = load_benchmark()
        bench_topic = dict(zip(bench["Topic"], bench[sector]))
        bench_cat = {}
        for topic in topic_scores:
            cat = topic_to_cat[topic]
            bench_cat.setdefault(cat, []).append(bench_topic.get(topic, 0))
        bench_cat_means = {cat: round(sum(v) / len(v)) for cat, v in bench_cat.items()}
        plot_matrix(user_cat_means, sector, bench_cat_means)
        plot_radar_graph(topic_scores, sector, bench_topic)
    else:
        bench_topic = None
        plot_matrix(user_cat_means, sector)
        plot_radar_graph(topic_scores, sector)

    if st.button("Start over"):
        st.session_state.sector = None
        st.session_state.current = 0
        st.session_state.answers = {}
        st.rerun()

    prompt = build_insight_prompt(topic_scores, bench_topic, sector, topic_to_cat)

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    st.markdown(response.choices[0].message.content)


if __name__ == "__main__":
    main()
