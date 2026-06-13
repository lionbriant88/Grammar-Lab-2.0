"""Grammar Lab Grammar Service - FastAPI Entry Point"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from grammar_engine.models import (
    HealthResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    RewriteRequest,
    RewriteResponse,
    VerbNode,
    TimeAdverbial,
    TimelineNode,
    TimelineData,
    AnalysisSummary,
)
from grammar_engine.nlp_loader import nlp_loader


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("service.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


# Global state
model_loaded = False
startup_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Loading spaCy model...")
    global model_loaded
    try:
        nlp_loader.load()
        model_loaded = True
        startup_event.set()
        logger.info("[OK] Model loaded, service ready")
    except Exception as e:
        logger.error(f"[FAIL] Model loading failed: {e}")
        model_loaded = False
        startup_event.set()
    
    yield
    
    logger.info("Service shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Grammar Lab Grammar Service",
    description="Tense analysis and sentence rewriting engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    await startup_event.wait()
    
    nlp = nlp_loader.get() if model_loaded else None
    return HealthResponse(
        status="ok" if model_loaded else "error",
        model_loaded=model_loaded,
        model_version=nlp.meta["version"] if nlp else None,
    )


@app.post("/api/tense/analyze", response_model=AnalyzeResponse)
async def analyze_tense(request: AnalyzeRequest):
    """Analyze tenses in a sentence"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    from grammar_engine.tense_analyzer import analyze as tense_analyze

    result = tense_analyze(request.sentence)

    return AnalyzeResponse(
        sentence=result["sentence"],
        verbs=[VerbNode(**v) for v in result["verbs"]],
        time_adverbials=[TimeAdverbial(**a) for a in result["time_adverbials"]],
        timeline=TimelineData(
            nodes=[TimelineNode(**n) for n in result["timeline"]["nodes"]],
            past_zone=result["timeline"]["past_zone"],
            present_zone=result["timeline"]["present_zone"],
            future_zone=result["timeline"]["future_zone"],
        ),
        summary=AnalysisSummary(
            verb_count=result["summary"]["verb_count"],
            supported_verb_count=result["summary"]["supported_verb_count"],
            primary_tense=result["summary"]["primary_tense"],
            warnings=result["summary"].get("warnings", []),
        ),
        warnings=[],
    )


@app.post("/api/tense/rewrite", response_model=RewriteResponse)
async def rewrite_sentence(request: RewriteRequest):
    """Rewrite sentence (after drag to change tense)"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    from grammar_engine.models import (
        AnalyzeResponse, ChangeItem,
        VerbNode, SupportedTense, TimeZone, Aspect,
        TimeAdverbial, TimelineNode, TimelineData, AnalysisSummary
    )
    
    return RewriteResponse(
        new_sentence=request.sentence,
        new_analysis=AnalyzeResponse(
            sentence=request.sentence,
            verbs=[],
            time_adverbials=[],
            timeline=TimelineData(
                nodes=[],
                past_zone=(0.0, 0.33),
                present_zone=(0.33, 0.67),
                future_zone=(0.67, 1.0),
            ),
            summary=AnalysisSummary(
                verb_count=0,
                supported_verb_count=0,
                primary_tense="unknown",
            ),
        ),
        changes=[],
        explanation="Rewrite feature not implemented yet",
        warnings=["Rewrite feature not implemented yet"],
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=18765,
        reload=True,
        log_level="info",
    )
