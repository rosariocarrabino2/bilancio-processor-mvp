"""
Parser per file PDF ed Excel
Estrae il testo/dati grezzi dai file caricati
"""

import pdfplumber
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileParser:
    """Classe per parsing di file PDF e Excel"""

    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """
        Parse file PDF o Excel e restituisce dati grezzi

        Args:
            file_path: Path al file da parsare

        Returns:
            Dict con 'type', 'content' e 'tables' (se presenti)
        """
        extension = file_path.lower().split('.')[-1]

        if extension == 'pdf':
            return FileParser._parse_pdf(file_path)
        elif extension in ['xlsx', 'xls']:
            return FileParser._parse_excel(file_path)
        else:
            raise ValueError(f"Formato file non supportato: {extension}")

    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, Any]:
        """Estrae testo e tabelle da PDF"""
        logger.info(f"Parsing PDF: {file_path}")

        result = {
            'type': 'pdf',
            'content': '',
            'tables': []
        }

        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = []
                all_tables = []

                for page_num, page in enumerate(pdf.pages, 1):
                    # Estrai testo
                    text = page.extract_text()
                    if text:
                        full_text.append(f"--- Pagina {page_num} ---\n{text}")

                    # Estrai tabelle
                    tables = page.extract_tables()
                    if tables:
                        for table_idx, table in enumerate(tables):
                            all_tables.append({
                                'page': page_num,
                                'index': table_idx,
                                'data': table
                            })

                result['content'] = '\n\n'.join(full_text)
                result['tables'] = all_tables

                logger.info(f"PDF parsed: {len(pdf.pages)} pagine, {len(all_tables)} tabelle")

        except Exception as e:
            logger.error(f"Errore parsing PDF: {e}")
            raise

        return result

    @staticmethod
    def _parse_excel(file_path: str) -> Dict[str, Any]:
        """Estrae dati da file Excel"""
        logger.info(f"Parsing Excel: {file_path}")

        result = {
            'type': 'excel',
            'content': '',
            'sheets': {}
        }

        try:
            # Leggi tutti i fogli
            excel_file = pd.ExcelFile(file_path)

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)

                # Converti in formato utilizzabile
                result['sheets'][sheet_name] = {
                    'dataframe': df,
                    'data': df.to_dict('records'),
                    'text': df.to_string()
                }

            # Crea un content testuale per l'AI
            content_parts = []
            for sheet_name, sheet_data in result['sheets'].items():
                content_parts.append(f"=== Sheet: {sheet_name} ===\n{sheet_data['text']}")

            result['content'] = '\n\n'.join(content_parts)

            logger.info(f"Excel parsed: {len(result['sheets'])} fogli")

        except Exception as e:
            logger.error(f"Errore parsing Excel: {e}")
            raise

        return result
