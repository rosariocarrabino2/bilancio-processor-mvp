"""
Base Parser - Classe astratta per tutti i parser
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional
from core.utils.logger import ProcessingLogger


class BaseParser(ABC):
    """Classe base astratta per parser di bilanci"""

    def __init__(self, file_path: str, logger: Optional[ProcessingLogger] = None):
        """
        Inizializza parser

        Args:
            file_path: Percorso del file da parsare
            logger: Logger opzionale per tracking
        """
        self.file_path = file_path
        self.logger = logger
        self.raw_data = []

    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """
        Metodo astratto per parsing del file

        Returns:
            DataFrame con colonne: ['Codice', 'Descrizione', 'Amount']
            (Tipo non ancora classificato)
        """
        pass

    @abstractmethod
    def can_parse(self) -> bool:
        """
        Verifica se il parser può gestire questo file

        Returns:
            True se può parsare, False altrimenti
        """
        pass

    def log_info(self, message: str):
        """Helper per logging info"""
        if self.logger:
            self.logger.info(message)

    def log_warning(self, message: str):
        """Helper per logging warning"""
        if self.logger:
            self.logger.warning(message)

    def log_error(self, message: str):
        """Helper per logging error"""
        if self.logger:
            self.logger.error(message)

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """
        Normalizza stringa importo in float

        Gestisce formati:
        - IT: 1.234,56
        - EN: 1,234.56
        - Semplice: 1234.56

        Args:
            amount_str: Stringa con importo

        Returns:
            Float o None se non parsabile
        """
        if not amount_str:
            return None

        try:
            amount_str = str(amount_str).strip()

            # Rimuovi spazi
            amount_str = amount_str.replace(' ', '')

            # Formato IT: 1.234,56
            if ',' in amount_str and '.' in amount_str:
                # Se punto prima di virgola → IT
                if amount_str.index('.') < amount_str.index(','):
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                # Se virgola prima di punto → EN
                else:
                    amount_str = amount_str.replace(',', '')

            # Solo virgola: IT
            elif ',' in amount_str:
                amount_str = amount_str.replace(',', '.')

            # Solo punto o nessuno: già OK
            return float(amount_str)

        except (ValueError, AttributeError):
            return None

    def create_dataframe(self, data: list) -> pd.DataFrame:
        """
        Crea DataFrame da lista di dict

        Args:
            data: Lista di dict con keys: Codice, Descrizione, Amount

        Returns:
            DataFrame pulito
        """
        if not data:
            return pd.DataFrame(columns=['Codice', 'Descrizione', 'Amount'])

        df = pd.DataFrame(data)

        # Assicura colonne corrette
        required_cols = ['Codice', 'Descrizione', 'Amount']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''

        # Riordina colonne
        df = df[required_cols]

        return df
