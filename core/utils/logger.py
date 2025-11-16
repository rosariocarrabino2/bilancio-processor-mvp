"""
Sistema di logging centralizzato con rotazione file e formattazione colorata
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
import config

class BilancioLogger:
    """Logger personalizzato per Bilancio Processor"""

    def __init__(self, name='bilancio_processor'):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))

        # Evita duplicati
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()

        # Cleanup vecchi log
        self._cleanup_old_logs()

    def _setup_file_handler(self):
        """Crea handler per file log"""
        os.makedirs(config.LOG_FOLDER, exist_ok=True)

        # File log con timestamp
        log_filename = f"bilancio_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(config.LOG_FOLDER, log_filename)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def _setup_console_handler(self):
        """Crea handler per console (solo WARNING+)"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def _cleanup_old_logs(self):
        """Rimuove log più vecchi di LOG_RETENTION_DAYS"""
        try:
            log_folder = Path(config.LOG_FOLDER)
            if not log_folder.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=config.LOG_RETENTION_DAYS)

            for log_file in log_folder.glob('bilancio_*.log'):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.logger.debug(f"Rimosso vecchio log: {log_file.name}")
        except Exception as e:
            self.logger.error(f"Errore cleanup log: {e}")

    def get_logger(self):
        """Ritorna il logger configurato"""
        return self.logger


class ProcessingLogger:
    """Logger specifico per singola elaborazione con statistiche"""

    def __init__(self, file_id):
        self.file_id = file_id
        self.logger = BilancioLogger().get_logger()
        self.stats = {
            'warnings': 0,
            'errors': 0,
            'conti_estratti': 0,
            'conti_validi': 0,
            'duplicati_rimossi': 0,
        }
        self.messages = []

    def info(self, message):
        """Log info con tracking"""
        msg = f"[{self.file_id}] {message}"
        self.logger.info(msg)
        self.messages.append(('info', message))

    def warning(self, message):
        """Log warning con conteggio"""
        msg = f"[{self.file_id}] {message}"
        self.logger.warning(msg)
        self.stats['warnings'] += 1
        self.messages.append(('warning', message))

    def error(self, message):
        """Log error con conteggio"""
        msg = f"[{self.file_id}] {message}"
        self.logger.error(msg)
        self.stats['errors'] += 1
        self.messages.append(('error', message))

    def debug(self, message):
        """Log debug"""
        msg = f"[{self.file_id}] {message}"
        self.logger.debug(msg)

    def update_stat(self, key, value):
        """Aggiorna statistica"""
        self.stats[key] = value

    def increment_stat(self, key, amount=1):
        """Incrementa statistica"""
        self.stats[key] = self.stats.get(key, 0) + amount

    def get_summary(self):
        """Ritorna summary dell'elaborazione"""
        return {
            'file_id': self.file_id,
            'stats': self.stats,
            'messages': self.messages,
            'has_errors': self.stats['errors'] > 0,
            'has_warnings': self.stats['warnings'] > 0,
        }

    def format_summary(self):
        """Formatta summary in formato leggibile"""
        lines = [
            f"\n{'='*60}",
            f"SUMMARY ELABORAZIONE: {self.file_id}",
            f"{'='*60}",
            f"Conti estratti: {self.stats.get('conti_estratti', 0)}",
            f"Conti validi: {self.stats.get('conti_validi', 0)}",
            f"Duplicati rimossi: {self.stats.get('duplicati_rimossi', 0)}",
            f"Warnings: {self.stats['warnings']}",
            f"Errors: {self.stats['errors']}",
            f"{'='*60}",
        ]

        if self.messages:
            lines.append("\nMESSAGGI:")
            for level, msg in self.messages[-10:]:  # Ultimi 10
                icon = '⚠️' if level == 'warning' else '❌' if level == 'error' else 'ℹ️'
                lines.append(f"  {icon} {msg}")

        return '\n'.join(lines)


# Istanza globale
_global_logger = None

def get_logger():
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = BilancioLogger().get_logger()
    return _global_logger
