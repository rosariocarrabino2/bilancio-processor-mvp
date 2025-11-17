# 📊 Bilancio Processor MVP

**Automatizza l'analisi dei bilancini di verifica per banche d'investimento, società di consulenza e imprese.**

## 🎯 Cosa fa

Trasforma un bilancino di verifica grezzo (PDF o Excel) in un file Excel pulito e strutturato con:

### Sheet 1: "Bilancino Pulito"
- **Codice Conto**: Codice del conto contabile
- **Descrizione**: Descrizione del conto
- **Tipo Voce**: SP (Stato Patrimoniale) o CE (Conto Economico)
- **Importo**: Valore numerico del conto

## 🚀 Quick Start

### 1. Requisiti
- Python 3.8+
- Account OpenAI (per API GPT)

### 2. Installazione

```bash
# Clona il repository
git clone <repository-url>
cd bilancio-processor-mvp

# Installa dipendenze
pip install -r requirements.txt

# Configura variabili d'ambiente
cp .env.example .env
# Modifica .env e inserisci la tua OPENAI_API_KEY
```

### 3. Configurazione

Crea un file `.env` nella root del progetto:

```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

**IMPORTANTE**: Devi avere una API Key di OpenAI attiva. Ottienila su [platform.openai.com](https://platform.openai.com/api-keys)

### 4. Avvio

```bash
python app.py
```

Apri il browser su: **http://localhost:5000**

## 💡 Come si usa

1. **Carica il file**: Trascina o seleziona il tuo bilancino di verifica (PDF o Excel)
2. **Processa**: Click su "Processa Bilancino"
3. **Scarica**: Download automatico dell'Excel pulito

**È semplicissimo!** 🎉

## 🏗️ Architettura

```
bilancio-processor-mvp/
├── app.py                    # Flask app principale
├── config.py                 # Configurazioni
├── requirements.txt          # Dipendenze Python
├── .env                      # Variabili d'ambiente (da creare)
│
├── services/
│   ├── parser.py            # Parsing PDF/Excel
│   ├── processor.py         # AI processing (GPT)
│   └── excel_generator.py   # Generazione Excel output
│
├── templates/
│   └── index.html           # UI web
│
├── static/
│   ├── css/style.css        # Styling
│   └── js/app.js            # Frontend logic
│
├── uploads/                 # File caricati dagli utenti
├── outputs/                 # Excel generati
└── logs/                    # Log applicazione
```

## 🔧 Tecnologie

- **Backend**: Flask (Python)
- **AI**: OpenAI GPT-4
- **Parsing**: pdfplumber, pandas, openpyxl
- **Frontend**: HTML5, CSS3, JavaScript vanilla

## 🎨 Features

- ✅ Interfaccia drag & drop intuitiva
- ✅ Supporto PDF e Excel (XLS, XLSX)
- ✅ Parsing intelligente con AI
- ✅ Gestione formati variabili
- ✅ Classificazione automatica SP/CE
- ✅ Excel output pulito e formattato
- ✅ Validazione dati
- ✅ Logging completo

## 🔮 Roadmap (Future)

- [ ] **Sheet 2**: Mapping con Cluster I e II
- [ ] **Sheet 3**: Headline SP e CE
- [ ] **Integrazione AIDA**: Recupero bilanci ufficiali
- [ ] **Multi-utente**: Autenticazione e gestione utenti
- [ ] **Batch processing**: Processa multipli file
- [ ] **Export multipli**: JSON, CSV, PDF

## 🐛 Troubleshooting

### Errore: "OPENAI_API_KEY non configurata"
→ Crea il file `.env` e inserisci la tua API key OpenAI

### Errore: "Formato file non supportato"
→ Usa solo file PDF, XLS o XLSX

### Errore nel parsing
→ Verifica che il bilancino contenga dati tabellari strutturati

## 📝 License

MIT License - Vedi LICENSE file

## 👨‍💻 Autore

Sviluppato per semplificare la vita a professionisti della finanza

---

**Pronto per iniziare? Avvia l'app e carica il tuo primo bilancino! 🚀**
