import os
import uuid
import logging
import asyncio
import random
import glob
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from .renderer import render_video
from app.config import settings

logger = logging.getLogger(__name__)


def delete_video_file(video_path: str) -> bool:
    """Deleta um arquivo de vídeo se existir."""
    try:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"Arquivo deletado: {video_path}")
            return True
    except Exception as e:
        logger.error(f"Erro ao deletar arquivo {video_path}: {e}")
    return False


def save_payload_log(payload: Dict[str, Any], video_id: str, error_message: str, logs_dir: str = "./logs") -> str:
    """Salva o payload em um arquivo .txt quando há falha de integração."""
    try:
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failed_payload_{video_id}_{timestamp}.txt"
        filepath = os.path.join(logs_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== FALHA DE INTEGRAÇÃO INSTAGRAM ===\n")
            f.write(f"Data/Hora: {datetime.now().isoformat()}\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Erro: {error_message}\n")
            f.write(f"\n=== PAYLOAD ===\n")
            f.write(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

        logger.info(f"Payload salvo em: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Erro ao salvar payload: {e}")
        return ""

# --- DICIONÁRIO DE TRADUÇÃO (labels básicos) ---
LOCALES = {
    "BR": {
        "currency_symbol": "R$",
        "brand": "THRONECLASH"
    },
    "GLOBAL": {
        "currency_symbol": "$",
        "brand": "THRONECLASH GLOBAL"
    }
}

class VideoProcessor:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.assets_dir = os.path.join(base_dir, "assets")
        template_dir = os.path.join(base_dir, "templates")
        
        os.makedirs(self.assets_dir, exist_ok=True)
        if not os.path.exists(template_dir): template_dir = os.path.join(os.getcwd(), "templates")
        self.template_env = Environment(loader=FileSystemLoader(template_dir))

    def _get_random_music(self) -> Optional[str]:
        mp3_files = glob.glob(os.path.join(self.assets_dir, "*.mp3"))
        logger.info(f"🔍 Diretório de assets: {self.assets_dir}")
        logger.info(f"🎵 Arquivos MP3 encontrados: {len(mp3_files)}")
        if mp3_files:
            selected = random.choice(mp3_files)
            logger.info(f"🎵 Música selecionada: {selected}")
            return selected
        
        # Fallback
        backup_url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_14578d6b8e.mp3?filename=cinematic.mp3"
        dest = os.path.join(self.assets_dir, "default_epic.mp3")
        try:
            with open(dest, 'wb') as f: f.write(requests.get(backup_url).content)
            return dest
        except: return None

    def _format_currency(self, amount: float, region: str) -> str:
        """Formata dinheiro: R$ 1.000,00 (BR) ou $ 1,000.00 (Global)"""
        if region == "BR":
            return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"{amount:,.2f}"

    def process_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Iniciando renderização Dinâmica...")

        video_id = str(uuid.uuid4())
        region = params.get("region", "BR").upper()
        filename = f"{region.lower()}_{video_id}.mp4"
        output_path = os.path.join(self.output_dir, filename)

        # 1. Música aleatória
        audio_path = self._get_random_music()
        texts = LOCALES.get(region, LOCALES["BR"])

        # 2. Preparar Contexto (dados do backend)
        context = params.copy()
        context["region"] = region
        context["labels"] = texts

        # 3. Renderizar
        try:
            template = self.template_env.get_template("template_dynamic_new.html")
            html_content = template.render(**context)

            # Duração Dinâmica: f1=5.5s + frames condicionais + f4=4s
            duration = 10000  # f1 (5.5s) + f4 (4s) + margem
            if context.get("dethroned_name"): duration += 3500  # f2: Ex-Rei
            if context.get("victims"): duration += 3500         # f3: Eliminados

            logger.info(f"Renderizando [{region}] {duration}ms -> {output_path}")

            asyncio.run(render_video(
                html_content=html_content,
                output_path=output_path,
                audio_path=audio_path,
                width=1080, height=1920,
                duration=duration
            ))

            status = "completed"
            error = None
        except Exception as e:
            logger.error(f"Erro Fatal: {e}", exc_info=True)
            status = "failed"
            error = str(e)
            # Deleta arquivo em caso de erro
            delete_video_file(output_path)

        # Formata amount para exibição
        raw_amount = float(params.get("amount", 0))
        formatted_amount = self._format_currency(raw_amount, region)

        return {
            "video_id": video_id,
            "status": status,
            "video_path": output_path if status == "completed" else None,
            "region": region,
            "king_name": params.get("king_name"),
            "amount": formatted_amount,
            "persist_file": params.get("persist_file", False),
            "original_params": params
        }

class InstagramPublisher:
    def __init__(self):
        # Não iniciamos credenciais fixas aqui, decidimos no momento do envio
        self.last_error = None

    def publish_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publica vídeo no Instagram.
        Retorna dict com: success (bool), error (str ou None), published_id (str ou None)
        """
        path = video_data.get("video_path")
        region = video_data.get("region", "BR")
        self.last_error = None

        # Seleciona Credenciais baseadas na região
        if region == "GLOBAL":
            access_token = settings.INSTAGRAM_ACCESS_TOKEN_GLOBAL
            account_id = settings.INSTAGRAM_ACCOUNT_ID_GLOBAL
        else:
            access_token = settings.INSTAGRAM_ACCESS_TOKEN_BR
            account_id = settings.INSTAGRAM_ACCOUNT_ID_BR

        if not access_token or not account_id:
            self.last_error = f"Credenciais não encontradas para região {region}"
            logger.error(f"❌ {self.last_error}")
            return {"success": False, "error": self.last_error, "published_id": None}

        if not path or not os.path.exists(path):
            self.last_error = f"Arquivo de vídeo não encontrado: {path}"
            logger.error(f"❌ {self.last_error}")
            return {"success": False, "error": self.last_error, "published_id": None}

        base_api = f"https://graph.facebook.com/v18.0/{account_id}"
        video_api = f"https://graph-video.facebook.com/v18.0/{account_id}"

        try:
            # 1. Init
            logger.info(f"Iniciando upload para Instagram [{region}]...")
            res = requests.post(f"{video_api}/media?upload_type=resumable&media_type=REELS",
                              headers={"Authorization": f"Bearer {access_token}"})
            if res.status_code != 200:
                self.last_error = f"Erro Init: {res.text}"
                logger.error(self.last_error)
                return {"success": False, "error": self.last_error, "published_id": None}

            uri = res.json().get("uri")
            creation_id = res.json().get("id")

            # 2. Upload
            with open(path, 'rb') as f:
                requests.post(uri, data=f, headers={
                    "Authorization": f"OAuth {access_token}",
                    "offset": "0", "file_size": str(os.path.getsize(path))
                })

            # 3. Publish
            import time
            time.sleep(15)

            caption = f"👑 {video_data.get('king_name')} - {video_data.get('amount')}"
            if region == "GLOBAL":
                caption += "\n\n#throneclash #crypto #game #winner"
            else:
                caption += "\n\n#throneclash #ganhador #leilao #pix"

            pub = requests.post(f"{base_api}/media_publish", params={
                "creation_id": creation_id,
                "caption": caption,
                "access_token": access_token
            })

            if pub.status_code == 200:
                published_id = pub.json().get('id')
                logger.info(f"✅ Publicado no IG {region}! ID: {published_id}")
                return {"success": True, "error": None, "published_id": published_id}
            else:
                self.last_error = f"Erro Publish: {pub.text}"
                logger.error(f"❌ {self.last_error}")
                return {"success": False, "error": self.last_error, "published_id": None}

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro Exception: {e}")
            return {"success": False, "error": self.last_error, "published_id": None}