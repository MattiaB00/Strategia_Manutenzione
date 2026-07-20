import streamlit as st

import pipeline

st.set_page_config(
    page_title="Optimal Maintenance Strategy",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️ Optimal Maintenance Strategy")
st.write(
    "This tool suggests, based on the FMECA scenario and a few economic/reliability "
    "parameters, which maintenance strategy is more convenient among **Corrective**, "
    "**Preventive** and **Predictive**, using a decision tree trained on the cost "
    "of each policy."
)


@st.cache_resource(show_spinner="Computing costs and training the models (one-time setup)...")
def load_models():
    return pipeline.build_all("tabella_weibull.csv")


data = load_models()
models = data["models"]

st.divider()
st.subheader("1. FMEA scenario")

col1, col2, col3 = st.columns(3)
with col1:
    detectability = st.selectbox(
        "Detectability",
        options=["HIGH", "MEDIUM", "LOW"],
        help="How easily an incoming failure can be detected in advance.",
    )
with col2:
    severity = st.selectbox(
        "Severity",
        options=["HIGH", "MEDIUM", "LOW"],
        help="Impact/cost of the failure if it occurs (mapped onto Cf).",
    )
with col3:
    occurrence = st.selectbox(
        "Occurrence",
        options=["HIGH", "MEDIUM", "LOW"],
        help="Expected failure frequency (mapped onto MTTF: HIGH = frequent failures).",
    )

st.subheader("2. Economic & reliability parameters")
st.caption(
    "These values are free and continuous: the decision tree evaluates them against "
    "its learned split thresholds, it is not limited to the discrete grid used for training."
)

c1, c2 = st.columns(2)
with c1:
    cinter = st.slider(
        "Cinter — cost of a single intervention (€)",
        min_value=500.0,
        max_value=8000.0,
        value=4250.0,
        step=50.0,
    )
    beta = st.slider(
        "Beta — Weibull shape parameter",
        min_value=1.0,
        max_value=5.0,
        value=3,
        step=0.05,
    )
with c2:
    csystpdm = st.slider(
        "CSystPdM — yearly cost of the Predictive system (€/year)",
        min_value=500.0,
        max_value=30000.0,
        value=15200.0,
        step=100.0,
    )
    alfa = st.slider(
        "Alfa — Ratio between the cost of the Preventive system and the cost of the Predictive system",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
    )

st.divider()

if st.button("🔍 Get recommended strategy", type="primary", use_container_width=True):
    result = pipeline.query_tree(models, detectability, severity, occurrence, cinter, csystpdm, beta, alfa)

    if "error" in result:
        st.error(result["error"])
    else:
        colors = {
            "PREDICTIVE": "green",
            "PREVENTIVE": "orange",
            "CORRECTIVE": "red",
        }
        strategy = result["strategy"]
        color = colors.get(strategy, "blue")

        st.markdown(f"### Recommended strategy: :{color}[{strategy}]")

        st.write("Estimated probability for the selected scenario:")
        proba = result["proba"]
        for cls in ["PREDICTIVE", "PREVENTIVE", "CORRECTIVE"]:
            if cls in proba:
                st.progress(float(proba[cls]), text=f"{cls}: {proba[cls]:.0%}")

with st.expander("ℹ️ How it works / definitions"):
    st.markdown(
        """
- **Corrective**: intervene only after the failure occurs.
- **Preventive**: replace/intervene at scheduled intervals, computed by optimizing
  the trade-off between failure cost and early-intervention cost.
- **Predictive**: monitor the component's condition and intervene only when the
  data indicates an imminent risk.

For each of the 27 combinations of Detectability × Severity × Occurrence, a
decision tree (max depth 3) was trained that, given Cinter, CSystPdM, Beta and
Alfa, predicts which of the three strategies minimizes the expected total cost.
Since the tree only checks numeric thresholds, any continuous value for these
four parameters can be evaluated, not just the discrete grid used during training.
        """
    )
