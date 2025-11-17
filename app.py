"""
Bilancio Processor MVP
Applicazione Flask per processare bilancini di verifica
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from config import Config
from services import FileParser, BilancioProcessor, ExcelGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Inizializza Flask
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app()


def allowed_file(filename):
    """Verifica se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Homepage con interfaccia upload"""
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def process_file():
    """
    Endpoint per processare file bilancino

    Returns:
        JSON con status e path al file generato
    """
    try:
        # Verifica presenza file
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file caricato'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Nome file vuoto'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato file non supportato. Usa PDF, XLS o XLSX'}), 400

        # Salva file upload
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(Config.UPLOAD_FOLDER, upload_filename)

        file.save(upload_path)
        logger.info(f"File caricato: {upload_path}")

        # Step 1: Parsing
        logger.info("Step 1: Parsing file...")
        parser = FileParser()
        parsed_data = parser.parse_file(upload_path)

        # Step 2: Processing con AI
        logger.info("Step 2: Estrazione bilancino con AI...")
        processor = BilancioProcessor()
        bilancino = processor.extract_bilancino(parsed_data)

        # Step 3: Validazione
        logger.info("Step 3: Validazione...")
        validation = processor.validate_bilancino(bilancino)

        if not validation['valid']:
            logger.error(f"Validazione fallita: {validation['errors']}")
            return jsonify({
                'error': 'Errore nella validazione del bilancino',
                'details': validation['errors']
            }), 400

        if validation['warnings']:
            logger.warning(f"Warning: {validation['warnings']}")

        # Step 4: Generazione Excel
        logger.info("Step 4: Generazione Excel...")
        output_filename = f"bilancino_pulito_{timestamp}.xlsx"
        output_path = os.path.join(Config.OUTPUT_FOLDER, output_filename)

        generator = ExcelGenerator()
        generator.generate_bilancino_excel(bilancino, output_path)

        logger.info(f"Processing completato: {output_filename}")

        return jsonify({
            'success': True,
            'message': 'Bilancino processato con successo',
            'output_file': output_filename,
            'num_accounts': len(bilancino),
            'warnings': validation['warnings']
        })

    except Exception as e:
        logger.error(f"Errore nel processing: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Errore nel processing del file',
            'details': str(e)
        }), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """
    Download del file Excel generato

    Args:
        filename: Nome del file da scaricare

    Returns:
        File Excel
    """
    try:
        file_path = os.path.join(Config.OUTPUT_FOLDER, secure_filename(filename))

        if not os.path.exists(file_path):
            return jsonify({'error': 'File non trovato'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"Errore nel download: {str(e)}")
        return jsonify({'error': 'Errore nel download del file'}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Verifica configurazione
    if not Config.OPENAI_API_KEY:
        logger.warning("ATTENZIONE: OPENAI_API_KEY non configurata!")
        print("\n" + "="*60)
        print("CONFIGURAZIONE RICHIESTA")
        print("="*60)
        print("Crea un file .env nella root del progetto con:")
        print("OPENAI_API_KEY=sk-your-api-key-here")
        print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
