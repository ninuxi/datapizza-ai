from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    from pypdf import PdfReader
except Exception as e:  # pragma: no cover
    PdfReader = None


@dataclass
class RAGConfig:
    corpus_dir: Path
    index_dir: Path
    chunk_size: int = 1200
    chunk_overlap: int = 200


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    page: int | None = None


class RecipeIndexer:
    def __init__(self, config: RAGConfig):
        self.config = config
        self.embeddings: np.ndarray | None = None
        self.metadata: List[Dict[str, Any]] = []
        self._loaded = False

    # --- Public API ---
    def ensure_index(self) -> None:
        if not self._index_exists():
            self.build_index()
        else:
            self.load_index()

    def build_index(self) -> None:
        self.config.index_dir.mkdir(parents=True, exist_ok=True)
        texts, metas = self._load_corpus()
        if not texts:
            # No docs; create empty index
            self.embeddings = np.zeros((0, 384), dtype=np.float32)
            self.metadata = []
            self._save_index()
            self._loaded = True
            return
        embeddings = self._embed_texts(texts)
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        embeddings = embeddings / norms
        self.embeddings = embeddings.astype(np.float32)
        self.metadata = metas
        self._save_index()
        self._loaded = True

    def load_index(self) -> None:
        idx = self.config.index_dir
        emb_path = idx / "embeddings.npy"
        meta_path = idx / "metadata.json"
        if emb_path.exists() and meta_path.exists():
            self.embeddings = np.load(emb_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            self._loaded = True
        else:
            self._loaded = False

    def search(self, query: str, top_k: int = 6) -> List[RetrievedChunk]:
        if not self._loaded:
            self.ensure_index()
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        q_emb = self._embed_texts([query])[0]
        q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-12)
        scores = np.dot(self.embeddings, q_emb)
        top_idx = np.argsort(-scores)[:top_k]
        results: List[RetrievedChunk] = []
        for i in top_idx:
            meta = self.metadata[int(i)]
            results.append(
                RetrievedChunk(
                    text=meta["text"],
                    score=float(scores[int(i)]),
                    source=meta.get("source", ""),
                    page=meta.get("page"),
                )
            )
        return results

    # --- Internals ---
    def _index_exists(self) -> bool:
        idx = self.config.index_dir
        return (idx / "embeddings.npy").exists() and (idx / "metadata.json").exists()

    def _save_index(self) -> None:
        assert self.embeddings is not None
        idx = self.config.index_dir
        np.save(idx / "embeddings.npy", self.embeddings)
        with open(idx / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)
        with open(idx / "model.json", "w", encoding="utf-8") as f:
            json.dump({"embedder": "fastembed/gte-small", "dim": int(self.embeddings.shape[1])}, f)

    def _load_corpus(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        texts: List[str] = []
        metas: List[Dict[str, Any]] = []
        corpus = self.config.corpus_dir
        pdfs = sorted(corpus.glob("**/*.pdf"))
        for pdf in pdfs:
            try:
                if PdfReader is None:
                    raise RuntimeError("pypdf non installato")
                reader = PdfReader(str(pdf))
                for page_num, page in enumerate(reader.pages, start=1):
                    raw = page.extract_text() or ""
                    for chunk in self._chunk_text(raw):
                        texts.append(chunk)
                        metas.append({"source": str(pdf.name), "page": page_num, "text": chunk})
            except Exception:
                # Skip unreadable PDFs but continue indexing others
                continue
        return texts, metas

    def _chunk_text(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + size)
            chunk = text[start:end]
            chunk = " ".join(chunk.split())  # normalize whitespace
            if len(chunk) > 50:
                chunks.append(chunk)
            if end == len(text):
                break
            start = end - overlap
        return chunks

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        # Lazy import to speed initial module import
        try:
            from fastembed import TextEmbedding
        except Exception as e:  # pragma: no cover
            raise RuntimeError("fastembed non installato. Aggiungi 'fastembed' ai requirements.") from e

        # Modello supportato da fastembed; compatto e multilingua
        # Nota: per l'elenco completo dei modelli supportati usa
        #   from fastembed import TextEmbedding; print(TextEmbedding.list_supported_models())
        try:
            embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except Exception:
            # Fallback automatico al primo modello disponibile
            try:
                available_models = TextEmbedding.list_supported_models()
                # list_supported_models() restituisce una lista di dict con chiave "model"
                if isinstance(available_models, list) and available_models:
                    # Estrai il nome del primo modello
                    first_model = available_models[0]
                    if isinstance(first_model, dict):
                        fallback = first_model.get("model")
                    else:
                        fallback = str(first_model)
                else:
                    fallback = None
            except Exception:
                fallback = None
            
            if not fallback:
                raise RuntimeError("Nessun modello fastembed disponibile. Verifica l'installazione di fastembed e i modelli supportati.")
            embedder = TextEmbedding(model_name=fallback)
        # fastembed returns list of vectors
        vectors = list(embedder.embed(texts))
        arr = np.array(vectors, dtype=np.float32)
        return arr
