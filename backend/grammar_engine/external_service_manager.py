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
