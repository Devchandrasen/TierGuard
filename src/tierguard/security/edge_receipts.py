"""Signed client receipts and post-commit random edge challenges.

The cloud learns challenged raw plaintext updates.  This module provides
authentication and detection of inconsistent reports, not confidentiality.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import secrets
from dataclasses import asdict, dataclass
from typing import Callable

import torch
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def update_digest(update: torch.Tensor) -> str:
    vector = update.detach().cpu().contiguous().to(torch.float32)
    return hashlib.sha256(vector.numpy().tobytes()).hexdigest()


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class ClientReceipt:
    round: int
    model_hash: str
    client_id: int
    edge_id: int
    sample_mass: int
    update_hash: str
    signature: str

    def payload(self) -> dict:
        content = asdict(self)
        del content["signature"]
        return content


@dataclass(frozen=True)
class EdgeReport:
    round: int
    edge_id: int
    aggregate: torch.Tensor
    receipts: tuple[ClientReceipt, ...]
    commitment: str


def report_commitment(round_idx: int, edge_id: int, aggregate: torch.Tensor,
                      receipts: tuple[ClientReceipt, ...]) -> str:
    content = {
        "round": round_idx,
        "edge_id": edge_id,
        "aggregate_hash": update_digest(aggregate),
        "receipt_hashes": [hashlib.sha256(_canonical(asdict(item))).hexdigest()
                           for item in receipts],
    }
    return hashlib.sha256(_canonical(content)).hexdigest()


class ReceiptAuthority:
    def __init__(self, client_ids: list[int]):
        self._private = {int(client_id): Ed25519PrivateKey.generate()
                         for client_id in client_ids}
        self.public_keys = {
            client_id: private.public_key()
            for client_id, private in self._private.items()
        }
        self._seen: set[tuple[int, int, str]] = set()

    def public_key_bytes(self, client_id: int) -> bytes:
        return self.public_keys[client_id].public_bytes(Encoding.Raw, PublicFormat.Raw)

    def sign(self, *, round_idx: int, model_hash: str, client_id: int, edge_id: int,
             sample_mass: int, update: torch.Tensor) -> ClientReceipt:
        if sample_mass <= 0:
            raise ValueError("Receipt sample mass must be positive")
        payload = {
            "round": int(round_idx), "model_hash": model_hash,
            "client_id": int(client_id), "edge_id": int(edge_id),
            "sample_mass": int(sample_mass), "update_hash": update_digest(update),
        }
        signature = self._private[client_id].sign(_canonical(payload))
        return ClientReceipt(**payload, signature=base64.b64encode(signature).decode("ascii"))

    def verify(self, receipt: ClientReceipt, *, round_idx: int, model_hash: str,
               edge_id: int, update: torch.Tensor) -> None:
        self.verify_signature(receipt, round_idx=round_idx, model_hash=model_hash,
                              edge_id=edge_id)
        if receipt.sample_mass <= 0 or receipt.update_hash != update_digest(update):
            raise ValueError("Receipt has incorrect sample mass or update hash")
        key = (receipt.round, receipt.client_id, receipt.update_hash)
        if key in self._seen:
            raise ValueError("Replayed client receipt")
        self._seen.add(key)

    def verify_signature(self, receipt: ClientReceipt, *, round_idx: int,
                         model_hash: str, edge_id: int) -> None:
        if (receipt.round, receipt.model_hash, receipt.edge_id) != (round_idx, model_hash, edge_id):
            raise ValueError("Receipt has stale or incorrect round, model or edge assignment")
        if receipt.sample_mass <= 0:
            raise ValueError("Receipt has incorrect sample mass")
        public = self.public_keys.get(receipt.client_id)
        if public is None:
            raise ValueError("Unknown client public key")
        try:
            public.verify(base64.b64decode(receipt.signature, validate=True),
                          _canonical(receipt.payload()))
        except (InvalidSignature, ValueError) as exc:
            raise ValueError("Invalid client signature") from exc


def commit_edge(round_idx: int, edge_id: int, aggregate: torch.Tensor,
                receipts: list[ClientReceipt]) -> EdgeReport:
    items = tuple(receipts)
    if len({item.client_id for item in items}) != len(items):
        raise ValueError("An edge report contains duplicate client receipts")
    return EdgeReport(round_idx, edge_id, aggregate.detach().cpu().clone(), items,
                      report_commitment(round_idx, edge_id, aggregate, items))


def choose_challenges(reports: list[EdgeReport], rng=None) -> set[int]:
    edge_ids = sorted({report.edge_id for report in reports})
    if len(edge_ids) != len(reports):
        raise ValueError("Multiple reports from one edge")
    count = math.ceil(len(edge_ids) / 2)
    picker = rng if rng is not None else secrets.SystemRandom()
    return set(picker.sample(edge_ids, count))


def single_report_escape_probability(active_edges: int) -> float:
    """Probability that one forged aggregate is not challenged in one round."""
    if active_edges < 1:
        raise ValueError("At least one edge must be active")
    return (active_edges - math.ceil(active_edges / 2)) / active_edges


def verify_challenged_report(
    report: EdgeReport,
    raw_updates: dict[int, torch.Tensor],
    authority: ReceiptAuthority,
    *,
    round_idx: int,
    model_hash: str,
    recompute: Callable[[list[torch.Tensor], list[int]], torch.Tensor],
    atol: float = 1e-6,
) -> int:
    if report.round != round_idx or report.commitment != report_commitment(
        report.round, report.edge_id, report.aggregate, report.receipts
    ):
        raise ValueError("Missing, replayed or inconsistent edge commitment")
    if set(raw_updates) != {item.client_id for item in report.receipts}:
        raise ValueError("Challenged edge did not reveal exactly the receipted updates")
    updates = []
    masses = []
    for receipt in report.receipts:
        update = raw_updates[receipt.client_id]
        authority.verify(receipt, round_idx=round_idx, model_hash=model_hash,
                         edge_id=report.edge_id, update=update)
        updates.append(update)
        masses.append(receipt.sample_mass)
    expected = recompute(updates, masses).detach().cpu()
    if not torch.allclose(report.aggregate, expected, atol=atol, rtol=0):
        raise ValueError("Challenged edge aggregate does not match signed raw updates")
    # Explicit additional upload, excluding the normal client->edge update path.
    return sum(update.numel() * update.element_size() for update in updates)
