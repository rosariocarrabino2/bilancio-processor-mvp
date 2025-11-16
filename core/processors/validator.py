"""
Sistema di validazione multi-livello per dati di bilancio
"""
import pandas as pd
import os
import config
from typing import Tuple, List, Dict


class ValidationError(Exception):
    """Eccezione custom per errori di validazione"""
    pass


class Validator:
    """Validatore multi-livello per file e dati"""

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, List[str]]:
        """
        Livello 1: Validazione file fisico

        Args:
            file_path: Percorso del file da validare

        Returns:
            (is_valid, errors_list)
        """
        errors = []

        # Check esistenza
        if not os.path.exists(file_path):
            errors.append("File non trovato")
            return False, errors

        # Check dimensione
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            errors.append("File vuoto")
            return False, errors

        if file_size > config.MAX_FILE_SIZE:
            max_mb = config.MAX_FILE_SIZE / (1024 * 1024)
            errors.append(f"File troppo grande (max {max_mb}MB)")
            return False, errors

        # Check estensione
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            errors.append(f"Formato non supportato. Usa: {', '.join(config.ALLOWED_EXTENSIONS)}")
            return False, errors

        return True, errors

    @staticmethod
    def validate_dataframe_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Livello 2: Validazione struttura DataFrame

        Args:
            df: DataFrame da validare

        Returns:
            (is_valid, errors_list)
        """
        errors = []
        warnings = []

        # Check vuoto
        if df.empty:
            errors.append("Nessun dato estratto dal file")
            return False, errors

        # Check numero minimo righe
        if len(df) < 5:
            warnings.append(f"Solo {len(df)} conti trovati, sembra poco")

        # Check colonne richieste
        required_columns = ['Codice', 'Descrizione', 'Tipo', 'Amount']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            errors.append(f"Colonne mancanti: {', '.join(missing_columns)}")
            return False, errors

        # Check tipi dati
        if not pd.api.types.is_numeric_dtype(df['Amount']):
            errors.append("Colonna 'Amount' deve contenere valori numerici")

        # Check valori NULL critici
        null_codici = df['Codice'].isna().sum()
        if null_codici > 0:
            errors.append(f"{null_codici} conti senza codice")

        null_amounts = df['Amount'].isna().sum()
        if null_amounts > 0:
            errors.append(f"{null_amounts} conti senza importo")

        return len(errors) == 0, errors + warnings

    @staticmethod
    def validate_business_rules(df: pd.DataFrame) -> Tuple[bool, List[str], Dict]:
        """
        Livello 3: Validazione regole di business

        Args:
            df: DataFrame validato

        Returns:
            (is_valid, warnings_list, stats_dict)
        """
        warnings = []
        stats = {}

        # Check codici validi
        invalid_codes = []
        for idx, row in df.iterrows():
            code = str(row['Codice'])
            # Verifica formato: XX/YYYY o XX/YYYY/ZZZZ
            if not ('/' in code and len(code.split('/')[0]) == 2):
                invalid_codes.append(code)

        if invalid_codes:
            warnings.append(f"{len(invalid_codes)} codici in formato non standard")
            stats['invalid_codes'] = invalid_codes[:5]  # Primi 5

        # Check descrizioni vuote o troppo corte
        short_descriptions = df[
            (df['Descrizione'].isna()) |
            (df['Descrizione'].str.len() < config.MIN_DESCRIPTION_LENGTH)
        ]

        if len(short_descriptions) > 0:
            warnings.append(f"{len(short_descriptions)} conti con descrizione mancante o troppo corta")
            stats['short_descriptions'] = len(short_descriptions)

        # Check importi zero
        zero_amounts = df[df['Amount'] == 0]
        if len(zero_amounts) > 0:
            warnings.append(f"{len(zero_amounts)} conti con importo zero")
            stats['zero_amounts'] = len(zero_amounts)

        # Check valori outlier (importi molto grandi)
        if not df.empty:
            median_amount = df['Amount'].abs().median()
            outliers = df[df['Amount'].abs() > median_amount * 1000]
            if len(outliers) > 0:
                warnings.append(f"{len(outliers)} conti con importi molto elevati (possibili errori)")
                stats['outliers'] = outliers[['Codice', 'Descrizione', 'Amount']].to_dict('records')[:3]

        # Check distribuzione SP/CE
        sp_count = len(df[df['Tipo'] == 'Stato Patrimoniale'])
        ce_count = len(df[df['Tipo'] == 'Conto Economico'])
        other_count = len(df) - sp_count - ce_count

        if other_count > 0:
            warnings.append(f"{other_count} conti senza classificazione SP/CE")

        stats['distribution'] = {
            'sp': sp_count,
            'ce': ce_count,
            'other': other_count,
            'total': len(df),
        }

        # Check bilanciamento (almeno 20% di ogni tipo)
        if sp_count > 0 and ce_count > 0:
            ratio_sp = sp_count / len(df)
            ratio_ce = ce_count / len(df)

            if ratio_sp < 0.2:
                warnings.append("Pochi conti Stato Patrimoniale rispetto al totale")
            if ratio_ce < 0.2:
                warnings.append("Pochi conti Conto Economico rispetto al totale")

        # Tutto OK se non ci sono warning critici
        is_valid = True
        return is_valid, warnings, stats

    @staticmethod
    def validate_all(df: pd.DataFrame, file_path: str = None) -> Dict:
        """
        Esegue tutte le validazioni e ritorna report completo

        Args:
            df: DataFrame da validare
            file_path: Percorso file originale (opzionale)

        Returns:
            Dict con risultati validazione
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {},
        }

        # Livello 1: File (se fornito)
        if file_path:
            file_valid, file_errors = Validator.validate_file(file_path)
            if not file_valid:
                report['valid'] = False
                report['errors'].extend(file_errors)
                return report

        # Livello 2: Struttura DataFrame
        struct_valid, struct_messages = Validator.validate_dataframe_structure(df)
        if not struct_valid:
            report['valid'] = False
            # Separa errors e warnings
            report['errors'].extend([m for m in struct_messages if 'mancant' in m.lower() or 'vuoto' in m.lower()])
            report['warnings'].extend([m for m in struct_messages if m not in report['errors']])
            return report
        else:
            report['warnings'].extend(struct_messages)

        # Livello 3: Business rules
        business_valid, business_warnings, business_stats = Validator.validate_business_rules(df)
        report['warnings'].extend(business_warnings)
        report['stats'] = business_stats

        return report


class DataCleaner:
    """Pulizia e normalizzazione dati"""

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Pulisce e normalizza DataFrame

        Args:
            df: DataFrame grezzo

        Returns:
            DataFrame pulito
        """
        df = df.copy()

        # Rimuovi righe con Codice o Amount NULL
        df = df.dropna(subset=['Codice', 'Amount'])

        # Rimuovi importi zero (opzionale, configurabile)
        # df = df[df['Amount'].abs() >= config.MIN_AMOUNT_VALUE]

        # Normalizza descrizioni
        df['Descrizione'] = df['Descrizione'].fillna('')
        df['Descrizione'] = df['Descrizione'].str.strip()
        df['Descrizione'] = df['Descrizione'].str[:100]  # Max 100 caratteri

        # Normalizza Tipo
        df['Tipo'] = df['Tipo'].fillna('Non Classificato')
        df['Tipo'] = df['Tipo'].str.strip()

        # Normalizza Codice
        df['Codice'] = df['Codice'].astype(str).str.strip()

        # Rimuovi duplicati (mantieni primo)
        df = df.drop_duplicates(subset=['Codice'], keep='first')

        # Ordina per Codice
        df = df.sort_values('Codice').reset_index(drop=True)

        return df
