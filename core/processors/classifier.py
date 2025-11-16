"""
Sistema di classificazione automatica SP/CE con gestione segni
"""
import pandas as pd
import config
import re
from typing import Tuple


class BilancioClassifier:
    """Classificatore automatico per conti contabili"""

    @staticmethod
    def extract_code_prefix(codice: str) -> str:
        """
        Estrae il prefisso (prime due cifre) dal codice conto

        Args:
            codice: Codice conto (es. '01/0001', '40/********')

        Returns:
            Prefisso a 2 cifre (es. '01', '40')
        """
        # Pulisci il codice
        codice = str(codice).strip()

        # Estrai prime due cifre prima dello slash
        match = re.match(r'^(\d{2})', codice)
        if match:
            return match.group(1)

        # Fallback: cerca pattern XX/
        match = re.search(r'(\d{2})/', codice)
        if match:
            return match.group(1)

        return ''

    @staticmethod
    def classify_tipo(codice: str) -> str:
        """
        Classifica un conto in Stato Patrimoniale o Conto Economico

        Args:
            codice: Codice conto

        Returns:
            'Stato Patrimoniale' o 'Conto Economico'
        """
        prefix = BilancioClassifier.extract_code_prefix(codice)

        if not prefix:
            return 'Non Classificato'

        # Stato Patrimoniale: 01-49
        if prefix in config.SP_CODES:
            return 'Stato Patrimoniale'

        # Conto Economico: 50-99
        if prefix in config.CE_CODES:
            return 'Conto Economico'

        return 'Non Classificato'

    @staticmethod
    def determine_sign(codice: str, tipo: str, amount: float) -> float:
        """
        Determina il segno corretto dell'importo

        Logica:
        - SP: Attività (+), Passività e Patrimonio Netto (-)
        - CE: Ricavi (+), Costi (-)

        Args:
            codice: Codice conto
            tipo: 'Stato Patrimoniale' o 'Conto Economico'
            amount: Importo grezzo (sempre positivo dal parsing)

        Returns:
            Importo con segno corretto
        """
        prefix = BilancioClassifier.extract_code_prefix(codice)

        if not prefix:
            return amount

        # Assicurati che amount sia positivo (prendendo valore assoluto)
        amount = abs(amount)

        if tipo == 'Stato Patrimoniale':
            # Fondi ammortamento: negativi
            if prefix in ['04', '07']:
                return -amount

            # Patrimonio Netto: negativo
            if prefix in ['28', '29']:
                return -amount

            # Passività (40-49): negative
            if prefix in config.SP_NEGATIVE_CODES:
                return -amount

            # Attività: positive (default)
            return amount

        elif tipo == 'Conto Economico':
            # Ricavi (80-99): positivi
            if int(prefix) >= 80:
                return amount

            # Costi (50-79): negativi
            if int(prefix) < 80:
                return -amount

        # Default: mantieni positivo
        return amount

    @staticmethod
    def classify_and_sign(df: pd.DataFrame) -> pd.DataFrame:
        """
        Classifica tutti i conti e applica segni corretti

        Args:
            df: DataFrame con colonna 'Codice' e 'Amount'

        Returns:
            DataFrame con colonne 'Tipo' e 'Amount' corretti
        """
        df = df.copy()

        # Classifica tipo
        df['Tipo'] = df['Codice'].apply(BilancioClassifier.classify_tipo)

        # Applica segni (crea nuova colonna temporanea)
        df['Amount_Signed'] = df.apply(
            lambda row: BilancioClassifier.determine_sign(
                row['Codice'],
                row['Tipo'],
                row['Amount']
            ),
            axis=1
        )

        # Sostituisci Amount originale
        df['Amount'] = df['Amount_Signed']
        df = df.drop(columns=['Amount_Signed'])

        return df

    @staticmethod
    def get_classification_stats(df: pd.DataFrame) -> dict:
        """
        Calcola statistiche di classificazione

        Args:
            df: DataFrame classificato

        Returns:
            Dict con statistiche
        """
        stats = {
            'sp': {
                'count': len(df[df['Tipo'] == 'Stato Patrimoniale']),
                'attivita': len(df[(df['Tipo'] == 'Stato Patrimoniale') & (df['Amount'] > 0)]),
                'passivita': len(df[(df['Tipo'] == 'Stato Patrimoniale') & (df['Amount'] < 0)]),
            },
            'ce': {
                'count': len(df[df['Tipo'] == 'Conto Economico']),
                'ricavi': len(df[(df['Tipo'] == 'Conto Economico') & (df['Amount'] > 0)]),
                'costi': len(df[(df['Tipo'] == 'Conto Economico') & (df['Amount'] < 0)]),
            },
            'non_classificati': len(df[df['Tipo'] == 'Non Classificato']),
            'totale': len(df),
        }

        return stats


class ClusterMapper:
    """
    Mapper per Cluster I e II (per futuro sviluppo)
    Attualmente placeholder, sarà implementato nelle prossime versioni
    """

    # Mapping standard italiano (esempio)
    CLUSTER_I_MAPPING = {
        # Attivo
        '01': 'Immobilizzazioni Immateriali',
        '02': 'Immobilizzazioni Immateriali',
        '03': 'Immobilizzazioni Materiali',
        '04': 'Fondi Ammortamento',
        '05': 'Immobilizzazioni Materiali',
        '06': 'Immobilizzazioni Materiali',
        '07': 'Fondi Ammortamento',
        '08': 'Immobilizzazioni Finanziarie',
        '10': 'Rimanenze',
        '11': 'Rimanenze',
        '12': 'Crediti Commerciali',
        '13': 'Crediti Commerciali',
        '20': 'Disponibilità Liquide',
        '21': 'Disponibilità Liquide',

        # Passivo
        '28': 'Patrimonio Netto',
        '29': 'Patrimonio Netto',
        '40': 'Debiti Commerciali',
        '41': 'Debiti Finanziari',
        '42': 'Debiti Tributari',
        '43': 'Debiti Previdenziali',

        # Conto Economico
        '50': 'Costi per Materie Prime',
        '51': 'Costi per Servizi',
        '52': 'Costi per Godimento Beni Terzi',
        '53': 'Costi del Personale',
        '54': 'Ammortamenti',
        '80': 'Ricavi Vendite',
        '81': 'Ricavi Vendite',
        '90': 'Proventi Finanziari',
        '91': 'Oneri Finanziari',
    }

    @staticmethod
    def map_cluster_i(codice: str) -> str:
        """Mappa un codice al Cluster I (placeholder)"""
        prefix = BilancioClassifier.extract_code_prefix(codice)
        return ClusterMapper.CLUSTER_I_MAPPING.get(prefix, '')

    @staticmethod
    def add_cluster_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Aggiunge colonne Cluster I e II (placeholder per v2)"""
        df = df.copy()
        df['Cluster I'] = ''
        df['Cluster II'] = ''
        # In futuro: implementare logica intelligente
        return df
