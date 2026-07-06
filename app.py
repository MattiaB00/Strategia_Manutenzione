import streamlit as st

import pipeline

st.set_page_config(
    page_title="Strategia di Manutenzione Ottimale",
    page_icon="🛠️",
    layout="centered",
)

st.title("🛠️ Strategia di Manutenzione Ottimale")
st.write(
    "Questo strumento suggerisce, in base ai parametri del componente/impianto, "
    "quale strategia di manutenzione è più conveniente tra **Correttiva**, "
    "**Preventiva** e **Predittiva**, usando un modello ad albero decisionale "
    "addestrato su un'analisi FMEA e sui costi di ciascuna politica."
)


@st.cache_resource(show_spinner="Calcolo dei costi e addestramento dei modelli (una tantum)...")
def carica_modelli():
    return pipeline.build_all("tabella_weibull.csv")


dati = carica_modelli()
models = dati["models"]

st.divider()
st.subheader("1. Scenario FMEA")

col1, col2, col3 = st.columns(3)
with col1:
    predictability = st.selectbox(
        "Predictability (rilevabilità)",
        options=["HIGH", "MEDIUM", "LOW"],
        help="Quanto è facile rilevare in anticipo un guasto imminente.",
    )
with col2:
    severity = st.selectbox(
        "Severity (gravità del guasto)",
        options=["HIGH", "MEDIUM", "LOW"],
        help="Impatto/costo del guasto se si verifica (mappato su Cf).",
    )
with col3:
    occurrence = st.selectbox(
        "Occurrence (frequenza del guasto)",
        options=["HIGH", "MEDIUM", "LOW"],
        help="Frequenza attesa del guasto (mappata su MTTF: HIGH = guasti frequenti).",
    )

st.subheader("2. Parametri economici e affidabilistici")

c1, c2 = st.columns(2)
with c1:
    cinter = st.select_slider(
        "Cinter — costo di un intervento (€)",
        options=pipeline.Cinter_list,
        value=pipeline.Cinter_list[len(pipeline.Cinter_list) // 2],
    )
    beta = st.select_slider(
        "Beta — parametro di forma Weibull",
        options=pipeline.beta_list,
        value=pipeline.beta_list[len(pipeline.beta_list) // 2],
    )
with c2:
    csystpdm = st.select_slider(
        "CSystPdM — costo annuo del sistema di monitoraggio (€/anno)",
        options=pipeline.CSystPdM_list,
        value=pipeline.CSystPdM_list[len(pipeline.CSystPdM_list) // 2],
    )
    alfa = st.select_slider(
        "Alfa — grado di utilizzo del sistema di monitoraggio",
        options=pipeline.alfa_list,
        value=pipeline.alfa_list[len(pipeline.alfa_list) // 2],
    )

st.divider()

if st.button("🔍 Calcola strategia consigliata", type="primary", use_container_width=True):
    risultato = pipeline.query_tree(models, predictability, severity, occurrence, cinter, csystpdm, beta, alfa)

    if "error" in risultato:
        st.error(risultato["error"])
    else:
        colori = {
            "PREDICTIVE": "green",
            "PREVENTIVE": "orange",
            "CORRECTIVE": "red",
        }
        strategia = risultato["strategy"]
        colore = colori.get(strategia, "blue")

        st.markdown(f"### Strategia consigliata: :{colore}[{strategia}]")

        st.write("Probabilità stimata per lo scenario selezionato:")
        proba = risultato["proba"]
        for classe in ["PREDICTIVE", "PREVENTIVE", "CORRECTIVE"]:
            if classe in proba:
                st.progress(float(proba[classe]), text=f"{classe}: {proba[classe]:.0%}")

with st.expander("ℹ️ Come funziona / definizioni"):
    st.markdown(
        """
- **Correttiva**: si interviene solo dopo il guasto.
- **Preventiva**: si sostituisce/interviene a intervalli programmati, calcolati
  ottimizzando il compromesso tra costo del guasto e costo dell'intervento anticipato.
- **Predittiva**: si monitora la condizione del componente e si interviene solo
  quando i dati indicano un rischio imminente.

Per ciascuna delle 27 combinazioni di Predictability × Severity × Occurrence è stato
addestrato un albero decisionale (profondità massima 3) che, dati Cinter, CSystPdM,
Beta e Alfa, predice quale delle tre strategie minimizza il costo totale atteso.
        """
    )
