"""Tiny document store. Firestore when FIRESTORE_DB is set, in-memory otherwise (tests, local runs)."""
from __future__ import annotations

import datetime as dt
import os
import uuid
from typing import Any


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class MemoryStore:
    def __init__(self):
        self._data: dict[str, dict[str, dict]] = {}

    def list(self, collection: str, order_by: str | None = None, **filters: Any) -> list[dict]:
        rows = [dict(r) for r in self._data.get(collection, {}).values()
                if all(r.get(k) == v for k, v in filters.items())]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by.lstrip("-")) or "", reverse=order_by.startswith("-"))
        return rows

    def get(self, collection: str, doc_id: str) -> dict | None:
        r = self._data.get(collection, {}).get(doc_id)
        return dict(r) if r else None

    def create(self, collection: str, data: dict) -> dict:
        doc = {**data, "id": uuid.uuid4().hex[:12], "created_at": _now(), "updated_at": _now()}
        self._data.setdefault(collection, {})[doc["id"]] = doc
        return dict(doc)

    def update(self, collection: str, doc_id: str, data: dict) -> dict | None:
        cur = self._data.get(collection, {}).get(doc_id)
        if not cur:
            return None
        cur.update({**data, "updated_at": _now()})
        return dict(cur)

    def delete(self, collection: str, doc_id: str) -> bool:
        return self._data.get(collection, {}).pop(doc_id, None) is not None


class FirestoreStore:
    def __init__(self, database: str):
        from google.cloud import firestore

        self._db = firestore.Client(database=database)

    def list(self, collection: str, order_by: str | None = None, **filters: Any) -> list[dict]:
        q = self._db.collection(collection)
        for k, v in filters.items():
            q = q.where(k, "==", v)
        rows = [{**d.to_dict(), "id": d.id} for d in q.limit(500).stream()]
        if order_by:
            rows.sort(key=lambda r: r.get(order_by.lstrip("-")) or "", reverse=order_by.startswith("-"))
        return rows

    def get(self, collection: str, doc_id: str) -> dict | None:
        snap = self._db.collection(collection).document(doc_id).get()
        return {**snap.to_dict(), "id": snap.id} if snap.exists else None

    def create(self, collection: str, data: dict) -> dict:
        ref = self._db.collection(collection).document(uuid.uuid4().hex[:12])
        doc = {**data, "created_at": _now(), "updated_at": _now()}
        ref.set(doc)
        return {**doc, "id": ref.id}

    def update(self, collection: str, doc_id: str, data: dict) -> dict | None:
        ref = self._db.collection(collection).document(doc_id)
        if not ref.get().exists:
            return None
        ref.update({**data, "updated_at": _now()})
        return self.get(collection, doc_id)

    def delete(self, collection: str, doc_id: str) -> bool:
        ref = self._db.collection(collection).document(doc_id)
        existed = ref.get().exists
        ref.delete()
        return existed


def make_store():
    database = os.environ.get("FIRESTORE_DB")
    return FirestoreStore(database) if database else MemoryStore()
