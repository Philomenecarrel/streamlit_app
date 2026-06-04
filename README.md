# Marketing Maturity Benchmark

A Streamlit app that lets companies self-assess their marketing maturity across key dimensions and compare their scores against sector benchmarks.

## What it does

Users answer a guided questionnaire (5-level maturity scale per question) organized across three categories:

- **Global Organization** — Strategy, People & Skills, Data Tools & Storage
- **Customer Centricity** — Customer Activation, Customer Experience (online & offline), Voice of Customer
- **Marketing Performance** — Marketing Measurement, Prices & Promotions, Offer & Network

After completing the quiz, results are displayed as:
- A score matrix (company vs. sector benchmark, color-coded green/red)
- A radar chart overlaying company scores with sector averages
- 3 AI-generated strategic insights powered by Mistral (in `quizz.py`)

Responses are appended to `responses.csv` for later analysis.

## Variants

| File | Description |
|------|-------------|
| `quizz.py` | Full version with Mistral AI insights |
| `quizz_without_llm.py` | Same quiz and charts, no AI call |

## Supported sectors

Food & Beverage, Automotive & Mobility Services, Energy, Luxury Goods, Retail, Tech & Public Sector. Users can also select "Other" to run without a benchmark comparison.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Mistral API key (required for `quizz.py` only)

The app is deployed on Streamlit Cloud, where the key is stored in the app's **Secrets** settings as `MISTRAL_API_KEY`. For local development, add it to a `.env` file:

```
MISTRAL_API_KEY=your_key_here
```

### 3. Run the app

```bash
# With AI insights
streamlit run quizz.py

# Without AI
streamlit run quizz_without_llm.py
```

## Data files

| File | Purpose |
|------|---------|
| `questions.csv` | Quiz questions and 5-level answer options, semicolon-separated |
| `benchmark.csv` | Sector benchmark scores by topic, semicolon-separated |
| `responses.csv` | Auto-generated; stores all submitted responses(only when launched locally TT )) |

## Requirements

- Python 3.9+
- `streamlit`, `pandas`, `plotly`, `mistralai`, `python-dotenv`
