"""
Main FastAPI application for video creation and Instagram publishing.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    TemplateDynamicParams,
    VideoCreationRequest,
    VideoCreationResponse,
    HealthCheckResponse
)
from app.job_queue import job_queue, Job, JobStatus
from utils.video_processor import VideoProcessor, InstagramPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
video_processor = VideoProcessor(output_dir=settings.VIDEO_OUTPUT_DIR)
instagram_publisher = InstagramPublisher()
settings.ensure_output_dir()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    if not settings.validate():
        logger.warning("Environment variables missing. Instagram publishing may fail.")

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

def process_video_background(job_id: str, template: str, params: dict, publish: bool = True) -> None:
    try:
        logger.info(f"Starting job {job_id}")
        job_queue.update_job_status(job_id, JobStatus.PROCESSING)
        
        video_data = video_processor.process_video(params)
        
        job_queue.update_job_status(job_id, JobStatus.COMPLETED, result=video_data)
        
        if publish:
            logger.info(f"Publishing to Instagram ({video_data.get('region', 'BR')})")
            if instagram_publisher.publish_video(video_data):
                job_queue.update_job_status(job_id, JobStatus.PUBLISHED)
            else:
                logger.warning(f"Failed to publish video {job_id}")
    except Exception as e:
        logger.error(f"Error job {job_id}: {e}", exc_info=True)
        job_queue.update_job_status(job_id, JobStatus.FAILED, error=str(e))

@app.post("/api/v1/videos/create", response_model=VideoCreationResponse, status_code=202, tags=["Videos"])
async def create_video(request: VideoCreationRequest, background_tasks: BackgroundTasks, publish: bool = True):
    """Generic endpoint. Only accepts 'DYNAMIC' or 'E'."""
    try:
        if request.template.upper() not in ["DYNAMIC", "E"]:
            raise HTTPException(status_code=400, detail="Only 'DYNAMIC' template supported.")
        
        job_id = str(uuid.uuid4())
        job = Job(job_id, request.template, request.params)
        job_queue.add_job(job)
        
        background_tasks.add_task(process_video_background, job_id, request.template, request.params, publish)
        
        return VideoCreationResponse(status="ok", message="Job accepted", video_id=job_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/videos/template-dynamic", response_model=VideoCreationResponse, status_code=202, tags=["Videos"])
async def create_video_template_dynamic(params: TemplateDynamicParams, background_tasks: BackgroundTasks, publish: bool = True):
    """Create video with Template Dynamic (Ultimate)."""
    request = VideoCreationRequest(template="DYNAMIC", params=params.model_dump())
    return await create_video(request, background_tasks, publish)

@app.get("/api/v1/videos/{video_id}", tags=["Videos"])
async def get_video_status(video_id: str):
    job = job_queue.get_job(video_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()

@app.get("/api/v1/videos", tags=["Videos"])
async def list_videos(status_filter: Optional[str] = None, limit: int = 100):
    all_jobs = job_queue.get_all_jobs()
    if status_filter:
        all_jobs = {k: v for k, v in all_jobs.items() if v.get("status") == status_filter}
    return {"total": len(all_jobs), "jobs": list(all_jobs.values())[:limit]}

