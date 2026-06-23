"""LanguageTool Manager - Embedded LanguageTool server lifecycle management

M3c1: Non-blocking async startup, stateless health checks, graceful degradation.
"""
import logging
import os
import socket
import subprocess
import threading
from dataclasses import dataclass
from typing import Optional

from .external_service_manager import ExternalServiceManager, ServiceStatus

logger = logging.getLogger(__name__)


@dataclass
class LTReport:
    """LanguageTool 检查结果（结构化，非 dict）"""
    success: bool
    matches: list[dict]
    error: Optional[str] = None
    timeout: bool = False


class LanguageToolManager(ExternalServiceManager):
    """LanguageTool embedded server manager.

    Key features:
    - Non-blocking async startup (background thread)
    - Stateless health checks (no cached bool)
    - Graceful degradation on failure
    """

    def __init__(self, jar_path: str, jre_path: str, port: int = 8081):
        self.jar_path = jar_path
        self.jre_path = jre_path
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self._startup_thread: Optional[threading.Thread] = None

    def is_alive(self) -> bool:
        """Real-time health check (lightweight, doesn't call actual API)

        Returns:
            True if service process exists and port is reachable
        """
        # Check if process exists and hasn't terminated
        if self.process is None or self.process.poll() is not None:
            return False

        # Check if port is listening
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_status(self) -> ServiceStatus:
        """Get detailed service status

        Returns:
            ServiceStatus with availability, message, and port
        """
        if self.is_alive():
            return ServiceStatus(
                available=True,
                message="LanguageTool server running",
                port=self.port
            )
        elif self._startup_thread and self._startup_thread.is_alive():
            return ServiceStatus(
                available=False,
                message="LanguageTool server starting...",
                port=self.port
            )
        else:
            return ServiceStatus(
                available=False,
                message="LanguageTool server not running",
                port=self.port
            )

    def ensure_server_async(self):
        """Start server in background thread (non-blocking)

        If already running or starting, does nothing.
        Grammar Engine should be immediately available.
        """
        # Already running
        if self.is_alive():
            return

        # Already starting
        if self._startup_thread and self._startup_thread.is_alive():
            return

        # Start in background thread
        self._startup_thread = threading.Thread(
            target=self._start_server,
            daemon=True
        )
        self._startup_thread.start()
        logger.info("LanguageTool startup initiated (non-blocking)")

    def _start_server(self):
        """实际启动逻辑（后台线程）"""
        try:
            # Check if jar and jre exist
            if not os.path.exists(self.jar_path):
                logger.warning(f"LanguageTool jar not found: {self.jar_path}")
                return

            if not os.path.exists(self.jre_path):
                logger.warning(f"JRE not found: {self.jre_path}")
                return

            java_bin = os.path.join(self.jre_path, "bin", "java")
            if os.name == 'nt':
                java_bin += ".exe"

            if not os.path.exists(java_bin):
                logger.warning(f"Java executable not found: {java_bin}")
                return

            cmd = [
                java_bin,
                "-cp", self.jar_path,
                "org.languagetool.server.HTTPServer",
                "--port", str(self.port),
                "--allow-origin", "*"
            ]

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )

            logger.info(f"LanguageTool server starting on port {self.port} (PID: {self.process.pid})")

        except Exception as e:
            logger.error(f"Failed to start LanguageTool: {e}", exc_info=True)

    def check(self, sentence: str, timeout: int = 5) -> LTReport:
        """语法检查（返回结构化 LTReport）

        Args:
            sentence: Sentence to check
            timeout: Request timeout in seconds

        Returns:
            LTReport with success status, matches, and error info
        """
        if not self.is_alive():
            return LTReport(
                success=False,
                matches=[],
                error="LanguageTool server not available"
            )

        try:
            import requests

            response = requests.post(
                f"http://localhost:{self.port}/v2/check",
                data={"text": sentence, "language": "en-US"},
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

            return LTReport(
                success=True,
                matches=data.get("matches", [])
            )

        except requests.Timeout:
            return LTReport(
                success=False,
                matches=[],
                error="Request timeout",
                timeout=True
            )

        except Exception as e:
            return LTReport(
                success=False,
                matches=[],
                error=str(e)
            )

    def restart(self):
        """Restart the service

        Calls shutdown() then ensure_server_async()
        """
        logger.info("Restarting LanguageTool server")
        self.shutdown()
        self.ensure_server_async()

    def shutdown(self):
        """Shutdown the service

        Terminate process and clean up resources
        """
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("LanguageTool server shut down")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("LanguageTool server killed (timeout)")
            except Exception as e:
                logger.error(f"Error shutting down LanguageTool: {e}")
            finally:
                self.process = None


# ===================== Singleton Pattern =====================

_languagetool_manager_instance: Optional[LanguageToolManager] = None


def get_languagetool_manager() -> LanguageToolManager:
    """获取全局 LanguageTool 管理器单例

    Returns:
        Singleton LanguageToolManager instance
    """
    global _languagetool_manager_instance

    if _languagetool_manager_instance is None:
        jar_path = os.getenv("LT_JAR_PATH", "./languagetool/languagetool-server.jar")
        jre_path = os.getenv("LT_JRE_PATH", "./jre")
        port = int(os.getenv("LT_PORT", "8081"))

        _languagetool_manager_instance = LanguageToolManager(
            jar_path=jar_path,
            jre_path=jre_path,
            port=port
        )

    return _languagetool_manager_instance


__all__ = [
    "LanguageToolManager",
    "LTReport",
    "get_languagetool_manager",
]
