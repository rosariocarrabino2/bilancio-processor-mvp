# Bilancio Processor MVP v2.0

Sistema robusto e modulare per l'elaborazione automatica di bilancini di verifica.

## 🎯 Obiettivo

Semplificare la vita a banche di investimento, società di consulenza e imprese trasformando bilancini di verifica grezzi (PDF/Excel) in fogli Excel puliti e lavorabili.

## ✨ Funzionalità

### Input Supportati
- **PDF**: Bilancini in formato PDF (estrazione automatica con pdfplumber)
- **Excel**: File .xlsx, .xls
- **CSV**: File comma-separated values

### Output
File Excel con 3 sheet:

1. **Bilancino Pulito**: 4 colonne (Codice, Descrizione, Tipo, Amount)
2. **Mapping**: 6 colonne (+ Cluster I e Cluster II per riclassificazioni future)
3. **Headline**: Stato Patrimoniale e Conto Economico riclassificati

### Processo
```
Upload → Parsing → Validazione → Classificazione → Quadratura → Excel Output
```

## 🏗️ Architettura

```
bilancio-processor-mvp/
├── app.py                      # Flask application
├── config.py                   # Configurazione centralizzata
├── requirements.txt
│
├── core/                       # Business Logic
│   ├── bilancio_processor.py  # Orchestratore principale
│   ├── parsers/               # Parser multi-formato
│   │   ├── base_parser.py
│   │   ├── pdf_parser.py
│   │   └── excel_parser.py
│   ├── processors/            # Elaborazione dati
│   │   ├── validator.py       # Validazione multi-livello
│   │   └── classifier.py      # Classificazione SP/CE
│   ├── generators/
│   │   └── excel_generator.py
│   └── utils/
│       ├── logger.py          # Logging dettagliato
│       └── quadratura.py      # Sistema quadratura avanzato
│
├── templates/                 # HTML templates
├── uploads/                   # File caricati
├── outputs/                   # Excel generati
└── logs/                      # Log elaborazioni
```

## 🚀 Installazione

```bash
# 1. Clone repository
git clone <repo-url>
cd bilancio-processor-mvp

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia server
python app.py
```

L'applicazione sarà disponibile su: http://localhost:5000

## 🔐 Credenziali Default

- **Username**: `admin`
- **Password**: `BilancioMVP2024!`

## 📋 Validazioni Implementate

### Livello 1: File
- Formato supportato
- Dimensione max 10MB
- File non vuoto

### Livello 2: Struttura Dati
- Colonne richieste presenti
- Valori numerici validi
- Dati sufficienti

### Livello 3: Business Rules
- Codici contabili validi
- Descrizioni complete
- Importi coerenti
- Distribuzione SP/CE bilanciata

## 🎨 Sistema di Quadratura

Verifica automatica con tolleranza dinamica:

- **Tolleranza assoluta**: 1,00€
- **Tolleranza relativa**: 0,01% del totale attività
- **Tolleranza dinamica**: max(assoluta, relativa)

Report dettagliato:
- Stato Patrimoniale (Attività vs Passività)
- Conto Economico (Ricavi vs Costi)
- Quadratura generale (SP + CE = 0)

## 📊 Classificazione Automatica

### Stato Patrimoniale (01-49)
- **Attività**: positive
- **Fondi ammortamento** (04, 07): negative
- **Patrimonio Netto** (28, 29): negative
- **Passività** (40-49): negative

### Conto Economico (50-99)
- **Costi** (50-79): negative
- **Ricavi** (80-99): positive

## 🔧 Configurazione

Modificare `config.py` per personalizzare:

- Pattern regex per codici conti
- Regole classificazione
- Tolleranze quadratura
- Stili output Excel
- Logging level

## 📝 Log

I log vengono salvati in `logs/bilancio_YYYYMMDD.log` con:
- Timestamp
- Livello (INFO/WARNING/ERROR)
- Dettagli elaborazione
- Statistiche

Retention: 30 giorni (configurabile)

## 🐛 Troubleshooting

### Errore "Nessun dato estratto"
- Verificare formato file
- Controllare struttura bilancino
- Consultare log per dettagli

### Bilancio non quadra
- Verificare warning nel report
- Controllare classificazione conti
- Verificare segni importi

### Parser non riconosce colonne Excel
- Verificare nomi colonne (deve contenere: codice/descrizione/importo)
- Provare rinominare colonne
- Consultare log per auto-detection

## 🔜 Roadmap v2.1

- [ ] Integrazione API AIDA per bilanci ufficiali
- [ ] Mapping automatico Cluster I/II
- [ ] Preview interattiva pre-download
- [ ] Supporto batch processing
- [ ] Export PDF report
- [ ] API REST

## 📄 License

MIT

## 👤 Autore

Progetto MVP per semplificazione analisi finanziaria
