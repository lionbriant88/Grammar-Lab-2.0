"""spaCy Model Loader - Singleton Pattern"""

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
