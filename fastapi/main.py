"""Main FastAPI application for AI Receptionist."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.config import settings
from fastapi.services.audio_service import AudioService
from fastapi.routing.main import main_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"🚀 Starting AI Receptionist on {settings.host}:{settings.port}")
    print(f"📞 Twilio WebSocket URL: {settings.public_ws_url}")
    
    # Initialize services
    app.state.audio_service = AudioService()
    
    # Debug: Print all registered routes
    print("🔍 Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {route.methods} {route.path}")
        elif hasattr(route, 'path') and hasattr(route, 'endpoint'):
            print(f"  WebSocket {route.path}")
    
    yield
    # Shutdown
    print("👋 Shutting down AI Receptionist")


# Create FastAPI app
app = FastAPI(
    title="AI Receptionist",
    description="Voice AI receptionist with Twilio, LangChain, and real-time STT/TTS",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.socket_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(main_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app=app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
