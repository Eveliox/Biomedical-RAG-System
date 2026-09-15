// A small curated set of human gene symbols we highlight in answers and
// snippets. Not exhaustive — a proper implementation would call the NCBI
// gene API or use scispaCy — but a static allowlist is enough for demo
// quality and has zero runtime cost.
//
// Symbols follow HGNC conventions: uppercase letters and digits, no spaces.
// We match whole words only (word boundaries) so "AKTA" doesn't get lit up
// when we're looking for "AKT".

export const GENE_SYMBOLS: string[] = [
  // pancreatic / GI oncology
  "KRAS", "NRAS", "HRAS", "TP53", "SMAD4", "CDKN2A", "BRCA1", "BRCA2",
  "PALB2", "ATM", "MLH1", "MSH2", "MSH6", "PMS2", "STK11", "RNF43",
  "ARID1A", "GNAS", "PIK3CA",
  // breast / gyn
  "ERBB2", "PGR", "ESR1", "HER2", "CDH1", "PTEN", "AKT1",
  // lung
  "EGFR", "ALK", "ROS1", "MET", "RET", "KEAP1", "STK11", "BRAF",
  // colorectal
  "APC", "KRAS", "NRAS", "BRAF", "PIK3CA", "MLH1", "MSH2",
  // hematologic
  "JAK2", "FLT3", "NPM1", "IDH1", "IDH2", "DNMT3A", "TET2",
  // brain / glioma
  "IDH1", "IDH2", "MGMT", "TERT", "ATRX", "H3F3A",
  // melanoma
  "BRAF", "NRAS", "NF1", "CDK4",
  // general onco / TSGs / signaling
  "MYC", "MYCN", "PTEN", "RB1", "BCL2", "MDM2", "CTNNB1", "NOTCH1",
  "FGFR1", "FGFR2", "FGFR3", "MTOR", "STAT3", "STAT5", "SRC", "ABL1",
  // repair pathways / checkpoints
  "PARP1", "PARP2", "PD-L1", "PDCD1", "CTLA4", "LAG3", "TIGIT",
];

// De-dupe while preserving the reading order above.
const UNIQUE = Array.from(new Set(GENE_SYMBOLS));

// Alphabetical, longest-first so overlapping matches favor the longer symbol
// (e.g. HER2 wins over HER when both are candidates — though HER isn't in
// the list, the pattern still uses word boundaries).
const SORTED = [...UNIQUE].sort((a, b) => b.length - a.length);

export const GENE_REGEX = new RegExp(
  `\\b(${SORTED.map(escapeRe).join("|")})\\b`,
  "g",
);

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function isGeneSymbol(word: string): boolean {
  return UNIQUE.includes(word);
}
