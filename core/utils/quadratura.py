"""
Sistema di quadratura avanzato con report dettagliato
"""
import pandas as pd
import config
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class QuadraturaReport:
    """Report dettagliato della quadratura del bilancio"""

    # Totali
    totale_sp: float
    totale_ce: float
    totale_attivita: float
    totale_passivita: float
    totale_ricavi: float
    totale_costi: float

    # Differenze
    differenza_totale: float
    differenza_sp: float
    differenza_ce: float

    # Tolleranza
    tolleranza_usata: float
    tolleranza_tipo: str  # 'absolute', 'relative', 'dynamic'

    # Status
    quadra: bool
    quadra_sp: bool
    quadra_ce: bool

    # Dettagli
    num_conti_sp: int
    num_conti_ce: int
    num_conti_totali: int

    # Warnings
    warnings: List[str]
    details: Dict

    def to_dict(self):
        """Converte in dizionario per JSON"""
        return {
            'totali': {
                'sp': round(self.totale_sp, 2),
                'ce': round(self.totale_ce, 2),
                'attivita': round(self.totale_attivita, 2),
                'passivita': round(self.totale_passivita, 2),
                'ricavi': round(self.totale_ricavi, 2),
                'costi': round(self.totale_costi, 2),
            },
            'differenze': {
                'totale': round(self.differenza_totale, 2),
                'sp': round(self.differenza_sp, 2),
                'ce': round(self.differenza_ce, 2),
            },
            'status': {
                'quadra': self.quadra,
                'quadra_sp': self.quadra_sp,
                'quadra_ce': self.quadra_ce,
            },
            'tolleranza': {
                'valore': round(self.tolleranza_usata, 2),
                'tipo': self.tolleranza_tipo,
            },
            'conti': {
                'sp': self.num_conti_sp,
                'ce': self.num_conti_ce,
                'totali': self.num_conti_totali,
            },
            'warnings': self.warnings,
            'details': self.details,
        }

    def format_text(self):
        """Formatta report in formato testo leggibile"""
        icon = "✅" if self.quadra else "❌"
        lines = [
            f"\n{'='*70}",
            f"REPORT QUADRATURA {icon}",
            f"{'='*70}",
            "",
            "STATO PATRIMONIALE:",
            f"  Attività:     {self.totale_attivita:>15,.2f} €",
            f"  Passività:    {self.totale_passivita:>15,.2f} €",
            f"  Differenza:   {self.differenza_sp:>15,.2f} € {'✅' if self.quadra_sp else '❌'}",
            "",
            "CONTO ECONOMICO:",
            f"  Ricavi:       {self.totale_ricavi:>15,.2f} €",
            f"  Costi:        {self.totale_costi:>15,.2f} €",
            f"  Differenza:   {self.differenza_ce:>15,.2f} € {'✅' if self.quadra_ce else '❌'}",
            "",
            "QUADRATURA GENERALE:",
            f"  Totale SP:    {self.totale_sp:>15,.2f} €",
            f"  Totale CE:    {self.totale_ce:>15,.2f} €",
            f"  Differenza:   {self.differenza_totale:>15,.2f} €",
            f"  Tolleranza:   {self.tolleranza_usata:>15,.2f} € ({self.tolleranza_tipo})",
            f"  Status:       {'QUADRA ✅' if self.quadra else 'NON QUADRA ❌'}",
            "",
            f"Conti: {self.num_conti_totali} totali ({self.num_conti_sp} SP, {self.num_conti_ce} CE)",
        ]

        if self.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for w in self.warnings:
                lines.append(f"  ⚠️  {w}")

        lines.append(f"{'='*70}\n")

        return '\n'.join(lines)


class QuadraturaChecker:
    """Sistema di verifica quadratura con logica avanzata"""

    @staticmethod
    def calcola_tolleranza(df: pd.DataFrame, tipo: str = 'dynamic') -> float:
        """
        Calcola tolleranza dinamica basata sui dati

        Args:
            df: DataFrame con i dati del bilancio
            tipo: 'absolute', 'relative', 'dynamic'

        Returns:
            Tolleranza in euro
        """
        if tipo == 'absolute':
            return config.QUADRATURA_TOLERANCE_ABSOLUTE

        elif tipo == 'relative':
            totale_attivita = df[df['Amount'] > 0]['Amount'].sum()
            return totale_attivita * config.QUADRATURA_TOLERANCE_RELATIVE

        else:  # dynamic
            totale_attivita = df[df['Amount'] > 0]['Amount'].sum()
            tol_relative = totale_attivita * config.QUADRATURA_TOLERANCE_RELATIVE
            return max(config.QUADRATURA_TOLERANCE_ABSOLUTE, tol_relative)

    @staticmethod
    def verifica_quadratura(df: pd.DataFrame, tolleranza: Optional[float] = None) -> QuadraturaReport:
        """
        Verifica la quadratura del bilancio con analisi dettagliata

        Args:
            df: DataFrame con colonne ['Codice', 'Descrizione', 'Tipo', 'Amount']
            tolleranza: Tolleranza manuale, se None usa dinamica

        Returns:
            QuadraturaReport con tutti i dettagli
        """
        warnings = []

        # Separa SP e CE
        df_sp = df[df['Tipo'] == 'Stato Patrimoniale'].copy()
        df_ce = df[df['Tipo'] == 'Conto Economico'].copy()

        # Check dati vuoti
        if df.empty:
            warnings.append("Nessun dato presente")
            return QuadraturaReport(
                totale_sp=0, totale_ce=0, totale_attivita=0, totale_passivita=0,
                totale_ricavi=0, totale_costi=0, differenza_totale=0,
                differenza_sp=0, differenza_ce=0, tolleranza_usata=0,
                tolleranza_tipo='none', quadra=False, quadra_sp=False,
                quadra_ce=False, num_conti_sp=0, num_conti_ce=0,
                num_conti_totali=0, warnings=warnings, details={}
            )

        # Calcola totali SP
        totale_attivita = df_sp[df_sp['Amount'] > 0]['Amount'].sum()
        totale_passivita = abs(df_sp[df_sp['Amount'] < 0]['Amount'].sum())
        totale_sp = df_sp['Amount'].sum()
        differenza_sp = totale_attivita - totale_passivita

        # Calcola totali CE
        totale_ricavi = df_ce[df_ce['Amount'] > 0]['Amount'].sum()
        totale_costi = abs(df_ce[df_ce['Amount'] < 0]['Amount'].sum())
        totale_ce = df_ce['Amount'].sum()
        differenza_ce = totale_ricavi - totale_costi

        # Differenza totale (SP + CE dovrebbe fare 0)
        differenza_totale = abs(totale_sp + totale_ce)

        # Calcola tolleranza
        if tolleranza is None:
            if config.USE_DYNAMIC_TOLERANCE:
                tolleranza = QuadraturaChecker.calcola_tolleranza(df, 'dynamic')
                tol_tipo = 'dynamic'
            else:
                tolleranza = config.QUADRATURA_TOLERANCE_ABSOLUTE
                tol_tipo = 'absolute'
        else:
            tol_tipo = 'manual'

        # Verifica quadratura
        quadra_sp = abs(differenza_sp) <= tolleranza
        quadra_ce = abs(differenza_ce) <= tolleranza
        quadra_totale = differenza_totale <= tolleranza

        # Warnings
        if not quadra_sp:
            warnings.append(f"Stato Patrimoniale non quadra: {differenza_sp:.2f}€")

        if not quadra_ce:
            warnings.append(f"Conto Economico non quadra: {differenza_ce:.2f}€")

        if not quadra_totale:
            warnings.append(f"Quadratura generale non rispettata: {differenza_totale:.2f}€")

        # Check conti senza classificazione
        conti_senza_tipo = df[df['Tipo'].isna() | (df['Tipo'] == '')].shape[0]
        if conti_senza_tipo > 0:
            warnings.append(f"{conti_senza_tipo} conti senza classificazione SP/CE")

        # Check conti con amount = 0
        conti_zero = df[df['Amount'] == 0].shape[0]
        if conti_zero > 0:
            warnings.append(f"{conti_zero} conti con importo zero")

        # Details aggiuntivi
        details = {
            'sp_breakdown': {
                'attivita': {
                    'totale': round(totale_attivita, 2),
                    'num_conti': int(df_sp[df_sp['Amount'] > 0].shape[0]),
                },
                'passivita': {
                    'totale': round(totale_passivita, 2),
                    'num_conti': int(df_sp[df_sp['Amount'] < 0].shape[0]),
                },
            },
            'ce_breakdown': {
                'ricavi': {
                    'totale': round(totale_ricavi, 2),
                    'num_conti': int(df_ce[df_ce['Amount'] > 0].shape[0]),
                },
                'costi': {
                    'totale': round(totale_costi, 2),
                    'num_conti': int(df_ce[df_ce['Amount'] < 0].shape[0]),
                },
            },
        }

        return QuadraturaReport(
            totale_sp=totale_sp,
            totale_ce=totale_ce,
            totale_attivita=totale_attivita,
            totale_passivita=totale_passivita,
            totale_ricavi=totale_ricavi,
            totale_costi=totale_costi,
            differenza_totale=differenza_totale,
            differenza_sp=differenza_sp,
            differenza_ce=differenza_ce,
            tolleranza_usata=tolleranza,
            tolleranza_tipo=tol_tipo,
            quadra=quadra_totale,
            quadra_sp=quadra_sp,
            quadra_ce=quadra_ce,
            num_conti_sp=len(df_sp),
            num_conti_ce=len(df_ce),
            num_conti_totali=len(df),
            warnings=warnings,
            details=details,
        )
