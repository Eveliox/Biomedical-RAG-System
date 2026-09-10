"""Prompt construction for the RAG /ask endpoint.

The whole point of RAG is to *constrain* the model to the supplied context.
The system rules below spell that out. Numbered SOURCE blocks let the model
cite [1], [2], [3] — the numbers map back to the same-index entry in the
`sources` array we return to the frontend.
"""
from __future__ import annotations

from dataclasses import dataclass


SYSTEM_RULES = """You are a biomedical literature research assistant.

Answer the user's question using ONLY the provided research context below.

Rules:
1. Do not invent facts. If the supplied sources don't cover something, say so.
2. Every important biomedical claim must be supported by a citation like [1] or [2].
3. Citation numbers correspond to the SOURCE blocks below — do not invent new numbers.
4. Distinguish association from causation ("associated with" ≠ "causes").
5. Do not claim a study "proves" something unless the source says so.
6. Do not give personalized medical advice, diagnosis, dosage, or treatment plans.
7. Keep the answer concise and scientific. A well-informed reader outside biomedicine
   should be able to follow it.
"""


@dataclass
class ContextChunk:
    """One retrieved chunk, ready to be inserted into the prompt as a SOURCE block."""
    citation_number: int   # 1-based; matches [N] in the answer
    pmid: str
    title: str
    text: str


def format_context_block(chunk: ContextChunk) -> str:
    return (
        f"SOURCE [{chunk.citation_number}]\n"
        f"PMID: {chunk.pmid}\n"
        f"TITLE: {chunk.title}\n"
        f"TEXT:\n{chunk.text}\n"
    )


def build_rag_prompt(question: str, chunks: list[ContextChunk]) -> str:
    """Assemble the full prompt sent to the LLM."""
    context = "\n\n".join(format_context_block(c) for c in chunks) or "(no sources)"
    return (
        f"{SYSTEM_RULES}\n"
        f"---\n"
        f"CONTEXT:\n\n{context}\n"
        f"---\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER (cite sources like [1], [2] where relevant):"
    )
