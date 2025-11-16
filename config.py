"""
Configurazione centralizzata per Bilancio Processor MVP
"""
import os

# Configurazione Flask
SECRET_KEY = 'bilancio_mvp_secret_key_2024'
DEBUG = False

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

# File upload
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Credenziali (in produzione usare variabili ambiente)
VALID_USERNAME = os.environ.get('APP_USERNAME', 'admin')
VALID_PASSWORD = os.environ.get('APP_PASSWORD', 'BilancioMVP2024!')

# ==========================================
# REGOLE DI CLASSIFICAZIONE CONTABILE
# ==========================================

# Codici Stato Patrimoniale (01-49)
SP_CODES = [f'{i:02d}' for i in range(1, 50)]

# Codici Conto Economico (50-99)
CE_CODES = [f'{i:02d}' for i in range(50, 100)]

# Codici con SEGNO NEGATIVO in Stato Patrimoniale
SP_NEGATIVE_CODES = [
    '04',  # Fondi ammortamento immobilizzazioni immateriali
    '07',  # Fondi ammortamento immobilizzazioni materiali
    '28',  # Patrimonio netto - Capitale sociale
    '29',  # Patrimonio netto - Riserve e utili
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',  # Passività
]

# Codici con SEGNO NEGATIVO in Conto Economico (Costi)
CE_NEGATIVE_CODES = [f'{i:02d}' for i in range(50, 80)]

# Codici con SEGNO POSITIVO in Conto Economico (Ricavi)
CE_POSITIVE_CODES = [f'{i:02d}' for i in range(80, 100)]

# ==========================================
# PATTERN REGEX PER PARSING
# ==========================================

# Pattern per codici conto italiani
# Formato: XX/XXXX o XX/XXXX/XXXX o XX/******** (con asterischi per totali)
CONTO_CODE_PATTERNS = [
    r'(\d{2}/\d{4,8}(?:/\d{4})?)',  # Standard: 01/0001, 01/0001/0001
    r'(\d{2}/\*{4,8})',  # Con asterischi: 40/********
]

# Pattern per importi (formati IT e EN)
AMOUNT_PATTERNS = [
    r'([\d\.]+,\d{2})',      # IT: 1.234,56
    r'(\d{1,3}(?:\.\d{3})*,\d{2})',  # IT: 1.234.567,89
    r'(\d+,\d{2})',           # IT semplice: 1234,56
    r'([\d,]+\.\d{2})',       # EN: 1,234.56
]

# Pattern per righe di totale da escludere (default)
EXCLUDE_PATTERNS = [
    r'\*{3,}',      # Righe con asterischi multipli
    r'={3,}',       # Righe con uguali
    r'TOTALE',      # Righe con "TOTALE"
    r'SALDO',       # Righe con "SALDO"
]

# Eccezioni: codici speciali che anche con * vanno inclusi
SPECIAL_INCLUDE_CODES = [
    '40/',  # DEBITI V/FORNITORI anche se 40/********
]

# ==========================================
# VALIDAZIONE
# ==========================================

# Lunghezza minima descrizione valida
MIN_DESCRIPTION_LENGTH = 3

# Importo minimo per considerare un conto valido (evita 0.00)
MIN_AMOUNT_VALUE = 0.01

# ==========================================
# QUADRATURA
# ==========================================

# Tolleranza assoluta (euro)
QUADRATURA_TOLERANCE_ABSOLUTE = 1.0

# Tolleranza relativa (percentuale del totale attività)
QUADRATURA_TOLERANCE_RELATIVE = 0.0001  # 0.01%

# Usa tolleranza dinamica: max(absolute, relative * totale)
USE_DYNAMIC_TOLERANCE = True

# ==========================================
# EXCEL OUTPUT
# ==========================================

# Colori header (formato HEX senza #)
HEADER_COLOR = "366092"
HEADER_TEXT_COLOR = "FFFFFF"

# Larghezza colonne
COLUMN_WIDTHS = {
    'Codice': 12,
    'Descrizione': 50,
    'Tipo': 20,
    'Amount': 15,
    'Cluster I': 25,
    'Cluster II': 30,
}

# Nome sheet
SHEET_NAMES = {
    'pulito': 'Bilancino Pulito',
    'mapping': 'Mapping',
    'headline': 'Headline',
}

# ==========================================
# LOGGING
# ==========================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Mantieni log per N giorni
LOG_RETENTION_DAYS = 30
