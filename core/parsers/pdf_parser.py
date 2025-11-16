"""
PDF Parser - Estrazione dati da bilanci in formato PDF
"""
import pdfplumber
import pandas as pd
import re
import config
from typing import Optional, List, Dict
from core.parsers.base_parser import BaseParser
from core.utils.logger import ProcessingLogger


class PDFParser(BaseParser):
    """Parser specializzato per file PDF"""

    def __init__(self, file_path: str, logger: Optional[ProcessingLogger] = None):
        super().__init__(file_path, logger)
        self.pages_to_skip_end = 2  # Salta ultime N pagine (sezione fiscale)

    def can_parse(self) -> bool:
        """Verifica se il file è un PDF"""
        return self.file_path.lower().endswith('.pdf')

    def parse(self) -> pd.DataFrame:
        """
        Estrae dati dal PDF

        Returns:
            DataFrame con Codice, Descrizione, Amount
        """
        self.log_info(f"Inizio parsing PDF: {self.file_path}")

        try:
            with pdfplumber.open(self.file_path) as pdf:
                num_pages = len(pdf.pages)
                self.log_info(f"PDF contiene {num_pages} pagine")

                # Determina quante pagine processare
                pages_to_process = max(1, num_pages - self.pages_to_skip_end)
                self.log_info(f"Processerò {pages_to_process} pagine (escluse ultime {self.pages_to_skip_end})")

                for page_idx, page in enumerate(pdf.pages):
                    if page_idx >= pages_to_process:
                        break

                    # Prova prima con tabelle estratte
                    tables = page.extract_tables()
                    if tables:
                        self._extract_from_tables(tables, page_idx)
                    else:
                        # Fallback: estrazione da testo
                        text = page.extract_text()
                        if text:
                            self._extract_from_text(text, page_idx)

                self.log_info(f"Estratti {len(self.raw_data)} conti grezzi")

                # Crea DataFrame
                df = self.create_dataframe(self.raw_data)

                return df

        except Exception as e:
            self.log_error(f"Errore parsing PDF: {str(e)}")
            raise

    def _extract_from_tables(self, tables: List, page_idx: int):
        """Estrae dati da tabelle strutturate"""
        for table in tables:
            for row in table:
                if not row or len(row) < 2:
                    continue

                # Analizza riga
                conto = self._parse_table_row(row)
                if conto:
                    self.raw_data.append(conto)

    def _extract_from_text(self, text: str, page_idx: int):
        """Estrae dati da testo non strutturato"""
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue

            conto = self._parse_text_line(line)
            if conto:
                self.raw_data.append(conto)

    def _parse_table_row(self, row: List) -> Optional[Dict]:
        """
        Parsa una riga di tabella

        Args:
            row: Lista di celle della riga

        Returns:
            Dict con Codice, Descrizione, Amount o None
        """
        # Unisci tutte le celle per analisi completa
        row_text = ' '.join([str(cell) if cell else '' for cell in row])

        # Verifica se è da escludere
        if self._should_exclude(row_text):
            return None

        # Cerca codice conto
        code = self._extract_code(row_text)
        if not code:
            return None

        # Cerca importi
        amounts = self._extract_amounts(row)
        if not amounts:
            return None

        # Estrai descrizione
        description = self._extract_description(row_text, code)
        if not description or len(description) < config.MIN_DESCRIPTION_LENGTH:
            return None

        # Usa ultimo importo trovato (convenzione bilancini italiani)
        amount = amounts[-1]

        return {
            'Codice': code,
            'Descrizione': description,
            'Amount': abs(amount),  # Segno verrà applicato dal classificatore
        }

    def _parse_text_line(self, line: str) -> Optional[Dict]:
        """Parsa una linea di testo"""
        # Stesso processo del table row
        if self._should_exclude(line):
            return None

        code = self._extract_code(line)
        if not code:
            return None

        # Estrai importi dal testo
        amount_matches = re.finditer(r'([\d.,]+)', line)
        amounts = []

        for match in amount_matches:
            amount_str = match.group(1)
            if len(amount_str) < 3:  # Evita codici come "03"
                continue

            amount = self.normalize_amount(amount_str)
            if amount and abs(amount) >= config.MIN_AMOUNT_VALUE:
                amounts.append(amount)

        if not amounts:
            return None

        description = self._extract_description(line, code)
        if not description or len(description) < config.MIN_DESCRIPTION_LENGTH:
            return None

        return {
            'Codice': code,
            'Descrizione': description,
            'Amount': abs(amounts[-1]),
        }

    def _should_exclude(self, text: str) -> bool:
        """
        Verifica se la riga deve essere esclusa

        Args:
            text: Testo della riga

        Returns:
            True se da escludere
        """
        # Eccezioni: codici speciali che vanno inclusi anche con *
        for special_code in config.SPECIAL_INCLUDE_CODES:
            if special_code in text and 'FORN' in text.upper():
                return False

        # Escludi pattern di totale
        for pattern in config.EXCLUDE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Escludi righe con asterischi (totali)
        if '*' in text:
            return True

        return False

    def _extract_code(self, text: str) -> Optional[str]:
        """
        Estrae codice conto dal testo

        Args:
            text: Testo contenente il codice

        Returns:
            Codice estratto o None
        """
        for pattern in config.CONTO_CODE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_amounts(self, row: List) -> List[float]:
        """
        Estrae tutti gli importi da una riga

        Args:
            row: Lista celle

        Returns:
            Lista di importi
        """
        amounts = []

        for cell in row:
            if not cell:
                continue

            # Cerca numeri nella cella
            cell_str = str(cell)
            matches = re.findall(r'[\d.,]+', cell_str)

            for match in matches:
                if len(match) < 3:  # Evita codici brevi tipo "03"
                    continue

                amount = self.normalize_amount(match)
                if amount and abs(amount) >= config.MIN_AMOUNT_VALUE:
                    amounts.append(amount)

        return amounts

    def _extract_description(self, text: str, code: str) -> str:
        """
        Estrae descrizione del conto

        Args:
            text: Testo completo riga
            code: Codice già estratto

        Returns:
            Descrizione pulita
        """
        # Trova posizione del codice
        code_pos = text.find(code)
        if code_pos == -1:
            return ''

        # Estrai tutto dopo il codice
        desc_start = code_pos + len(code)
        description = text[desc_start:].strip()

        # Rimuovi numeri alla fine (importi)
        description = re.sub(r'[\d.,\s]+$', '', description).strip()

        # Rimuovi caratteri speciali extra
        description = re.sub(r'\s+', ' ', description)

        # Limita lunghezza
        return description[:100]
