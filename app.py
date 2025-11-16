import os
import re
import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
import pdfplumber
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from functools import wraps

app = Flask(__name__)
app.secret_key = 'bilancio_mvp_secret_key_2024'

# Configurazione
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Credenziali
VALID_USERNAME = 'admin'
VALID_PASSWORD = 'BilancioMVP2024!'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_bilancio_from_pdf(pdf_path):
    """Estrae dati dal PDF - versione robusta"""
    data = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Prova prima con le tabelle
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 2:
                                continue
                            
                            # Cerca valori numerici nella riga
                            amounts = []
                            for cell in row:
                                if cell:
                                    # Cerca numeri con separatori
                                    matches = re.findall(r'[\d.,]+', str(cell))
                                    for match in matches:
                                        try:
                                            # Prova a convertire in numero
                                            if ',' in match and '.' in match:
                                                # Formato italiano: 1.234,56
                                                num = float(match.replace('.', '').replace(',', '.'))
                                            elif ',' in match:
                                                # Formato italiano: 1234,56
                                                num = float(match.replace(',', '.'))
                                            else:
                                                # Formato standard: 1234.56
                                                num = float(match.replace(',', ''))
                                            
                                            if abs(num) > 0.01:  # Ignora valori troppo piccoli
                                                amounts.append(num)
                                        except:
                                            continue
                            
                            if amounts:
                                # Prendi il primo elemento come codice/descrizione
                                first_cell = str(row[0]) if row[0] else ''
                                
                                # Cerca codice conto (numeri all'inizio)
                                code_match = re.match(r'^(\d+)', first_cell)
                                code = code_match.group(1) if code_match else ''
                                
                                # Descrizione
                                if code:
                                    description = first_cell[len(code):].strip()
                                else:
                                    description = ' '.join([str(cell) for cell in row[:-1] if cell]).strip()
                                
                                # Determina tipo (SP/CE) basato sul codice
                                tipo = 'Stato Patrimoniale'
                                if code:
                                    first_digit = code[0]
                                    if first_digit in ['5', '6', '7', '8', '9']:
                                        tipo = 'Conto Economico'
                                
                                # Usa l'ultimo importo trovato
                                amount = amounts[-1]
                                
                                if description or code:
                                    data.append({
                                        'Codice': code,
                                        'Descrizione': description[:100],  # Limita lunghezza
                                        'Tipo': tipo,
                                        'Amount': amount
                                    })
                
                # Se non ci sono tabelle, prova con il testo
                if not tables:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            if len(line) < 5:
                                continue
                            
                            # Cerca importi nella riga
                            amounts = []
                            amount_matches = re.finditer(r'([\d.,]+)', line)
                            
                            for match in amount_matches:
                                try:
                                    amount_str = match.group(1)
                                    # Conversione tollerante
                                    if ',' in amount_str and '.' in amount_str:
                                        num = float(amount_str.replace('.', '').replace(',', '.'))
                                    elif ',' in amount_str:
                                        num = float(amount_str.replace(',', '.'))
                                    else:
                                        num = float(amount_str)
                                    
                                    if abs(num) > 0.01:
                                        amounts.append((num, match.start()))
                                except:
                                    continue
                            
                            if amounts:
                                # Prendi l'ultimo importo
                                amount, pos = amounts[-1]
                                
                                # Tutto prima dell'importo è codice + descrizione
                                text_part = line[:pos].strip()
                                
                                # Cerca codice
                                code_match = re.match(r'^(\d+)', text_part)
                                code = code_match.group(1) if code_match else ''
                                
                                # Descrizione
                                if code:
                                    description = text_part[len(code):].strip()
                                else:
                                    description = text_part
                                
                                # Determina tipo
                                tipo = 'Stato Patrimoniale'
                                if code and code[0] in ['5', '6', '7', '8', '9']:
                                    tipo = 'Conto Economico'
                                
                                if description or code:
                                    data.append({
                                        'Codice': code,
                                        'Descrizione': description[:100],
                                        'Tipo': tipo,
                                        'Amount': amount
                                    })
        
        # Rimuovi duplicati
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.drop_duplicates(subset=['Codice', 'Descrizione'], keep='first')
            # Ordina per codice
            df = df.sort_values('Codice', na_position='last')
        
        return df
        
    except Exception as e:
        print(f"Errore nell'estrazione: {str(e)}")
        return pd.DataFrame()

def create_excel_output(df, output_path):
    """Crea file Excel con 3 sheets"""
    wb = Workbook()
    
    # Sheet 1: Bilancino Pulito
    ws1 = wb.active
    ws1.title = "Bilancino Pulito"
    
    headers = ['Codice', 'Descrizione', 'Tipo', 'Amount']
    ws1.append(headers)
    
    # Stile header
    for cell in ws1[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Aggiungi dati
    for _, row in df.iterrows():
        ws1.append([row['Codice'], row['Descrizione'], row['Tipo'], row['Amount']])
    
    # Formattazione colonne
    ws1.column_dimensions['A'].width = 12
    ws1.column_dimensions['B'].width = 50
    ws1.column_dimensions['C'].width = 20
    ws1.column_dimensions['D'].width = 15
    
    # Sheet 2: Mapping
    ws2 = wb.create_sheet("Mapping")
    mapping_headers = ['Codice', 'Descrizione', 'Tipo', 'Amount', 'Cluster I', 'Cluster II']
    ws2.append(mapping_headers)
    
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    for _, row in df.iterrows():
        ws2.append([row['Codice'], row['Descrizione'], row['Tipo'], row['Amount'], '', ''])
    
    # Formattazione colonne
    ws2.column_dimensions['A'].width = 12
    ws2.column_dimensions['B'].width = 50
    ws2.column_dimensions['C'].width = 20
    ws2.column_dimensions['D'].width = 15
    ws2.column_dimensions['E'].width = 25
    ws2.column_dimensions['F'].width = 30
    
    # Sheet 3: Headline
    ws3 = wb.create_sheet("Headline")
    
    ws3.append(["STATO PATRIMONIALE"])
    ws3['A1'].font = Font(bold=True, size=14)
    ws3.append([])
    ws3.append(["Voce", "Importo"])
    
    # Header
    for cell in ws3[3]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    
    ws3.append([])
    ws3.append([])
    
    ws3.append(["CONTO ECONOMICO"])
    ws3['A6'].font = Font(bold=True, size=14)
    ws3.append([])
    ws3.append(["Voce", "Importo"])
    
    # Header
    for cell in ws3[8]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    
    # Formattazione colonne
    ws3.column_dimensions['A'].width = 40
    ws3.column_dimensions['B'].width = 15
    
    # Salva
    wb.save(output_path)

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenziali non valide')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file caricato'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nessun file selezionato'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Formato file non supportato'})
    
    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"{timestamp}_{filename}"
        input_path = os.path.join(UPLOAD_FOLDER, file_id)
        file.save(input_path)
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            df = extract_bilancio_from_pdf(input_path)
        else:
            return jsonify({'success': False, 'error': 'Formato Excel non ancora supportato'})
        
        if df.empty:
            return jsonify({'success': False, 'error': 'Impossibile estrarre dati dal file. Verifica che sia un bilancino di verifica valido.'})
        
        output_filename = f"elaborato_{file_id.replace('.pdf', '.xlsx')}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        create_excel_output(df, output_path)
        
        df_sp = df[df['Tipo'] == 'Stato Patrimoniale']
        df_ce = df[df['Tipo'] == 'Conto Economico']
        totale = df['Amount'].sum()
        
        stats = {
            'total_conti': int(len(df)),
            'conti_sp': int(len(df_sp)),
            'conti_ce': int(len(df_ce)),
            'totale': float(totale),
            'quadra': bool(abs(totale) < 0.10)
        }
        
        return jsonify({
            'success': True,
            'file_id': output_filename,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Errore durante elaborazione: {str(e)}'})

@app.route('/download/<file_id>')
@login_required
def download_file(file_id):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, file_id)
        return send_file(file_path, as_attachment=True, download_name=f"bilancio_elaborato.xlsx")
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
