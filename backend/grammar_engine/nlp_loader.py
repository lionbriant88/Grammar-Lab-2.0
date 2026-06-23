"""spaCy Model Loader - Singleton Pattern

M3b: 新增 Benepar (Berkeley Neural Parser) 支持
"""

import spacy
from typing import Optional
import threading
import sys
import codecs


# Fix Windows console encoding
if sys.platform == "win32":
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


# ----------------------------- Benepar Loader (M3b) -----------------------------

_benepar_parser = None
_benepar_lock = threading.Lock()


def get_benepar_parser():
    """获取 Benepar parser 单例。

    返回:
    - benepar.Parser 实例(成功)
    - None(失败,降级到 spaCy)

    M3b: 首次调用时加载 benepar_en3 模型,失败时返回 None 而非抛异常。
    """
    global _benepar_parser

    if _benepar_parser is None:
        with _benepar_lock:
            if _benepar_parser is None:
                try:
                    import benepar
                    _benepar_parser = benepar.Parser("benepar_en3")
                    print("[OK] Benepar model 'benepar_en3' loaded successfully")
                except ImportError:
                    print("[WARN] Benepar not installed. Run: pip install benepar")
                    _benepar_parser = False  # 标记为失败
                except Exception as e:
                    print(f"[WARN] Benepar model load failed: {e}. Falling back to spaCy.")
                    _benepar_parser = False

    return _benepar_parser if _benepar_parser else None


# ----------------------------- spaCy Loader -----------------------------

class NLPLoader:
    """spaCy model singleton loader"""
    
    _instance: Optional["NLPLoader"] = None
    _lock = threading.Lock()
    _nlp = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, model_name: str = "en_core_web_sm") -> spacy.Language:
        """Load spaCy model"""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(model_name)
                print(f"[OK] spaCy model '{model_name}' loaded successfully")
            except OSError:
                print(f"[FAIL] Model '{model_name}' not found, attempting download...")
                try:
                    from spacy.cli.download import download as spacy_download
                    spacy_download(model_name)
                    self._nlp = spacy.load(model_name)
                    print(f"[OK] spaCy model '{model_name}' downloaded and loaded")
                except Exception as e:
                    raise RuntimeError(
                        f"Cannot load spaCy model: {e}. "
                        f"Please run: python -m spacy download {model_name}"
                    )
        return self._nlp
    
    def get(self) -> spacy.Language:
        """Get loaded model"""
        if self._nlp is None:
            return self.load()
        return self._nlp
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._nlp is not None


# Global singleton
nlp_loader = NLPLoader()
