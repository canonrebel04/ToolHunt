"""Build (or verify) the FAISS index for the current tools.db.

    python -m backend.build_index [--force]

Used by the Docker build so containers start with a fresh index instead of
embedding every tool on the first request.
"""
import argparse
import logging


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="rebuild even if the index looks fresh")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from backend import db
    from backend.hybrid_search import build_or_load_faiss_index
    from backend.indexing import index_text

    conn = db.connect()
    try:
        docs = [index_text(t) for t in db.load_tools(conn)]
    finally:
        conn.close()
    build_or_load_faiss_index(docs, force_rebuild=args.force)
    print(f"FAISS index ready for {len(docs)} tools")


if __name__ == "__main__":
    main()
