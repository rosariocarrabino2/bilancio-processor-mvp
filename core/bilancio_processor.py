"""
Orchestratore principale - Coordina parsing, validazione, classificazione e output
"""
import pandas as pd
from typing import Dict, Tuple
import os

from core.parsers.excel_parser import ParserFactory
from core.processors import Validator, DataCleaner, BilancioClassifier
from core.utils.quadratura import QuadraturaChecker, QuadraturaReport
from core.utils.logger import ProcessingLogger
from core.generators.excel_generator import ExcelGenerator


class BilancioProcessor:
    """Orchestratore completo del processo di elaborazione"""

    def __init__(self, file_id: str):
        """
        Inizializza processor

        Args:
            file_id: ID univoco per questo processo
        """
        self.file_id = file_id
        self.logger = ProcessingLogger(file_id)
        self.validation_report = None
        self.quadratura_report = None
        self.df_processed = None

    def process(
        self,
        input_path: str,
        output_path: str
    ) -> Tuple[bool, Dict]:
        """
        Processo completo: parsing → validazione → classificazione → quadratura → output

        Args:
            input_path: Percorso file input
            output_path: Percorso file output Excel

        Returns:
            (success, result_dict)
        """
        try:
            self.logger.info(f"Inizio elaborazione: {input_path}")

            # =====================
            # STEP 1: PARSING
            # =====================
            self.logger.info("STEP 1: Parsing file...")

            parser = ParserFactory.create(input_path, self.logger)
            df_raw = parser.parse()

            self.logger.update_stat('conti_estratti', len(df_raw))

            if df_raw.empty:
                return False, {
                    'error': 'Nessun dato estratto dal file',
                    'summary': self.logger.get_summary()
                }

            self.logger.info(f"Parsing completato: {len(df_raw)} conti estratti")

            # =====================
            # STEP 2: VALIDAZIONE
            # =====================
            self.logger.info("STEP 2: Validazione dati...")

            self.validation_report = Validator.validate_all(df_raw, input_path)

            # Log warnings
            for warning in self.validation_report.get('warnings', []):
                self.logger.warning(warning)

            # Check errori critici
            if not self.validation_report['valid']:
                errors = self.validation_report.get('errors', [])
                for error in errors:
                    self.logger.error(error)

                return False, {
                    'error': 'Validazione fallita: ' + '; '.join(errors),
                    'validation': self.validation_report,
                    'summary': self.logger.get_summary()
                }

            self.logger.info("Validazione superata")

            # =====================
            # STEP 3: PULIZIA
            # =====================
            self.logger.info("STEP 3: Pulizia dati...")

            df_clean = DataCleaner.clean_dataframe(df_raw)

            duplicati_rimossi = len(df_raw) - len(df_clean)
            if duplicati_rimossi > 0:
                self.logger.warning(f"{duplicati_rimossi} conti duplicati rimossi")
                self.logger.update_stat('duplicati_rimossi', duplicati_rimossi)

            self.logger.update_stat('conti_validi', len(df_clean))
            self.logger.info(f"Pulizia completata: {len(df_clean)} conti validi")

            # =====================
            # STEP 4: CLASSIFICAZIONE
            # =====================
            self.logger.info("STEP 4: Classificazione SP/CE e applicazione segni...")

            df_classified = BilancioClassifier.classify_and_sign(df_clean)

            # Stats classificazione
            class_stats = BilancioClassifier.get_classification_stats(df_classified)
            self.logger.info(
                f"Classificati: {class_stats['sp']['count']} SP, "
                f"{class_stats['ce']['count']} CE"
            )

            if class_stats['non_classificati'] > 0:
                self.logger.warning(f"{class_stats['non_classificati']} conti non classificati")

            # =====================
            # STEP 5: QUADRATURA
            # =====================
            self.logger.info("STEP 5: Verifica quadratura...")

            self.quadratura_report = QuadraturaChecker.verifica_quadratura(df_classified)

            # Log risultato
            if self.quadratura_report.quadra:
                self.logger.info(f"✅ Bilancio QUADRA (diff: {self.quadratura_report.differenza_totale:.2f}€)")
            else:
                self.logger.warning(f"⚠️  Bilancio NON quadra (diff: {self.quadratura_report.differenza_totale:.2f}€)")

            # Log warnings quadratura
            for warning in self.quadratura_report.warnings:
                self.logger.warning(warning)

            # Log report leggibile
            self.logger.debug(self.quadratura_report.format_text())

            # =====================
            # STEP 6: GENERAZIONE OUTPUT
            # =====================
            self.logger.info("STEP 6: Generazione Excel...")

            generator = ExcelGenerator(output_path)
            generator.generate(df_classified, self.quadratura_report)

            self.logger.info(f"Excel generato: {output_path}")

            # =====================
            # SUCCESS
            # =====================
            self.df_processed = df_classified

            result = {
                'success': True,
                'stats': {
                    'total_conti': len(df_classified),
                    'conti_sp': class_stats['sp']['count'],
                    'conti_ce': class_stats['ce']['count'],
                    'conti_estratti': self.logger.stats.get('conti_estratti', 0),
                    'duplicati_rimossi': duplicati_rimossi,
                },
                'quadratura': self.quadratura_report.to_dict(),
                'validation': self.validation_report,
                'summary': self.logger.get_summary(),
            }

            self.logger.info("✅ Elaborazione completata con successo")
            self.logger.info(self.logger.format_summary())

            return True, result

        except Exception as e:
            self.logger.error(f"Errore durante elaborazione: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())

            return False, {
                'error': f'Errore: {str(e)}',
                'summary': self.logger.get_summary()
            }

    def get_preview_data(self, limit: int = 20) -> Dict:
        """
        Ottieni preview dei dati processati

        Args:
            limit: Numero righe da restituire

        Returns:
            Dict con preview
        """
        if self.df_processed is None:
            return {'data': []}

        # Prime N righe
        preview_df = self.df_processed.head(limit)

        # Converti a dict
        data = preview_df.to_dict('records')

        # Formatta amounts
        for row in data:
            row['Amount'] = f"{row['Amount']:,.2f}"

        return {
            'data': data,
            'total_rows': len(self.df_processed),
            'showing': len(preview_df),
        }
