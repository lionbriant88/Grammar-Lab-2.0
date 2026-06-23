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


# ===================== Task 3: safe_execute wrapper =====================

def test_safe_execute_success():
    """safe_execute returns validator result on success"""
    from grammar_engine.expansion_validator import safe_execute, ValidationReport

    def dummy_validator(sentence, doc, phrases):
        return ValidationReport(severity="PASS", is_valid=True)

    result = safe_execute(dummy_validator, "dummy", "test", None, [])

    assert result.severity == "PASS"
    assert result.is_valid is True


def test_safe_execute_catches_exception():
    """safe_execute catches exception and returns WARNING"""
    from grammar_engine.expansion_validator import safe_execute

    def failing_validator(sentence, doc, phrases):
        raise ValueError("Test error")

    result = safe_execute(failing_validator, "failing_validator", "test", None, [])

    assert result.severity == "WARNING"
    assert result.is_valid is True  # Don't block pipeline
    assert len(result.warnings) == 1
    assert "failing_validator" in result.warnings[0]
    assert "Test error" in result.warnings[0]
    assert len(result.infos) == 1


def test_safe_execute_preserves_args():
    """safe_execute passes args to validator correctly"""
    from grammar_engine.expansion_validator import safe_execute, ValidationReport

    captured = {}

    def capturing_validator(sentence, doc, phrases):
        captured["sentence"] = sentence
        captured["doc"] = doc
        captured["phrases"] = phrases
        return ValidationReport()

    safe_execute(capturing_validator, "test", "my sentence", "my doc", ["my phrases"])

    assert captured["sentence"] == "my sentence"
    assert captured["doc"] == "my doc"
    assert captured["phrases"] == ["my phrases"]
