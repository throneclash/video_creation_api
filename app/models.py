from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel

class Victim(BaseModel):
    name: str
    photo_url: str
    cause: str = "EMPURRADO"
    old_position: int = 9

class TemplateDynamicParams(BaseModel):
    region: Literal["BR", "GLOBAL"] = "BR"
    event_type: str = "GOLPE NO TRONO"
    hook: str = "O REI CAIU!"
    amount: float
    king_name: str
    king_photo_url: str
    message: Optional[str] = None
    dethroned_name: Optional[str] = None
    dethroned_photo_url: Optional[str] = None
    dethroned_reign_days: Optional[int] = 0
    victims: Optional[List[Victim]] = []
    cta: str = "QUEM VAI DESAFIAR?"

    # Flags de controle
    persist_file: bool = False  # Se True, mantém o arquivo após processamento
    publish_instagram: bool = True  # Se True, publica no Instagram

class VideoCreationRequest(BaseModel):
    template: str
    params: Dict[str, Any]

class VideoCreationResponse(BaseModel):
    status: str
    message: Optional[str] = None
    video_id: str

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    timestamp: str