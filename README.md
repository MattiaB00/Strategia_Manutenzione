# Strategia di Manutenzione Ottimale 🛠️

App interattiva che, dato uno scenario FMEA (Predictability / Severity / Occurrence)
e alcuni parametri economici, suggerisce la strategia di manutenzione più conveniente
tra **Correttiva**, **Preventiva** e **Predittiva**.

Il modello si basa su un albero decisionale (uno per ciascuna delle 27 combinazioni
FMEA) addestrato sui costi calcolati per ogni politica, a partire dal notebook
originale `notebook/Modelli.ipynb`.

## Struttura del progetto

```
.
├── app.py                  # App Streamlit (interfaccia utente)
├── pipeline.py             # Logica di calcolo (estratta dal notebook)
├── tabella_weibull.csv     # Dati necessari al calcolo della manutenzione preventiva
├── requirements.txt        # Dipendenze Python
└── notebook/
    └── Modelli.ipynb       # Notebook originale con l'analisi completa
```

---

## 🚀 Come pubblicare questo progetto su GitHub (guida per chi non l'ha mai fatto)

### 1. Crea un account GitHub
Vai su [github.com](https://github.com) e registrati (è gratis).

### 2. Crea un nuovo repository
- Clicca sul **+** in alto a destra → **New repository**
- Dai un nome, ad es. `strategia-manutenzione`
- Lascialo **Public** (serve per usare la versione gratuita di Streamlit Cloud)
- **Non** spuntare "Add a README" (ne hai già uno)
- Clicca **Create repository**

### 3. Carica i file (senza usare la riga di comando)
Sulla pagina del repository appena creato:
- Clicca **uploading an existing file** (o **Add file → Upload files**)
- Trascina dentro tutti i file di questa cartella (`app.py`, `pipeline.py`,
  `tabella_weibull.csv`, `requirements.txt`, `README.md`, `.gitignore` e la
  cartella `notebook/` con dentro `Modelli.ipynb`)
- Scrivi un messaggio tipo "Primo commit" e clicca **Commit changes**

In alternativa, se preferisci usare Git da terminale:
```bash
git init
git add .
git commit -m "Primo commit"
git branch -M main
git remote add origin https://github.com/TUO-USERNAME/strategia-manutenzione.git
git push -u origin main
```

A questo punto il codice è pubblico su GitHub, ma **è solo codice**: per farlo
usare a chiunque tramite un link cliccabile serve pubblicarlo come app (passo
successivo).

---

## 🌐 Come mettere online l'app (gratis, nessuna installazione per chi la usa)

1. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con il tuo
   account GitHub
2. Clicca **New app**
3. Seleziona il repository che hai appena creato, il branch `main` e come
   "Main file path" scrivi `app.py`
4. Clicca **Deploy**

Dopo un paio di minuti (la prima volta l'app calcola tutti i costi e addestra
i 27 alberi decisionali, ci vogliono circa 20-30 secondi la prima apertura,
poi resta in cache) otterrai un link tipo:

```
https://strategia-manutenzione.streamlit.app
```

Questo link puoi condividerlo con chiunque: si apre nel browser, senza bisogno
di installare Python, Jupyter o altro.

---

## 💻 Come eseguirla in locale (facoltativo, per test)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Si aprirà automaticamente nel browser su `http://localhost:8501`.
