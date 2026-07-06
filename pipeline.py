"""
Logica di calcolo estratta dal notebook Modelli.ipynb.

Contiene tutte le funzioni necessarie per:
1. Calcolare i costi di manutenzione Correttiva, Preventiva e Predittiva
   su una griglia di scenari.
2. Determinare la strategia ottimale per ciascuno scenario.
3. Addestrare un albero decisionale per ognuna delle 27 combinazioni
   Predictability x Severity x Occurrence (FMEA).

Questo modulo viene importato sia dall'app Streamlit (app.py) sia,
volendo, da uno script offline per rigenerare grafici/estrazioni Excel.
"""

import itertools

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from sklearn.tree import DecisionTreeClassifier

# --------------------------------------------------------------------------
# 1. PARAMETRI DI BASE (identici al notebook)
# --------------------------------------------------------------------------

Cf_list = [10000, 20000, 50000]
MTTF_list = [0.5, 1, 2]
beta_list = [1.5, 2, 2.5, 3, 3.5]
CSystPdM_list = [1000, 2000, 4000, 5000, 10000, 25000]
alfa_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
Cinter_list = [1000, 2000, 4000, 5000, 10000]
AN_list = [1 - (1 / 880), 1 - (1 / 1760), 1 - (1 / 3520)]
fsc_list = [1]
Nh_list = [1760]
r_list = [0.99]

detectability_scenarios = [
    {"detectability": "low", "H": 0.65, "F": 0.30},
    {"detectability": "medium", "H": 0.85, "F": 0.10},
    {"detectability": "high", "H": 0.95, "F": 0.05},
]

FEATURES = ["Cinter", "CSystPdM", "Beta", "Alfa"]
TARGET = "Strategia_Ottimale"

SCENARI_PREDICTABILITY = {
    "HIGH": {"H": 0.95, "F": 0.05},
    "MEDIUM": {"H": 0.85, "F": 0.10},
    "LOW": {"H": 0.65, "F": 0.30},
}
SCENARI_SEVERITY = {"HIGH": 50000, "MEDIUM": 20000, "LOW": 10000}
SCENARI_OCCURRENCE = {"HIGH": 0.5, "MEDIUM": 1.0, "LOW": 2.0}


# --------------------------------------------------------------------------
# 2. MANUTENZIONE A GUASTO (CORRECTIVE)
# --------------------------------------------------------------------------

def calcola_df_guasto():
    combinazioni_essenziali = list(itertools.product(MTTF_list, Cf_list))
    risultati_guasto = []
    for mttf, cf in combinazioni_essenziali:
        costo_guasto = cf / mttf
        risultati_guasto.append(
            {"MTTF": mttf, "Cf": cf, "Costo_CORRECTIVE": round(costo_guasto, 4)}
        )
    return pd.DataFrame(risultati_guasto)


# --------------------------------------------------------------------------
# 3. MANUTENZIONE PREVENTIVA
# --------------------------------------------------------------------------

def calcola_df_preventiva(weibull_csv_path):
    df_raw = pd.read_csv(weibull_csv_path, header=None, index_col=0)
    beta_riferimento = df_raw.loc["beta"].values.astype(float)
    rapporto_riferimento = df_raw.loc["MTTF/theta"].values.astype(float)

    def get_theta(beta_val, mttf_val):
        rapporto = np.interp(beta_val, beta_riferimento, rapporto_riferimento)
        return mttf_val / rapporto

    def costo_obiettivo(tp_val, b, th, cf, cint, csys, alfa, dettagli=False):
        if tp_val <= 0:
            return np.inf
        rtp = np.exp(-((tp_val / th) ** b))
        area, _ = quad(lambda s: np.exp(-((s / th) ** b)), 0, tp_val)
        if area == 0:
            return np.inf
        c_failure = (cf * (1 - rtp)) / area
        c_preventivo = (cint * rtp) / area
        c_monitoraggio = alfa * csys
        costo_totale = c_failure + c_preventivo + c_monitoraggio
        if dettagli:
            return costo_totale, c_failure, c_preventivo, c_monitoraggio
        return costo_totale

    risultati_totali = []
    combinazioni = list(
        itertools.product(beta_list, MTTF_list, Cf_list, Cinter_list, CSystPdM_list, alfa_list)
    )

    for b, mttf, cf, cint, csys, alfa in combinazioni:
        th = get_theta(b, mttf)
        res = minimize_scalar(
            costo_obiettivo,
            bounds=(1, mttf * 5),
            args=(b, th, cf, cint, csys, alfa, False),
            method="bounded",
        )
        tot, fail, prev, mon = costo_obiettivo(res.x, b, th, cf, cint, csys, alfa, dettagli=True)
        risultati_totali.append(
            {
                "Beta": b,
                "MTTF": mttf,
                "Cf": cf,
                "Cinter": cint,
                "CSystPdM": csys,
                "Alfa": alfa,
                "Theta": th,
                "tp_Ottimo": round(res.x, 2),
                "Costo_Failure_prev": round(fail, 4),
                "Costo_Prevenzione_prev": round(prev, 4),
                "Costo_Monitoraggio_prev": round(mon, 4),
                "Costo_PREVENTIVE_Totale": round(res.fun, 4),
            }
        )

    return pd.DataFrame(risultati_totali)


# --------------------------------------------------------------------------
# 4. MANUTENZIONE PREDITTIVA
# --------------------------------------------------------------------------

def calcola_df_predittiva():
    combinazioni_pdm_base = list(
        itertools.product(Cf_list, Cinter_list, CSystPdM_list, MTTF_list, AN_list, fsc_list, Nh_list, r_list)
    )

    risultati_predittiva = []
    for cf, cint, csys, mttf, an, fsc, nh, r in combinazioni_pdm_base:
        for det in detectability_scenarios:
            h = det["H"]
            f = det["F"]

            t1 = csys
            t2 = cint * f * an * fsc * nh * (1 - r)
            t3 = (cint * h) / mttf
            t4 = (cf * (1 - h)) / mttf

            costo_totale_pred = t1 + t2 + t3 + t4

            risultati_predittiva.append(
                {
                    "Cf": cf,
                    "Cinter": cint,
                    "CSystPdM": csys,
                    "MTTF": mttf,
                    "F": f,
                    "H": h,
                    "AN": an,
                    "fsc": fsc,
                    "Nh": nh,
                    "r": r,
                    "Costo_falsi_positivi": t1,
                    "Costo_falsi_negativi": t4,
                    "Costo_veri_positivi": t3,
                    "Costo_PREDICTIVE_Totale": round(costo_totale_pred, 4),
                }
            )

    return pd.DataFrame(risultati_predittiva)


# --------------------------------------------------------------------------
# 5. CONFRONTO GLOBALE
# --------------------------------------------------------------------------

def calcola_df_confronto_globale(df_guasto, df_preventiva, df_predittiva):
    df_confronto = pd.merge(
        df_predittiva, df_preventiva, on=["Cf", "Cinter", "CSystPdM", "MTTF"], how="inner"
    )
    df_confronto = pd.merge(df_confronto, df_guasto, on=["Cf", "MTTF"], how="inner")

    colonne_costi = ["Costo_CORRECTIVE", "Costo_PREVENTIVE_Totale", "Costo_PREDICTIVE_Totale"]
    df_confronto["Strategia_Ottimale"] = df_confronto[colonne_costi].idxmin(axis=1)
    df_confronto["Strategia_Ottimale"] = (
        df_confronto["Strategia_Ottimale"].str.replace("Costo_", "").str.replace("_Totale", "")
    )
    return df_confronto


# --------------------------------------------------------------------------
# 6. ADDESTRAMENTO DEI 27 ALBERI DECISIONALI
# --------------------------------------------------------------------------

def addestra_modelli(df_confronto_globale):
    models = {}
    accuracies = {}

    for name_p, p_val in SCENARI_PREDICTABILITY.items():
        for name_s, s_val in SCENARI_SEVERITY.items():
            for name_o, o_val in SCENARI_OCCURRENCE.items():
                df_scenario = df_confronto_globale[
                    (df_confronto_globale["H"] == p_val["H"])
                    & (df_confronto_globale["F"] == p_val["F"])
                    & (df_confronto_globale["Cf"] == s_val)
                    & (df_confronto_globale["MTTF"] == o_val)
                ].copy()

                if df_scenario.empty:
                    continue

                X = df_scenario[FEATURES]
                y = df_scenario[TARGET]

                clf = DecisionTreeClassifier(max_depth=3, random_state=42)
                clf.fit(X, y)
                models[(name_p, name_s, name_o)] = clf
                accuracies[(name_p, name_s, name_o)] = clf.score(X, y)

    return models, accuracies


# --------------------------------------------------------------------------
# 7. FUNZIONE DI QUERY (usata dall'app)
# --------------------------------------------------------------------------

def query_tree(models, p, s, o, cinter, csystpdm, beta, alfa):
    key = (p, s, o)
    if key not in models:
        return {"error": "Scenario non trovato"}

    clf = models[key]
    X_new = pd.DataFrame(
        [{"Cinter": cinter, "CSystPdM": csystpdm, "Beta": beta, "Alfa": alfa}]
    )
    pred = clf.predict(X_new)[0]
    proba = dict(zip(clf.classes_, clf.predict_proba(X_new)[0]))

    return {"scenario": key, "strategy": pred, "proba": proba}


# --------------------------------------------------------------------------
# 8. PIPELINE COMPLETA (usata con caching in app.py)
# --------------------------------------------------------------------------

def build_all(weibull_csv_path):
    df_guasto = calcola_df_guasto()
    df_preventiva = calcola_df_preventiva(weibull_csv_path)
    df_predittiva = calcola_df_predittiva()
    df_confronto = calcola_df_confronto_globale(df_guasto, df_preventiva, df_predittiva)
    models, accuracies = addestra_modelli(df_confronto)
    return {
        "df_guasto": df_guasto,
        "df_preventiva": df_preventiva,
        "df_predittiva": df_predittiva,
        "df_confronto": df_confronto,
        "models": models,
        "accuracies": accuracies,
    }
