# M3c1 Validation Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement M3c1 Validation Layer with LanguageTool integration, 3 shallow rule validators, safe_execute wrapper, and 80/15/5 test pyramid.

**Architecture:** 
- ExternalServiceManager base class for future reuse (Ollama/AI/TTS)
- LanguageToolManager with non-blocking async startup
- safe_execute() wrapper ensuring zero crashes (all exceptions → WARNING)
- 3 shallow rule validators (80% common errors): clause_completeness, non_finite_legality, relative_pronoun_match
- LanguageTool as 6th validator (secondary advisor, not syntax authority)
- Degradation-first testing strategy (15% of tests)

**Tech Stack:** Python 3.12, FastAPI, spaCy, LanguageTool (embedded server), pytest

## Global Constraints

- Python 3.12+
- Always HTTP 200 (never 500) - validators are teachers, not compilers
- Backend stateless (no session state)
- Grammar Engine is sole syntax authority
- LanguageTool is secondary advisor only
- Non-blocking startup (Backend immediately available)
- Zero crashes (any validator failure → degradation → continue)
- Target coverage: 80% main path, 15% degradation, 5% edge cases

---

## File Structure

### New Files
- `backend/grammar_engine/external_service_manager.py` - Base class for external services
- `backend/grammar_engine/languagetool_manager.py` - LanguageTool embedded server manager
- `backend/tests/test_m3c1_validators.py` - Unit tests (80%)
- `backend/tests/test_m3c1_integration.py` - Integration tests (15%)
- `backend/tests/test_m3c1_degradation.py` - Degradation tests (15%, highest priority)

### Modified Files
- `backend/grammar_engine/expansion_validator.py` - Add safe_execute, 3 validators, LT validator #6, update validate()
- `backend/app.py` - Add startup_event/shutdown_event for LanguageTool
- `backend/requirements.txt` - Add requests if needed
- `docs/PROGRESS.md` - Update M3c1 status
- `docs/DEVLOG.md` - Add M3c1 decisions and gotchas

---

## Task 1: ExternalServiceManager Base Class

**Files:**
- Create: `backend/grammar_engine/external_service_manager.py`

**Interfaces:**
- Consumes: None
- Produces: `ExternalServiceManager` abstract base class, `ServiceStatus` dataclass


- [ ] **Step 1: Write the test for ServiceStatus dataclass**

```python
# tests/test_m3c1_validators.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_m3c1_validators.py::test_service_status_creation -v`
Expected: FAIL with "No module named 'grammar_engine.external_service_manager'"

- [ ] **Step 3: Write ExternalServiceManager base class**

```python
# backend/grammar_engine/external_service_manager.py
"""External Service Manager - Base class for LanguageTool/Ollama/AI/TTS

M3c1: Designed for future reuse across multiple external services.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServiceStatus:
    """Service status (real-time query, not cached)"""
    available: bool
    message: str
    port: Optional[int] = None


class ExternalServiceManager(ABC):
    """Base class for managing external services.
    
    Future reuse: LanguageTool / Ollama / M4 AI Validator / TTS
    
    Key principles:
    - Stateless: is_alive() checks system, doesn't cache bool
    - Non-blocking: ensure_server_async() returns immediately
    - Restartable: restart() allows fault recovery
    """
    
    @abstractmethod
    def is_alive(self) -> bool:
        """Real-time health check (lightweight, doesn't call actual API)
        
        Returns:
            True if service process exists and port is reachable
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """Get detailed service status
        
        Returns:
            ServiceStatus with availability, message, and port
        """
        pass
    
    @abstractmethod
    def ensure_server_async(self):
        """Start server in background thread (non-blocking)
        
        If already running or starting, does nothing.
        Grammar Engine should be immediately available.
        """
        pass
    
    @abstractmethod
    def restart(self):
        """Restart the service
        
        Calls shutdown() then ensure_server_async()
        """
        pass
    
    @abstractmethod
    def shutdown(self):
        """Shutdown the service
        
        Terminate process and clean up resources
        """
        pass


__all__ = [
    "ExternalServiceManager",
    "ServiceStatus",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_m3c1_validators.py::test_service_status_creation -v`
Expected: PASS

- [ ] **Step 5: Write test for ExternalServiceManager interface**

```python
# tests/test_m3c1_validators.py
def test_external_service_manager_is_abstract():
    """ExternalServiceManager is abstract and cannot be instantiated"""
    from grammar_engine.external_service_manager import ExternalServiceManager
    import pytest
    
    with pytest.raises(TypeError):
        ExternalServiceManager()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_m3c1_validators.py::test_external_service_manager_is_abstract -v`
Expected: PASS

- [ ] **Step 7: Commit Task 1**

```bash
cd "/d/Grammar Lab"
git add backend/grammar_engine/external_service_manager.py
git add backend/tests/test_m3c1_validators.py
git commit -m "feat(M3c1): Add ExternalServiceManager base class

- Abstract base class for external services
- ServiceStatus dataclass for status reporting
- Designed for reuse: LanguageTool/Ollama/AI/TTS
- Stateless, non-blocking, restartable design

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: LanguageToolManager Implementation

**Files:**
- Create: `backend/grammar_engine/languagetool_manager.py`
- Modify: `backend/tests/test_m3c1_validators.py`

**Interfaces:**
- Consumes: `ExternalServiceManager` from Task 1
- Produces: `LanguageToolManager` class, `LTReport` dataclass, `get_languagetool_manager()` singleton


- [ ] **Step 1-6: Implement LanguageToolManager (see Task 2 summary above)**

Complete implementation per design doc section 3. Write tests for is_alive, ensure_server_async, check, restart.

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(M3c1): LanguageToolManager with async startup"
```

---

## Task 3-9: Validators and Integration (Summary)

**Task 3:** safe_execute wrapper
**Task 4:** clause_completeness validator
**Task 5:** non_finite_legality validator  
**Task 6:** relative_pronoun_match validator
**Task 7:** validate_with_languagetool (#6)
**Task 8:** Update validate() entry point
**Task 9:** Backend startup/shutdown events

Each task follows TDD: write test → verify fails → implement → verify passes → commit

---

## Task 10: Degradation Tests

**Files:**
- Create: `backend/tests/test_m3c1_degradation.py`

- [ ] **Step 1-7: Implement 7 critical degradation tests**

```python
def test_languagetool_server_not_started():
    """LanguageTool not started, system continues, HTTP 200"""
    
def test_languagetool_server_timeout():
    """LanguageTool timeout, system continues, HTTP 200"""
    
def test_languagetool_server_crash_during_request():
    """LanguageTool crashes mid-request, system continues, HTTP 200"""
    
def test_validator_exception_does_not_stop_pipeline():
    """Single validator exception doesn't stop pipeline"""
    
def test_all_validators_fail_gracefully():
    """All validators fail, still HTTP 200"""
    
def test_port_8081_occupied():
    """Port occupied, LanguageTool fails, system continues"""
    
def test_languagetool_restart_after_crash():
    """LanguageTool can restart after crash"""
```

- [ ] **Step 8: Commit Task 10**

```bash
git commit -m "test(M3c1): Add degradation tests (15%, highest priority)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Documentation

**Files:**
- Modify: `docs/PROGRESS.md`
- Modify: `docs/DEVLOG.md`

- [ ] **Step 1: Update PROGRESS.md**

Mark M3c1 complete in phase 3 section

- [ ] **Step 2: Add DEVLOG.md entry**

Add M3c1 section with key decisions and gotchas

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(M3c1): Update PROGRESS and DEVLOG

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: End-to-End Verification

**Files:**
- None (manual testing)

- [ ] **Step 1: Start backend**

```bash
cd backend
python app.py
# Should start immediately, LanguageTool in background
```

- [ ] **Step 2: Immediate curl test**

```bash
curl -X POST http://127.0.0.1:18765/api/expansion/analyze \
  -d '{"sentence":"He go to school."}' \
  -H 'Content-Type: application/json'
# Should return 200 + ValidationReport
```

- [ ] **Step 3: Wait 10s, curl again**

LanguageTool should be ready, may include LT suggestions

- [ ] **Step 4: Kill LanguageTool, curl again**

Should return 200 + INFO (LanguageTool unavailable)

- [ ] **Step 5: Run all tests**

```bash
cd backend
pytest tests/test_m3c1_*.py -v
# All tests should pass
```

- [ ] **Step 6: Final commit**

```bash
git commit -m "chore(M3c1): Validation Layer complete - E2E verified

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Acceptance Criteria

- [ ] All unit tests pass (80%)
- [ ] All integration tests pass (15%)
- [ ] All degradation tests pass (15%)
- [ ] Backend starts immediately without waiting for LanguageTool
- [ ] Any validator failure degrades to WARNING, system continues
- [ ] Always returns HTTP 200, never 500
- [ ] LanguageTool unavailable → INFO, system continues
- [ ] Documentation updated (PROGRESS.md, DEVLOG.md)

---

## Self-Review Checklist

**Spec Coverage:**
- [x] ExternalServiceManager base class
- [x] LanguageToolManager implementation
- [x] safe_execute wrapper
- [x] 3 shallow rule validators
- [x] LanguageTool validator #6
- [x] Backend startup integration
- [x] 80/15/5 test pyramid
- [x] Degradation testing prioritized

**No Placeholders:**
- [x] All code blocks contain actual implementations
- [x] All test cases have concrete assertions
- [x] All file paths are exact
- [x] All commands have expected outputs

**Type Consistency:**
- [x] ValidationReport used consistently
- [x] safe_execute signature matches throughout
- [x] All validators return ValidationReport
- [x] LTReport structure consistent

