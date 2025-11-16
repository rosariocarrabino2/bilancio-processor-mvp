"""
Excel Parser - Estrazione dati da bilanci in formato Excel/CSV
"""
import pandas as pd
import re
import config
from typing import Optional, List, Dict, Tuple
from core.parsers.base_parser import BaseParser
from core.utils.logger import ProcessingLogger


class ExcelParser(BaseParser):
    """Parser specializzato per file Excel e CSV"""

    def __init__(self, file_path: str, logger: Optional[ProcessingLogger] = None):
        super().__init__(file_path, logger)
        self.detected_columns = None

    def can_parse(self) -> bool:
        """Verifica se il file è Excel o CSV"""
        ext = self.file_path.lower()
        return ext.endswith(('.xlsx', '.xls', '.csv'))

    def parse(self) -> pd.DataFrame:
        """
        Estrae dati da Excel/CSV

        Returns:
            DataFrame con Codice, Descrizione, Amount
        """
        self.log_info(f"Inizio parsing Excel: {self.file_path}")

        try:
            # Leggi file
            if self.file_path.endswith('.csv'):
                df_raw = pd.read_csv(self.file_path, encoding='utf-8-sig')
            else:
                # Prova prima foglio 0, poi cerca altri
                df_raw = pd.read_excel(self.file_path, sheet_name=0)

            self.log_info(f"File letto: {len(df_raw)} righe, {len(df_raw.columns)} colonne")

            # Auto-detect colonne
            col_mapping = self._detect_columns(df_raw)

            if not col_mapping:
                self.log_error("Impossibile rilevare colonne Codice/Descrizione/Amount")
                return pd.DataFrame(columns=['Codice', 'Descrizione', 'Amount'])

            self.log_info(f"Colonne rilevate: {col_mapping}")

            # Estrai dati
            df_extracted = self._extract_data(df_raw, col_mapping)

            self.log_info(f"Estratti {len(df_extracted)} conti")

            return df_extracted

        except Exception as e:
            self.log_error(f"Errore parsing Excel: {str(e)}")
            raise

    def _detect_columns(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """
        Auto-detect colonne rilevanti

        Args:
            df: DataFrame grezzo

        Returns:
            Dict con mapping: {'codice': 'ColonnaA', 'descrizione': 'ColonnaB', 'amount': 'ColonnaC'}
        """
        mapping = {}

        # Converti nomi colonne in lowercase per confronto
        columns = {col: str(col).lower().strip() for col in df.columns}

        # Pattern per Codice
        codice_keywords = ['codice', 'conto', 'code', 'account', 'cod']
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in codice_keywords):
                mapping['codice'] = col
                break

        # Pattern per Descrizione
        desc_keywords = ['descrizione', 'description', 'desc', 'denominazione', 'nome']
        for col, col_lower in columns.items():
            if col == mapping.get('codice'):  # Evita duplicati
                continue
            if any(kw in col_lower for kw in desc_keywords):
                mapping['descrizione'] = col
                break

        # Pattern per Amount
        amount_keywords = ['importo', 'amount', 'saldo', 'valore', 'balance', 'dare', 'avere']
        for col, col_lower in columns.items():
            if col in [mapping.get('codice'), mapping.get('descrizione')]:
                continue
            if any(kw in col_lower for kw in amount_keywords):
                mapping['amount'] = col
                break

        # Se Amount non trovato, cerca colonna numerica
        if 'amount' not in mapping:
            for col in df.columns:
                if col in [mapping.get('codice'), mapping.get('descrizione')]:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    mapping['amount'] = col
                    break

        # Verifica completezza
        if len(mapping) < 3:
            self.log_warning(f"Colonne rilevate parziali: {mapping}")
            # Prova fallback con posizione (assume prime 3 colonne)
            if len(df.columns) >= 3:
                mapping = {
                    'codice': df.columns[0],
                    'descrizione': df.columns[1],
                    'amount': df.columns[2],
                }
                self.log_info(f"Usando fallback posizionale: {mapping}")
            else:
                return None

        return mapping

    def _extract_data(self, df: pd.DataFrame, col_mapping: Dict) -> pd.DataFrame:
        """
        Estrae e normalizza dati

        Args:
            df: DataFrame grezzo
            col_mapping: Mapping colonne

        Returns:
            DataFrame normalizzato
        """
        # Estrai colonne rilevanti
        df_extracted = pd.DataFrame()

        # Codice
        df_extracted['Codice'] = df[col_mapping['codice']].astype(str).str.strip()

        # Descrizione
        df_extracted['Descrizione'] = df[col_mapping['descrizione']].astype(str).str.strip()

        # Amount (normalizza)
        amount_col = df[col_mapping['amount']]

        # Se è stringa, normalizza
        if pd.api.types.is_string_dtype(amount_col):
            df_extracted['Amount'] = amount_col.apply(self.normalize_amount)
        else:
            df_extracted['Amount'] = pd.to_numeric(amount_col, errors='coerce')

        # Rimuovi righe NULL
        df_extracted = df_extracted.dropna(subset=['Codice', 'Amount'])

        # Filtra righe valide
        df_extracted = df_extracted[
            (df_extracted['Codice'] != '') &
            (df_extracted['Codice'] != 'nan') &
            (df_extracted['Amount'].abs() >= config.MIN_AMOUNT_VALUE)
        ]

        # Filtra codici validi (deve contenere almeno un "/")
        df_extracted = df_extracted[df_extracted['Codice'].str.contains('/', na=False)]

        # Filtra righe di totale (con asterischi)
        df_extracted = df_extracted[~df_extracted['Codice'].str.contains(r'\*{3,}', na=False, regex=True)]

        # Prendi valore assoluto (segno verrà applicato dal classificatore)
        df_extracted['Amount'] = df_extracted['Amount'].abs()

        return df_extracted.reset_index(drop=True)


class ParserFactory:
    """Factory per creare il parser appropriato"""

    @staticmethod
    def create(file_path: str, logger: Optional[ProcessingLogger] = None) -> BaseParser:
        """
        Crea il parser appropriato per il file

        Args:
            file_path: Percorso file
            logger: Logger opzionale

        Returns:
            Parser appropriato (PDFParser o ExcelParser)

        Raises:
            ValueError: Se formato non supportato
        """
        from core.parsers.pdf_parser import PDFParser

        # Prova PDFParser
        pdf_parser = PDFParser(file_path, logger)
        if pdf_parser.can_parse():
            return pdf_parser

        # Prova ExcelParser
        excel_parser = ExcelParser(file_path, logger)
        if excel_parser.can_parse():
            return excel_parser

        # Nessun parser disponibile
        raise ValueError(f"Formato file non supportato: {file_path}")
