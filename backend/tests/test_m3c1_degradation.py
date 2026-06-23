"""M3c1 Degradation Tests (15%, highest priority)

Critical degradation scenarios ensuring zero crashes and graceful degradation.
"""
import pytest
from unittest.mock import patch, MagicMock


def test_languagetool_server_not_started():
    """LanguageTool not started, system continues, HTTP 200"""
    from grammar_engine.expansion_validator import validate_with_languagetool

    # LanguageTool not available (default state in tests)
    result = validate_with_languagetool("He go to school.")

    # System continues with INFO severity
    assert result.severity in ["INFO", "PASS"]
    assert result.is_valid is True
    assert any("LanguageTool" in info or "languagetool" in info.lower() for info in result.infos)


def test_languagetool_server_timeout():
    """LanguageTool timeout, system continues, HTTP 200"""
    from grammar_engine.expansion_validator import validate_with_languagetool
    from grammar_engine.languagetool_manager import LTReport

    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = True
    mock_manager.check.return_value = LTReport(
        success=False,
        matches=[],
        error="Request timeout",
        timeout=True
    )

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate_with_languagetool("Test sentence.")

    # System continues with INFO severity
    assert result.severity == "INFO"
    assert result.is_valid is True
    assert any("超时" in info or "timeout" in info.lower() for info in result.infos)


def test_languagetool_server_crash_during_request():
    """LanguageTool crashes mid-request, system continues, HTTP 200"""
    from grammar_engine.expansion_validator import validate_with_languagetool

    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = True
    mock_manager.check.side_effect = Exception("Server crashed")

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate_with_languagetool("Test sentence.")

    # System continues with INFO severity (exception caught)
    assert result.severity == "INFO"
    assert result.is_valid is True


def test_validator_exception_does_not_stop_pipeline():
    """Single validator exception doesn't stop pipeline"""
    from grammar_engine.expansion_validator import validate

    def failing_validator(sentence, doc, phrases):
        raise RuntimeError("Validator crashed")

    with patch('grammar_engine.expansion_validator.validate_subject_verb_agreement', failing_validator):
        result = validate("Test sentence.", None, [])

    # Pipeline continues, safe_execute catches exception
    assert result.severity in ["WARNING", "INFO", "PASS"]
    assert result.is_valid is True
    assert any("subject_verb_agreement" in w for w in result.warnings)


def test_all_validators_fail_gracefully():
    """All validators fail, still HTTP 200"""
    from grammar_engine.expansion_validator import validate

    def failing_validator(*args, **kwargs):
        raise RuntimeError("All validators failed")

    with patch('grammar_engine.expansion_validator.validate_subject_verb_agreement', failing_validator):
        with patch('grammar_engine.expansion_validator.validate_tense_consistency', failing_validator):
            with patch('grammar_engine.expansion_validator.validate_clause_completeness', failing_validator):
                with patch('grammar_engine.expansion_validator.validate_non_finite_legality', failing_validator):
                    with patch('grammar_engine.expansion_validator.validate_relative_pronoun_match', failing_validator):
                        with patch('grammar_engine.expansion_validator.validate_with_languagetool', failing_validator):
                            result = validate("Test.", None, [])

    # System continues (all failures caught by safe_execute)
    assert result.severity == "WARNING"  # All failures → WARNING
    assert result.is_valid is True
    assert len(result.warnings) == 6  # One warning per failed validator


def test_languagetool_check_returns_error():
    """LanguageTool check returns error, system continues"""
    from grammar_engine.expansion_validator import validate_with_languagetool
    from grammar_engine.languagetool_manager import LTReport

    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = True
    mock_manager.check.return_value = LTReport(
        success=False,
        matches=[],
        error="Connection refused",
        timeout=False
    )

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate_with_languagetool("Test.")

    assert result.severity == "INFO"
    assert result.is_valid is True
    assert any("失败" in info or "Connection refused" in info for info in result.infos)


def test_languagetool_restart_after_crash():
    """LanguageTool can restart after crash"""
    from grammar_engine.languagetool_manager import LanguageToolManager

    manager = LanguageToolManager(
        jar_path="/fake/path.jar",
        jre_path="/fake/jre",
        port=8081
    )

    # Simulate crash
    manager.process = MagicMock()
    manager.process.poll.return_value = 1  # Process terminated

    assert manager.is_alive() is False

    # Restart should not crash
    manager.restart()

    # Should have attempted restart (new thread started)
    assert manager._startup_thread is not None
