'''
JSON-file-backed database for the knowledge base.
Loads all .json files from a data directory into memory for querying.
'''

import os
import json
import glob
from typing import Dict, List, Any, Optional

import numpy as np
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Handles database operations backed by JSON files on disk."""

    def __init__(
        self,
        data_dir: str = os.getenv('DATA_DIR'),
        logger=None,
        **kwargs
    ):
        self.logger = logger
        self.data_dir = data_dir
        self._documents = {}  # id -> doc dict
        self._next_id = 1
        self._id_to_filepath = {}  # id -> file path on disk
        self._load_all()

    def _load_all(self) -> None:
        """Walk data_dir, load all .json files into memory."""
        if not self.data_dir or not os.path.isdir(self.data_dir):
            self.logger.warning(f"Data directory not found or not set: {self.data_dir}")
            return

        json_files = sorted(glob.glob(os.path.join(self.data_dir, '**', '*.json'), recursive=True))
        for filepath in json_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                doc_id = self._next_id
                self._next_id += 1
                doc = self._make_doc(doc_id, data)
                self._documents[doc_id] = doc
                self._id_to_filepath[doc_id] = filepath
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load {filepath}: {e}")

        if self.logger:
            self.logger.info(f"Loaded {len(self._documents)} documents from {self.data_dir}")

    def _make_doc(self, doc_id: int, data: dict) -> dict:
        """Create a standardized document dict from raw JSON data."""
        return {
            'id': doc_id,
            'url': data.get('url'),
            'type': data.get('type'),
            'timestamp': data.get('timestamp'),
            'content': data.get('content'),
            'summary': data.get('summary'),
            'embeddings': data.get('embeddings'),
            'obsidian_markdown': data.get('obsidian_markdown'),
            'keywords': data.get('keywords', []),
        }

    def store_content(self, content: Dict[str, Any]) -> str:
        doc_id = self._next_id
        self._next_id += 1
        doc = self._make_doc(doc_id, content)
        self._documents[doc_id] = doc

        # Write JSON file to data_dir
        if self.data_dir:
            timestamp = content.get('timestamp', '')
            filename = f"doc_{doc_id}_{timestamp}.json"
            filepath = os.path.join(self.data_dir, filename)
            raw = {k: v for k, v in content.items()}
            with open(filepath, 'w') as f:
                json.dump(raw, f, indent=4)
            self._id_to_filepath[doc_id] = filepath

        if self.logger:
            self.logger.info("Content stored in database")
        return str(doc_id)

    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        doc_id = int(content_id)
        doc = self._documents.get(doc_id)
        if doc:
            return dict(doc)
        return None

    def search_content(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        results = list(self._documents.values())

        if 'type' in query:
            qtype = query['type']
            results = [d for d in results if d.get('type') == qtype]

        if 'keywords' in query:
            search_kws = {k.lower() for k in query['keywords']}
            results = [
                d for d in results
                if search_kws & {k.lower() for k in (d.get('keywords') or [])}
            ]

        if 'text_search' in query:
            terms = query['text_search'].lower().replace(' & ', ' ').split()
            def matches(d):
                text = ((d.get('content') or '') + ' ' + (d.get('summary') or '')).lower()
                return all(t in text for t in terms)
            results = [d for d in results if matches(d)]

        if 'embedding' in query:
            threshold = query.get('similarity_threshold', 0.8)
            query_emb = np.array(query['embedding'], dtype=np.float32)
            query_norm = np.linalg.norm(query_emb)
            if query_norm > 0:
                filtered = []
                for d in results:
                    emb = d.get('embeddings')
                    if emb:
                        doc_emb = np.array(emb, dtype=np.float32)
                        doc_norm = np.linalg.norm(doc_emb)
                        if doc_norm > 0:
                            sim = np.dot(query_emb, doc_emb) / (query_norm * doc_norm)
                            if sim >= threshold:
                                filtered.append(d)
                results = filtered

        return [dict(d) for d in results[:limit]]

    def find_similar_documents(
        self,
        source_embedding: List[float],
        limit: int = 20,
        exclude_id: int = None
    ) -> List[Dict[str, Any]]:
        source_emb = np.array(source_embedding, dtype=np.float32)
        source_norm = np.linalg.norm(source_emb)
        if source_norm == 0:
            return []

        scored = []
        for doc in self._documents.values():
            if exclude_id and doc['id'] == exclude_id:
                continue
            emb = doc.get('embeddings')
            if not emb:
                continue
            doc_emb = np.array(emb, dtype=np.float32)
            doc_norm = np.linalg.norm(doc_emb)
            if doc_norm == 0:
                continue
            similarity = float(np.dot(source_emb, doc_emb) / (source_norm * doc_norm))
            # pgvector uses cosine distance (1 - similarity), keep same interface
            distance = 1.0 - similarity
            scored.append((distance, doc))

        scored.sort(key=lambda x: x[0])
        results = []
        for distance, doc in scored[:limit]:
            d = dict(doc)
            d['similarity_distance'] = distance
            results.append(d)
        return results

    def update_content(
        self,
        content_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        doc_id = int(content_id)
        doc = self._documents.get(doc_id)
        if not doc:
            return False

        for key, value in updates.items():
            if key in doc:
                doc[key] = value

        # Write updated JSON to disk
        filepath = self._id_to_filepath.get(doc_id)
        if filepath and os.path.exists(filepath):
            raw = {k: v for k, v in doc.items() if k not in ('id', 'similarity_distance')}
            with open(filepath, 'w') as f:
                json.dump(raw, f, indent=4)

        return True

    def delete_content(self, content_id: str) -> bool:
        doc_id = int(content_id)
        if doc_id not in self._documents:
            return False

        del self._documents[doc_id]

        filepath = self._id_to_filepath.pop(doc_id, None)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        return True

    def close(self) -> None:
        """No-op for JSON file backend."""
        pass
