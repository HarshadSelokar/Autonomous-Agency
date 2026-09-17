"""
Application engine for Disaster Recovery, RPO/RTO SLA Verification, & Backup Reconciliation (Phase 30).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.domain.exceptions import DisasterRecoveryError
from src.domain.repository import ResilienceRepositoryInterface
from src.domain.resilience import ProductionReadinessItem

logger = logging.getLogger(__name__)


@dataclass
class BackupSnapshot:
    snapshot_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    component_states: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    rpo_minutes: float = 0.0
    is_validated: bool = False


class DisasterRecoveryEngine:
    """Engine orchestrating automated disaster recovery snapshots, SLA validation (RPO < 5m, RTO < 15m), and failover reconciliation."""

    def __init__(self, repository: ResilienceRepositoryInterface) -> None:
        self.repository = repository
        self._snapshots: Dict[str, BackupSnapshot] = {}

    def create_backup_snapshot(self, snapshot_id: str, component_states: Dict[str, Any]) -> BackupSnapshot:
        now = datetime.now(UTC)
        raw_json = json.dumps(component_states, sort_keys=True)
        checksum = hashlib.sha256(f"{snapshot_id}:{raw_json}".encode("utf-8")).hexdigest()

        snapshot = BackupSnapshot(
            snapshot_id=snapshot_id,
            timestamp=now,
            component_states=component_states,
            checksum=checksum,
            rpo_minutes=0.0,
            is_validated=True,
        )
        self._snapshots[snapshot_id] = snapshot
        logger.info(f"Disaster Recovery Snapshot '{snapshot_id}' created with checksum {checksum[:8]}...")
        return snapshot

    def validate_backup_snapshot(self, snapshot_id: str) -> bool:
        if snapshot_id not in self._snapshots:
            raise DisasterRecoveryError(component="DR_CATALOG", reason=f"Snapshot '{snapshot_id}' not found in DR catalog")

        snap = self._snapshots[snapshot_id]
        raw_json = json.dumps(snap.component_states, sort_keys=True)
        expected_checksum = hashlib.sha256(f"{snapshot_id}:{raw_json}".encode("utf-8")).hexdigest()

        if snap.checksum != expected_checksum:
            logger.error(f"Snapshot '{snapshot_id}' checksum corruption detected!")
            snap.is_validated = False
            return False

        snap.is_validated = True
        return True

    async def verify_dr_sla(self, latest_snapshot_timestamp: datetime, recovery_duration_seconds: float) -> Tuple[bool, ProductionReadinessItem]:
        now = datetime.now(UTC)
        if latest_snapshot_timestamp.tzinfo is None:
            latest_snapshot_timestamp = latest_snapshot_timestamp.replace(tzinfo=UTC)

        rpo_seconds = (now - latest_snapshot_timestamp).total_seconds()
        rpo_minutes = rpo_seconds / 60.0
        rto_minutes = recovery_duration_seconds / 60.0

        rpo_passed = rpo_minutes <= 5.0
        rto_passed = rto_minutes <= 15.0
        sla_passed = rpo_passed and rto_passed

        evidence = f"RPO: {rpo_minutes:.2f}m (Threshold: 5.0m, Passed: {rpo_passed}) | RTO: {rto_minutes:.2f}m (Threshold: 15.0m, Passed: {rto_passed})"

        item = ProductionReadinessItem(
            domain="DISASTER_RECOVERY",
            requirement="RPO < 5m and RTO < 15m Verification",
            status="PASSED" if sla_passed else "FAILED",
            evidence_reference=evidence,
        )

        await self.repository.save_readiness_item(item)
        return sla_passed, item

    async def simulate_failover_and_reconcile(self, snapshot_id: str, target_region: str = "PRIMARY_FAILOVER_REGION") -> Dict[str, Any]:
        if not self.validate_backup_snapshot(snapshot_id):
            raise DisasterRecoveryError(component="SNAPSHOT_VALIDATOR", reason=f"Cannot execute failover: snapshot '{snapshot_id}' validation failed")

        snap = self._snapshots[snapshot_id]
        reconciled_components = {}
        for comp_name, state in snap.component_states.items():
            reconciled_components[comp_name] = {
                "status": "RECONCILED",
                "region": target_region,
                "restored_state": state,
                "reconciled_at": datetime.now(UTC).isoformat(),
            }

        logger.info(f"Disaster Recovery failover simulation successful for snapshot '{snapshot_id}' to region '{target_region}'.")
        return {
            "snapshot_id": snapshot_id,
            "target_region": target_region,
            "reconciled_components_count": len(reconciled_components),
            "details": reconciled_components,
        }
