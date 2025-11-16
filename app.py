"""
Bilancio Processor MVP - Web Application
Architettura modulare refactored
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.utils import secure_filename
from functools import wraps

import config
from core.bilancio_processor import BilancioProcessor

# Inizializza Flask
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Crea directory necessarie
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
os.makedirs(config.LOG_FOLDER, exist_ok=True)


# ==========================================
# DECORATORS
# ==========================================

def login_required(f):
    """Decorator per proteggere route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Verifica se il file è permesso"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


# ==========================================
# ROUTES - AUTH
# ==========================================

@app.route('/')
def index():
    """Homepage - redirect a dashboard o login"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == config.VALID_USERNAME and password == config.VALID_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenziali non valide')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


# ==========================================
# ROUTES - DASHBOARD
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale"""
    return render_template('dashboard.html')


# ==========================================
# ROUTES - PROCESSING
# ==========================================

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Upload e processing file

    Returns:
        JSON con risultato elaborazione
    """
    # Validazione upload
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nessun file caricato'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nessun file selezionato'})

    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Formato non supportato. Usa: {", ".join(config.ALLOWED_EXTENSIONS)}'
        })

    try:
        # Salva file uploaded
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"{timestamp}_{filename}"
        input_path = os.path.join(config.UPLOAD_FOLDER, file_id)

        file.save(input_path)

        # Prepara output path
        output_filename = f"elaborato_{file_id}".replace('.pdf', '.xlsx').replace('.csv', '.xlsx')
        output_path = os.path.join(config.OUTPUT_FOLDER, output_filename)

        # ===========================
        # PROCESSO PRINCIPALE
        # ===========================
        processor = BilancioProcessor(file_id)
        success, result = processor.process(input_path, output_path)

        if not success:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Errore sconosciuto'),
                'details': result.get('summary', {})
            })

        # Successo!
        return jsonify({
            'success': True,
            'file_id': output_filename,
            'stats': result['stats'],
            'quadratura': result['quadratura'],
            'validation': {
                'warnings': result['validation'].get('warnings', []),
                'stats': result['validation'].get('stats', {})
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore durante elaborazione: {str(e)}'
        })


@app.route('/download/<file_id>')
@login_required
def download_file(file_id):
    """
    Download file elaborato

    Args:
        file_id: ID del file da scaricare
    """
    try:
        file_path = os.path.join(config.OUTPUT_FOLDER, file_id)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File non trovato'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"bilancio_elaborato.xlsx"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 404


# ==========================================
# ROUTES - UTILITY (per future features)
# ==========================================

@app.route('/api/preview/<file_id>')
@login_required
def preview_data(file_id):
    """
    Preview dati elaborati (per futuro)

    Args:
        file_id: ID file elaborato

    Returns:
        JSON con preview dati
    """
    # Placeholder per v2
    return jsonify({
        'success': True,
        'preview': {'message': 'Preview non ancora implementata'}
    })


@app.route('/api/logs/<file_id>')
@login_required
def get_logs(file_id):
    """
    Ottieni log elaborazione (per futuro)

    Args:
        file_id: ID elaborazione

    Returns:
        JSON con log
    """
    # Placeholder per v2
    return jsonify({
        'success': True,
        'logs': []
    })


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({'error': 'Risorsa non trovata'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 handler"""
    return jsonify({'error': 'Errore interno del server'}), 500


# ==========================================
# RUN
# ==========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=config.DEBUG, host='0.0.0.0', port=port)
