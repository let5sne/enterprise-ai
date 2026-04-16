"""Build a Chroma vector index from local markdown knowledge docs.

Usage:
    python -m app.knowledge.index_builder
    python -m app.knowledge.index_builder --docs-dir data/knowledge_docs --persist-path .chroma
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from app.config import settings
from app.llm.embeddings import EmbeddingClient, get_default_embedding_client

logger = logging.getLogger(__name__)


def iter_markdown_files(docs_dir: Path) -> Iterable[Path]:
    root = docs_dir.resolve()
    files: list[Path] = []
    for p in root.rglob("*.md"):
        if not p.is_file():
            continue
        resolved = p.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        files.append(resolved)
    return sorted(files)


def chunk_markdown(text: str, max_chars: int = 800) -> list[str]:
    """Paragraph-based chunking. First version; tokenized windowing can come later."""
    chunks: list[str] = []
    for para in text.split("\n\n"):
        s = para.strip()
        if not s:
            continue
        if len(s) <= max_chars:
            chunks.append(s)
        else:
            for i in range(0, len(s), max_chars):
                chunks.append(s[i : i + max_chars])
    return chunks


def extract_title(raw: str, fallback: str) -> str:
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def build_index(
    docs_dir: str | Path | None = None,
    persist_path: str | None = None,
    collection_name: str | None = None,
    embedding_client: EmbeddingClient | None = None,
) -> int:
    """(Re)build the collection. Returns total chunks indexed."""
    try:
        import chromadb  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "chromadb is not installed. Run `pip install chromadb` first."
        ) from exc

    docs_path = Path(docs_dir or settings.knowledge_docs_dir).resolve()
    persist = persist_path or settings.vector_db_path
    coll_name = collection_name or settings.knowledge_collection

    if not docs_path.exists():
        raise FileNotFoundError(f"knowledge docs dir not found: {docs_path}")

    embedder = embedding_client or get_default_embedding_client()

    client = chromadb.PersistentClient(path=persist)
    try:
        client.delete_collection(coll_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=coll_name)

    total = 0
    for fp in iter_markdown_files(docs_path):
        raw = fp.read_text(encoding="utf-8")
        title = extract_title(raw, fallback=fp.stem)
        chunks = chunk_markdown(raw)
        if not chunks:
            continue

        try:
            embeddings = embedder.embed(chunks)
        except Exception as exc:
            logger.warning("Embedding failed for %s (%s); skipping file.", fp.name, exc)
            continue

        ids = [f"{fp.stem}:{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "title": title,
                "source_path": str(fp),
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        total += len(chunks)
        logger.info("indexed %s: %d chunks", fp.name, len(chunks))
        print(f"indexed {fp.name}: {len(chunks)} chunks")

    print(f"Done — {total} chunks indexed into '{coll_name}' at {persist}")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Chroma index from knowledge docs")
    parser.add_argument("--docs-dir", default=None, help="markdown docs directory")
    parser.add_argument("--persist-path", default=None, help="Chroma persist path")
    parser.add_argument("--collection", default=None, help="collection name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    build_index(
        docs_dir=args.docs_dir,
        persist_path=args.persist_path,
        collection_name=args.collection,
    )


if __name__ == "__main__":
    main()
