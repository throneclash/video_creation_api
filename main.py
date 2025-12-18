"""
Main FastAPI application for video creation and Instagram publishing.
"""

import os
import logging
import uuid
import requests
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pyngrok import ngrok

from app.config import settings
from app.models import (
    TemplateDynamicParams,
    VideoCreationRequest,
    VideoCreationResponse,
    HealthCheckResponse
)
from app.job_queue import job_queue, Job, JobStatus
from utils.video_processor import VideoProcessor, InstagramPublisher, delete_video_file, save_payload_log

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para capturar TODOS os payloads recebidos (inclusive erros 422)"""
    # Captura o corpo da requisição
    body = await request.body()

    # Log apenas para rotas de API (evita poluir com /docs, /health, etc)
    if "/api/" in request.url.path and body:
        logger.info(f"[PAYLOAD] {request.method} {request.url.path} - Body: {body.decode('utf-8', errors='replace')}")

    response = await call_next(request)

    # Log se houve erro de validação (422)
    if response.status_code == 422:
        logger.warning(f"[VALIDATION ERROR 422] {request.method} {request.url.path}")

    return response

# Initialize processor
video_processor = VideoProcessor(output_dir=settings.VIDEO_OUTPUT_DIR)
instagram_publisher = InstagramPublisher()
settings.ensure_output_dir()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    if not settings.validate():
        logger.warning("Environment variables missing. Instagram publishing may fail.")

    # Iniciar túnel ngrok
    ngrok_auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if ngrok_auth_token:
        try:
            ngrok.set_auth_token(ngrok_auth_token)
            public_url = ngrok.connect(8000).public_url
            logger.info(f"Túnel ngrok criado: {public_url}")

            # Enviar URL para o Supabase
            supabase_url = os.getenv("SUPABASE_FUNCTION_URL")
            supabase_key = os.getenv("SUPABASE_API_KEY")

            if supabase_url and supabase_key:
                headers = {
                    "Authorization": f"Bearer {supabase_key}",
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "name": "Functions",
                    "url": public_url
                }

                try:
                    res = requests.post(supabase_url, json=payload, headers=headers)
                    logger.info(f"URL enviada ao Supabase: {res.status_code}")
                except Exception as e:
                    logger.error(f"Erro ao enviar URL para Supabase: {e}")
            else:
                logger.warning("SUPABASE_FUNCTION_URL ou SUPABASE_API_KEY não configurados")
        except Exception as e:
            logger.error(f"Erro ao criar túnel ngrok: {e}")
    else:
        logger.info("NGROK_AUTH_TOKEN não configurado - túnel não será criado")

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

def process_video_background(job_id: str, template: str, params: dict) -> None:
    """
    Processa vídeo em background com controle de flags:
    - persist_file: Se False (padrão), deleta o arquivo após processamento
    - publish_instagram: Se True (padrão), tenta publicar no Instagram
    """
    video_path = None
    persist_file = params.get("persist_file", False)
    publish_instagram = params.get("publish_instagram", True)

    try:
        logger.info(f"Starting job {job_id}")
        logger.info(f"Flags: persist_file={persist_file}, publish_instagram={publish_instagram}")
        job_queue.update_job_status(job_id, JobStatus.PROCESSING)

        # 1. Renderiza o vídeo
        video_data = video_processor.process_video(params)
        video_path = video_data.get("video_path")

        # Se falhou na renderização, o arquivo já foi deletado pelo processor
        if video_data.get("status") == "failed":
            job_queue.update_job_status(job_id, JobStatus.FAILED, error="Erro na renderização")
            return

        job_queue.update_job_status(job_id, JobStatus.COMPLETED, result=video_data)

        # 2. Publica no Instagram (se flag habilitada)
        if publish_instagram:
            logger.info(f"Publishing to Instagram ({video_data.get('region', 'BR')})")
            publish_result = instagram_publisher.publish_video(video_data)

            if publish_result.get("success"):
                job_queue.update_job_status(job_id, JobStatus.PUBLISHED, result={
                    **video_data,
                    "instagram_id": publish_result.get("published_id")
                })
                # Sucesso no Instagram: deleta arquivo (a menos que persist_file=True)
                if not persist_file:
                    delete_video_file(video_path)
                    logger.info(f"Vídeo publicado e arquivo deletado: {video_path}")
            else:
                # Falha no Instagram: salva payload e deleta arquivo
                logger.warning(f"Failed to publish video {job_id}")
                error_msg = publish_result.get("error", "Erro desconhecido")

                # Salva payload para debug
                save_payload_log(
                    payload=video_data.get("original_params", params),
                    video_id=video_data.get("video_id", job_id),
                    error_message=error_msg
                )

                # Deleta arquivo em caso de falha de integração
                delete_video_file(video_path)
                logger.info(f"Falha no Instagram: payload salvo e arquivo deletado")

                job_queue.update_job_status(job_id, JobStatus.FAILED, error=f"Instagram: {error_msg}")
        else:
            # Não publica no Instagram
            logger.info(f"Publicação no Instagram desabilitada para job {job_id}")
            # Se não vai publicar e persist_file=False, deleta
            if not persist_file:
                delete_video_file(video_path)
                logger.info(f"Arquivo deletado (persist_file=False): {video_path}")

    except Exception as e:
        logger.error(f"Error job {job_id}: {e}", exc_info=True)
        job_queue.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        # Em caso de exceção, deleta o arquivo se existir
        if video_path:
            delete_video_file(video_path)

@app.post("/api/v1/videos/create", response_model=VideoCreationResponse, status_code=202, tags=["Videos"])
async def create_video(request: VideoCreationRequest, background_tasks: BackgroundTasks):
    """
    Generic endpoint. Only accepts 'DYNAMIC' or 'E'.

    Flags de controle (no payload):
    - persist_file: Se True, mantém o arquivo após processamento (padrão: False)
    - publish_instagram: Se True, publica no Instagram (padrão: True)
    """
    try:
        if request.template.upper() not in ["DYNAMIC", "E"]:
            raise HTTPException(status_code=400, detail="Only 'DYNAMIC' template supported.")

        job_id = str(uuid.uuid4())
        job = Job(job_id, request.template, request.params)
        job_queue.add_job(job)

        background_tasks.add_task(process_video_background, job_id, request.template, request.params)

        return VideoCreationResponse(status="ok", message="Job accepted", video_id=job_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/videos/template-dynamic", response_model=VideoCreationResponse, status_code=202, tags=["Videos"])
async def create_video_template_dynamic(params: TemplateDynamicParams, background_tasks: BackgroundTasks):
    """
    Create video with Template Dynamic (Ultimate).

    Flags de controle:
    - persist_file: Se True, mantém o arquivo após processamento (padrão: False)
    - publish_instagram: Se True, publica no Instagram (padrão: True)
    """
    # Log imediato do payload validado (útil para debug)
    logger.info(f"[VALIDATED] template-dynamic payload: {params.model_dump_json()}")

    request = VideoCreationRequest(template="DYNAMIC", params=params.model_dump())
    return await create_video(request, background_tasks)

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

