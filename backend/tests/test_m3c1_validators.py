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


# ===================== Task 2: LanguageToolManager =====================

def test_lt_report_creation():
    """LTReport dataclass can be created"""
    from grammar_engine.languagetool_manager import LTReport

    report = LTReport(
        success=True,
        matches=[{"message": "test"}],
        error=None,
        timeout=False
    )

    assert report.success is True
    assert report.matches == [{"message": "test"}]
    assert report.error is None
    assert report.timeout is False


def test_languagetool_manager_creation():
    """LanguageToolManager can be instantiated with required params"""
    from grammar_engine.languagetool_manager import LanguageToolManager

    manager = LanguageToolManager(
        jar_path="/path/to/languagetool.jar",
        jre_path="/path/to/jre",
        port=8081
    )

    assert manager.jar_path == "/path/to/languagetool.jar"
    assert manager.jre_path == "/path/to/jre"
    assert manager.port == 8081
    assert manager.process is None


def test_languagetool_manager_is_alive_when_no_process():
    """is_alive returns False when no process exists"""
    from grammar_engine.languagetool_manager import LanguageToolManager

    manager = LanguageToolManager(
        jar_path="/path/to/languagetool.jar",
        jre_path="/path/to/jre",
        port=8081
    )

    assert manager.is_alive() is False


def test_languagetool_manager_singleton():
    """get_languagetool_manager returns singleton instance"""
    from grammar_engine.languagetool_manager import get_languagetool_manager

    manager1 = get_languagetool_manager()
    manager2 = get_languagetool_manager()

    assert manager1 is manager2
