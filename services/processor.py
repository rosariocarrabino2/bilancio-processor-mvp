"""
Processor intelligente per estrarre dati strutturati dai bilancini
Utilizza OpenAI GPT per interpretare formati diversi
"""

import json
import logging
from typing import Dict, List, Any
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)


class BilancioProcessor:
    """Processore intelligente per bilancini di verifica"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def extract_bilancino(self, parsed_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Estrae il bilancino pulito dai dati parsati usando AI

        Args:
            parsed_data: Dati grezzi dal parser

        Returns:
            Lista di dict con: codice_conto, descrizione, tipo_voce, importo
        """
        logger.info("Inizio estrazione bilancino con AI")

        # Prepara il prompt per l'AI
        prompt = self._build_extraction_prompt(parsed_data)

        try:
            # Chiamata a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Bassa temperatura per output deterministico
                response_format={"type": "json_object"}
            )

            # Estrai e valida risposta
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            bilancino = result.get('bilancino', [])
            logger.info(f"Estratti {len(bilancino)} conti dal bilancino")

            return bilancino

        except Exception as e:
            logger.error(f"Errore nell'estrazione AI: {e}")
            raise

    def _get_system_prompt(self) -> str:
        """Prompt di sistema per l'AI"""
        return """Sei un esperto contabile specializzato nell'analisi di bilancini di verifica.

Il tuo compito è estrarre da documenti contabili (PDF o Excel) un bilancino di verifica pulito e strutturato.

STRUTTURA OUTPUT:
Devi restituire un JSON con questa struttura:
{
  "bilancino": [
    {
      "codice_conto": "string",
      "descrizione": "string",
      "tipo_voce": "SP" o "CE",
      "importo": "number"
    }
  ]
}

REGOLE:
1. **codice_conto**: Il codice del conto contabile (es: "1010", "2.01.01", "A.I.1")
2. **descrizione**: La descrizione del conto (es: "Immobilizzazioni materiali", "Ricavi delle vendite")
3. **tipo_voce**: Classifica come:
   - "SP" per voci di Stato Patrimoniale (Attivo, Passivo, Patrimonio Netto)
   - "CE" per voci di Conto Economico (Ricavi, Costi, etc.)
4. **importo**: L'importo numerico (usa numeri negativi per dare/avere quando appropriato)

IMPORTANTE:
- Estrai TUTTI i conti presenti
- Ignora righe di totali, subtotali, intestazioni
- Se manca il codice conto, usa un codice progressivo
- Sii preciso nella classificazione SP vs CE
- Converti importi in numero (rimuovi simboli di valuta, separatori, etc.)
"""

    def _build_extraction_prompt(self, parsed_data: Dict[str, Any]) -> str:
        """Costruisce il prompt con i dati da processare"""

        content = parsed_data.get('content', '')
        file_type = parsed_data.get('type', 'unknown')

        prompt = f"""Analizza il seguente bilancino di verifica (formato: {file_type}) ed estrailo in formato strutturato.

DATI DA ANALIZZARE:
{content[:15000]}

Estrai tutti i conti e restituisci il JSON con il bilancino pulito."""

        # Se ci sono tabelle (PDF), aggiungi informazioni
        if 'tables' in parsed_data and parsed_data['tables']:
            prompt += f"\n\nIl documento contiene {len(parsed_data['tables'])} tabelle. Analizza anche quelle."

        return prompt

    def validate_bilancino(self, bilancino: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Valida il bilancino estratto

        Returns:
            Dict con 'valid', 'errors', 'warnings'
        """
        errors = []
        warnings = []

        if not bilancino:
            errors.append("Nessun conto estratto")

        for idx, conto in enumerate(bilancino):
            # Valida campi obbligatori
            if not conto.get('codice_conto'):
                errors.append(f"Riga {idx+1}: manca codice_conto")
            if not conto.get('descrizione'):
                warnings.append(f"Riga {idx+1}: manca descrizione")
            if not conto.get('tipo_voce') or conto['tipo_voce'] not in ['SP', 'CE']:
                errors.append(f"Riga {idx+1}: tipo_voce deve essere 'SP' o 'CE'")
            if 'importo' not in conto:
                errors.append(f"Riga {idx+1}: manca importo")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
