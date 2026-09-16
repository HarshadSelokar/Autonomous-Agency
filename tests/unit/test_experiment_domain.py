"""Unit tests for Phase 18 Organizational Experiment domain entity."""

import pytest

from src.domain.experiment import ExperimentStatus, OrganizationalExperiment


def test_organizational_experiment_creation():
    exp = OrganizationalExperiment(
        title="Testing 2x Cache Retention Strategy",
        hypothesis="Increasing cache TTL by 50% reduces model latency by 20%",
        scope="COMPANY",
        risk_level="MEDIUM",
    )
    assert exp.is_isolated is True
    assert exp.status == ExperimentStatus.PROPOSED


def test_organizational_experiment_isolation_invariant():
    with pytest.raises(ValueError, match="strictly isolated"):
        OrganizationalExperiment(
            title="Invalid Non-Isolated Experiment",
            is_isolated=False,
        )
