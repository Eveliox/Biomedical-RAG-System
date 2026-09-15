"""Small curated list of human gene symbols we scan for.

Same idea as the frontend's genes.ts — a static allowlist keeps runtime
cheap. Swap for a real biomedical NER model (scispaCy `en_ner_bionlp13cg_md`
or GNormPlus) later when we need recall on rarer symbols.
"""
from __future__ import annotations

import re

GENES: list[str] = [
    "KRAS", "NRAS", "HRAS", "TP53", "SMAD4", "CDKN2A", "BRCA1", "BRCA2",
    "PALB2", "ATM", "MLH1", "MSH2", "MSH6", "PMS2", "STK11", "RNF43",
    "ARID1A", "GNAS", "PIK3CA", "ERBB2", "PGR", "ESR1", "HER2", "CDH1",
    "PTEN", "AKT1", "EGFR", "ALK", "ROS1", "MET", "RET", "KEAP1", "BRAF",
    "APC", "JAK2", "FLT3", "NPM1", "IDH1", "IDH2", "DNMT3A", "TET2",
    "MGMT", "TERT", "ATRX", "H3F3A", "NF1", "CDK4", "MYC", "MYCN", "RB1",
    "BCL2", "MDM2", "CTNNB1", "NOTCH1", "FGFR1", "FGFR2", "FGFR3", "MTOR",
    "STAT3", "STAT5", "SRC", "ABL1", "PARP1", "PARP2", "PDCD1", "CTLA4",
    "LAG3", "TIGIT",
]

_UNIQUE = sorted(set(GENES), key=len, reverse=True)
_PATTERN = re.compile(r"\b(" + "|".join(re.escape(g) for g in _UNIQUE) + r")\b")


def find_genes(text: str) -> list[str]:
    """Return every gene symbol (with duplicates preserved) found in `text`."""
    return _PATTERN.findall(text or "")
