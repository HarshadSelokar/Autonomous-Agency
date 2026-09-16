"""
Deterministic Financial Reconciliation Engine for Phase 23.

Compares internal business transaction records against external provider statements.
Never uses LLM non-determinism as the primary authority for financial reconciliation.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

from src.domain.business import (
    BusinessTransaction,
    Invoice,
    Reconciliation,
    ReconciliationItem,
    ReconciliationStatus,
)
from src.domain.exceptions import ReconciliationMismatchError


class ReconciliationEngine:
    """Deterministic matching and reconciliation engine."""

    def reconcile_records(
        self,
        internal_transactions: List[BusinessTransaction],
        external_statements: List[Dict[str, Any]],
        source_provider: str = "EXTERNAL_BANK",
    ) -> Reconciliation:
        """
        Reconciles internal transactions against external statement records.

        Each external statement entry is expected to contain:
        - external_ref: str
        - amount_cents: int
        - currency: str
        - counterparty: str (optional)
        - date: str or datetime (optional)
        """
        items: List[ReconciliationItem] = []
        total_matched = 0
        total_mismatched = 0

        # Create map of internal transactions by ID and external reference
        internal_map_by_ref: Dict[str, BusinessTransaction] = {}
        for tx in internal_transactions:
            if tx.external_reference:
                internal_map_by_ref[tx.external_reference] = tx
            internal_map_by_ref[tx.id] = tx

        for ext_entry in external_statements:
            ext_ref = ext_entry.get("external_ref") or ext_entry.get("id", str(uuid.uuid4()))
            ext_amount = int(ext_entry.get("amount_cents", 0))
            currency = ext_entry.get("currency", "USD")

            # Match attempt
            internal_tx = internal_map_by_ref.get(ext_ref)
            if not internal_tx:
                # Try matching by amount & counterparty
                counterparty = ext_entry.get("counterparty", "")
                matches = [
                    tx for tx in internal_transactions
                    if tx.amount_cents == ext_amount and tx.currency == currency and (not counterparty or tx.counterparty == counterparty)
                ]
                if len(matches) == 1:
                    internal_tx = matches[0]

            if not internal_tx:
                # Unmatched item
                item = ReconciliationItem(
                    id=str(uuid.uuid4()),
                    internal_ref="UNKNOWN_INTERNAL",
                    external_ref=ext_ref,
                    internal_amount_cents=0,
                    external_amount_cents=ext_amount,
                    currency=currency,
                    status=ReconciliationStatus.MISMATCH,
                    discrepancy_cents=ext_amount,
                    resolution_notes="No matching internal transaction found for external statement entry.",
                )
                items.append(item)
                total_mismatched += ext_amount
            else:
                discrepancy = abs(internal_tx.amount_cents - ext_amount)
                if discrepancy == 0:
                    status = ReconciliationStatus.MATCHED
                    total_matched += ext_amount
                    notes = "Exact amount match."
                else:
                    status = ReconciliationStatus.MISMATCH
                    total_mismatched += discrepancy
                    notes = f"Discrepancy detected: internal {internal_tx.amount_cents} cents vs external {ext_amount} cents."

                item = ReconciliationItem(
                    id=str(uuid.uuid4()),
                    internal_ref=internal_tx.id,
                    external_ref=ext_ref,
                    internal_amount_cents=internal_tx.amount_cents,
                    external_amount_cents=ext_amount,
                    currency=currency,
                    status=status,
                    discrepancy_cents=discrepancy,
                    resolution_notes=notes,
                )
                items.append(item)

        overall_status = ReconciliationStatus.MATCHED if total_mismatched == 0 else ReconciliationStatus.MISMATCH

        return Reconciliation(
            id=str(uuid.uuid4()),
            source_provider=source_provider,
            status=overall_status,
            items=items,
            total_matched_cents=total_matched,
            total_mismatched_cents=total_mismatched,
            conducted_at=datetime.now(UTC),
        )

    def resolve_discrepancy(
        self,
        reconciliation_item: ReconciliationItem,
        resolution_action: str,
        authorized_by: str,
        notes: str,
    ) -> ReconciliationItem:
        """
        Resolves a reconciliation mismatch explicitly with authorization.
        Original financial records are never overwritten silently.
        """
        reconciliation_item.status = ReconciliationStatus.RESOLVED
        reconciliation_item.resolution_notes = (
            f"Resolved by {authorized_by} via action '{resolution_action}': {notes}"
        )
        return reconciliation_item
