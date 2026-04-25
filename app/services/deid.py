import re
from collections import Counter
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from loguru import logger

_ENTITY_TO_REPLACEMENT: dict[str, str] = {
    "PERSON": "[PATIENT]",
    "DATE_TIME": "[DATE]",
    "LOCATION": "[ADDRESS]",
    "PHONE_NUMBER": "[PHONE]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "MEDICAL_LICENSE": "[MEDICAL_ID]",
    "UK_NHS": "[MEDICAL_ID]",
    "US_SSN": "[MEDICAL_ID]",
    "MRN": "[MEDICAL_ID]",
}

_MRN_PATTERN = Pattern(name="mrn_pattern", regex=r"MRN[\s:-]{0,2}\d{6,10}", score=0.9)
_MRN_RECOGNISER = PatternRecognizer(supported_entity="MRN", patterns=[_MRN_PATTERN])

# Presidio's built-in US_SSN recognizer uses heuristics that reject many valid-format SSNs.
# Add a custom pattern recognizer based purely on format (NNN-NN-NNNN).
_SSN_PATTERN = Pattern(name="ssn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=0.85)
_SSN_RECOGNISER = PatternRecognizer(supported_entity="US_SSN", patterns=[_SSN_PATTERN])

_analyser = AnalyzerEngine()
_analyser.registry.add_recognizer(_MRN_RECOGNISER)
_analyser.registry.add_recognizer(_SSN_RECOGNISER)
_anonymiser = AnonymizerEngine()

_ENTITIES = list(_ENTITY_TO_REPLACEMENT.keys())


def deidentify(text: str) -> tuple[str, list[dict], bool]:
    """
    Returns (anonymised_text, entity_list, deid_failed).
    deid_failed=True if text is empty or an exception occurs — caller must abort pipeline.
    """
    if not text.strip():
        return text, [], True

    try:
        results = _analyser.analyze(text=text, entities=_ENTITIES, language="en")

        operators = {
            entity: OperatorConfig("replace", {"new_value": replacement})
            for entity, replacement in _ENTITY_TO_REPLACEMENT.items()
        }

        anonymised = _anonymiser.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        counts: Counter[str] = Counter()
        for result in results:
            counts[result.entity_type] += 1
            logger.warning(
                "deid_entity_removed",
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                score=result.score,
            )

        entities = [{"type": entity_type, "count": count} for entity_type, count in counts.items()]
        return anonymised.text, entities, False

    except Exception as exc:
        logger.error("deid_failed", error=str(exc))
        return "", [], True
