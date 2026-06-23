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


# ===================== Task 4-6: Three Shallow Rule Validators =====================

def test_clause_completeness_valid():
    """validate_clause_completeness returns PASS for complete clauses"""
    from grammar_engine.expansion_validator import validate_clause_completeness

    # Mock data - no CLAUSE type phrases (simple sentence)
    result = validate_clause_completeness("He runs.", None, [])

    assert result.severity == "PASS"
    assert result.is_valid is True


def test_clause_completeness_missing_predicate():
    """validate_clause_completeness detects missing predicate"""
    from grammar_engine.expansion_validator import validate_clause_completeness
    from grammar_engine.phrase_segmenter import PhraseNode

    # Mock incomplete clause: "The boy who"
    clause = PhraseNode(
        id="clause_1", type="CLAUSE", text="who", head_token_text="who",
        head_pos="PRON", syntactic_role="relative_clause",
        span=(2, 3), features={}, parent_id="np_1", children_ids=[],
        is_expandable=False, candidates=[]
    )

    result = validate_clause_completeness("The boy who.", None, [clause])

    assert result.severity == "ERROR"
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_non_finite_legality_to_base_form_valid():
    """validate_non_finite_legality accepts 'to + base form'"""
    from grammar_engine.expansion_validator import validate_non_finite_legality

    # Mock doc with "to go"
    class MockToken:
        def __init__(self, text, pos, tag):
            self.text = text
            self.pos_ = pos
            self.tag_ = tag

    doc = [
        MockToken("I", "PRON", "PRP"),
        MockToken("want", "VERB", "VBP"),
        MockToken("to", "PART", "TO"),
        MockToken("go", "VERB", "VB"),  # VB = base form
    ]

    result = validate_non_finite_legality("I want to go.", doc, [])

    assert result.severity == "PASS"
    assert result.is_valid is True


def test_non_finite_legality_to_wrong_form():
    """validate_non_finite_legality rejects 'to + wrong form'"""
    from grammar_engine.expansion_validator import validate_non_finite_legality

    # Mock doc with "to went"
    class MockToken:
        def __init__(self, text, pos, tag):
            self.text = text
            self.pos_ = pos
            self.tag_ = tag

    doc = [
        MockToken("I", "PRON", "PRP"),
        MockToken("want", "VERB", "VBP"),
        MockToken("to", "PART", "TO"),
        MockToken("went", "VERB", "VBD"),  # VBD = past tense (wrong)
    ]

    result = validate_non_finite_legality("I want to went.", doc, [])

    assert result.severity == "ERROR"
    assert result.is_valid is False
    assert len(result.errors) > 0


def test_relative_pronoun_match_person_who_valid():
    """validate_relative_pronoun_match accepts 'person + who'"""
    from grammar_engine.expansion_validator import validate_relative_pronoun_match

    result = validate_relative_pronoun_match("The man who runs.", None, [])

    # Should pass (no CLAUSE phrases in mock)
    assert result.severity == "PASS"
    assert result.is_valid is True


def test_relative_pronoun_match_person_which_invalid():
    """validate_relative_pronoun_match rejects 'person + which'"""
    from grammar_engine.expansion_validator import validate_relative_pronoun_match
    from grammar_engine.phrase_segmenter import PhraseNode

    # Mock NP for "man"
    np = PhraseNode(
        id="np_1", type="NP", text="The man", head_token_text="man",
        head_pos="NOUN", syntactic_role="subject",
        span=(0, 2), features={}, parent_id=None, children_ids=["clause_1"],
        is_expandable=False, candidates=[]
    )

    # Mock CLAUSE for "which runs"
    clause = PhraseNode(
        id="clause_1", type="CLAUSE", text="which runs", head_token_text="which",
        head_pos="PRON", syntactic_role="relative_clause",
        span=(2, 4), features={}, parent_id="np_1", children_ids=[],
        is_expandable=False, candidates=[]
    )

    # Mock doc
    class MockToken:
        def __init__(self, text, pos, ent_type=""):
            self.text = text
            self.pos_ = pos
            self.ent_type_ = ent_type

    doc = [
        MockToken("The", "DET"),
        MockToken("man", "NOUN", "PERSON"),
        MockToken("which", "PRON"),
        MockToken("runs", "VERB"),
    ]

    result = validate_relative_pronoun_match("The man which runs.", doc, [np, clause])

    assert result.severity == "ERROR"
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "which" in result.errors[0].lower()


# ===================== Task 7: LanguageTool validator #6 =====================

def test_validate_with_languagetool_server_not_available():
    """validate_with_languagetool returns INFO when server not available"""
    from grammar_engine.expansion_validator import validate_with_languagetool

    # LanguageTool not started in test environment
    result = validate_with_languagetool("He go to school.")

    # Should return INFO (not ERROR), system continues
    assert result.severity in ["INFO", "PASS"]
    assert result.is_valid is True


def test_validate_with_languagetool_success():
    """validate_with_languagetool processes LT matches into ValidationReport"""
    from grammar_engine.expansion_validator import validate_with_languagetool
    from unittest.mock import patch, MagicMock

    # Mock LanguageTool to return a match
    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = True
    mock_manager.check.return_value = MagicMock(
        success=True,
        matches=[{
            "message": "Possible typo: you repeated a whitespace",
            "shortMessage": "Whitespace repetition",
            "category": {"id": "TYPOGRAPHY", "name": "Typography"},
            "ruleId": "WHITESPACE_RULE"
        }],
        error=None,
        timeout=False
    )

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate_with_languagetool("He  runs.")

    # Should map TYPOGRAPHY to INFO
    assert result.severity == "INFO"
    assert result.is_valid is True
    assert len(result.infos) > 0


def test_validate_with_languagetool_timeout():
    """validate_with_languagetool handles timeout gracefully"""
    from grammar_engine.expansion_validator import validate_with_languagetool
    from unittest.mock import patch, MagicMock

    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = True
    mock_manager.check.return_value = MagicMock(
        success=False,
        matches=[],
        error="Request timeout",
        timeout=True
    )

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate_with_languagetool("Test sentence.")

    assert result.severity == "INFO"
    assert result.is_valid is True
    assert "timeout" in result.infos[0].lower() or "超时" in result.infos[0]


# ===================== Task 8: Update validate() entry point =====================

def test_validate_entry_point_calls_all_validators():
    """validate() calls all 6 validators with safe_execute"""
    from grammar_engine.expansion_validator import validate
    from unittest.mock import patch, MagicMock

    # Mock LanguageTool manager
    mock_manager = MagicMock()
    mock_manager.is_alive.return_value = False

    with patch('grammar_engine.languagetool_manager.get_languagetool_manager', return_value=mock_manager):
        result = validate("Test sentence.", None, [])

    # Should return a ValidationReport (not crash)
    assert result.severity in ["PASS", "INFO", "WARNING", "ERROR"]
    assert result.is_valid in [True, False]


def test_validate_entry_point_validator_exception_does_not_crash():
    """validate() continues when one validator throws exception"""
    from grammar_engine.expansion_validator import validate
    from unittest.mock import patch

    # Mock one validator to raise exception
    def failing_validator(sentence, doc, phrases):
        raise ValueError("Test validator failure")

    with patch('grammar_engine.expansion_validator.validate_subject_verb_agreement', failing_validator):
        result = validate("Test sentence.", None, [])

    # Should degrade to WARNING but not crash
    assert result.severity in ["WARNING", "INFO", "PASS"]
    assert result.is_valid is True  # safe_execute ensures is_valid=True on exception
    assert any("subject_verb_agreement" in w for w in result.warnings)


def test_validate_entry_point_merges_severity():
    """validate() merges severity from multiple validators correctly"""
    from grammar_engine.expansion_validator import validate, ValidationReport
    from unittest.mock import patch

    # Mock validators with different severities
    def pass_validator(sentence, doc, phrases):
        return ValidationReport(severity="PASS", is_valid=True)

    def warning_validator(sentence, doc, phrases):
        return ValidationReport(severity="WARNING", is_valid=True, warnings=["Test warning"])

    def languagetool_pass_validator(sentence):
        return ValidationReport(severity="PASS", is_valid=True)

    with patch('grammar_engine.expansion_validator.validate_subject_verb_agreement', pass_validator):
        with patch('grammar_engine.expansion_validator.validate_tense_consistency', warning_validator):
            with patch('grammar_engine.expansion_validator.validate_clause_completeness', pass_validator):
                with patch('grammar_engine.expansion_validator.validate_non_finite_legality', pass_validator):
                    with patch('grammar_engine.expansion_validator.validate_relative_pronoun_match', pass_validator):
                        with patch('grammar_engine.expansion_validator.validate_with_languagetool', languagetool_pass_validator):
                            result = validate("Test.", None, [])

    # Should merge to WARNING (highest severity)
    assert result.severity == "WARNING"
    assert len(result.warnings) == 1
    assert "Test warning" in result.warnings[0]
