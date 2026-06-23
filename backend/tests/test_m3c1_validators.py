"""M3c1 Validation Layer - Unit Tests (80% coverage target)

Tests for ExternalServiceManager, LanguageToolManager, safe_execute, and validators.
"""
import pytest


def test_service_status_creation():
    """ServiceStatus dataclass can be created"""
    from grammar_engine.external_service_manager import ServiceStatus

    status = ServiceStatus(
        available=True,
        message="Service running",
        port=8081
    )

    assert status.available is True
    assert status.message == "Service running"
    assert status.port == 8081


def test_external_service_manager_is_abstract():
    """ExternalServiceManager is abstract and cannot be instantiated"""
    from grammar_engine.external_service_manager import ExternalServiceManager
    import pytest

    with pytest.raises(TypeError):
        ExternalServiceManager()
