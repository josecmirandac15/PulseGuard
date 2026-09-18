import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent.models import (
    EmergencyAdmission, Policy, Patient, PolicyStatus, AlertLevel
)
from src.services.policy_service import PolicyService


def test_policy_service_load():
    service = PolicyService()
    assert len(service.policies) > 0
    assert len(service.patients) > 0


def test_get_policy():
    service = PolicyService()
    policy = service.get_policy("POL-2024-001")
    assert policy is not None
    assert policy.status == PolicyStatus.ACTIVE


def test_validate_active_policy():
    service = PolicyService()
    policy = service.get_policy("POL-2024-001")
    result = service.validate_policy(policy)
    assert result["valid"] is True


def test_validate_expired_policy():
    service = PolicyService()
    policy = service.get_policy("POL-2024-002")
    result = service.validate_policy(policy)
    assert result["valid"] is False
    assert "expired" in result["reason"].lower()


def test_validate_suspended_policy():
    service = PolicyService()
    policy = service.get_policy("POL-2024-004")
    result = service.validate_policy(policy)
    assert result["valid"] is False
    assert "suspended" in result["reason"].lower()


def test_get_patient():
    service = PolicyService()
    patient = service.get_patient("PAT-001")
    assert patient is not None
    assert patient.name == "Juan Garcia"


def test_check_pre_existences():
    service = PolicyService()
    patient = service.get_patient("PAT-003")
    result = service.check_pre_existences(patient, "chest pain")
    assert result["has_relevant_pre_existences"] is True


def test_check_no_pre_existences():
    service = PolicyService()
    patient = service.get_patient("PAT-004")
    result = service.check_pre_existences(patient, "fracture")
    assert result["has_relevant_pre_existences"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
