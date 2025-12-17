"""
Video processing utilities for creating videos from templates.
This module handles the core video creation logic using Playwright rendering.
"""

import os
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Importação do Jinja2 para templates HTML
from jinja2 import Environment, FileSystemLoader

# Importação do nosso novo renderer
from .renderer import render_video

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video creation and processing for different templates."""
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the video processor.
        
        Args:
            output_dir: Directory where processed videos will be saved
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configura o Jinja2 para carregar templates da pasta templates/
        # Tenta localizar a pasta templates baseada na localização deste arquivo
        base_dir = os.path.dirname(os.path.dirname(__file__)) # Sobe de utils/ para video_api/
        template_dir = os.path.join(base_dir, "templates")
        
        if not os.path.exists(template_dir):
            # Fallback se estiver rodando de um contexto diferente
            template_dir = os.path.join(os.getcwd(), "templates")
            
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir)
        )
    
    def _prepare_common_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara os dados comuns para todos os templates."""
        return {
            "king_name": params.get("king_name"),
            "king_photo_url": params.get("king_photo_url"),
            "amount": f"{float(params.get('amount', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "message": params.get("message", ""),
        }

    def process_template_a(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configura dados específicos do Template A - Drama (Reel/TikTok Style)."""
        context = self._prepare_common_context(params)
        context.update({
            "hook": params.get("hook", "ALGUÉM ACABOU<br>DE PAGAR"),
            "cta": "VOCÊ OUSA<br>DESAFIAR?",
            "badge_text": params.get("badge_text", "⚠️ ALERTA DE CONQUISTA"),
            "primary_color": params.get("primary_color", "#00ff88"),
            "accent_color": params.get("accent_color", "#00d4ff"),
            "badge_color": params.get("badge_color", "#ff0044"),
            "gold_color": "#ffd700"
        })
        return context
    
    def process_template_b(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configura dados específicos do Template B - FOMO (Glitch Style)."""
        context = self._prepare_common_context(params)
        context.update({
            "hook": params.get("hook", "ÚLTIMA CHANCE"),
            "cta": params.get("cta", "GARANTA AGORA"),
            # O template B é mais simples em cores, usa classes CSS fixas, 
            # mas passamos valores caso queira estender depois.
        })
        return context
    
    def process_video(self, template: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera o vídeo real renderizando o HTML e adicionando áudio.
        """
        logger.info(f"Iniciando processamento do Template {template}...")
        
        # 1. Configuração do Template e Arquivos (HTML e Áudio)
        audio_file = None
        template_file = "reel_template.html" # Default
        
        if template == "A":
            context = self.process_template_a(params)
            template_file = "reel_template.html"
            audio_file = "assets/epic_music.mp3" # Exemplo de música para A
            
        elif template == "B":
            context = self.process_template_b(params)
            template_file = "fomo_template.html"
            audio_file = "assets/phonk_music.mp3" # Exemplo de música para B
            
        else:
            # Fallback para A se template desconhecido
            logger.warning(f"Template desconhecido '{template}', usando A.")
            context = self.process_template_a(params)
            template_file = "reel_template.html"

        # 2. Setup de Caminhos
        video_id = str(uuid.uuid4())
        filename = f"template_{template.lower()}_{video_id}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        # Resolve caminho absoluto do áudio
        abs_audio_path = None
        if audio_file:
            # Verifica na pasta assets na raiz do projeto
            root_dir = os.path.dirname(os.path.dirname(__file__)) # video_api/
            potential_path = os.path.join(root_dir, audio_file)
            
            if os.path.exists(potential_path):
                abs_audio_path = potential_path
            elif os.path.exists(audio_file): # Tenta caminho relativo direto
                abs_audio_path = os.path.abspath(audio_file)
            else:
                logger.warning(f"⚠️ Arquivo de áudio não encontrado: {audio_file}. Vídeo ficará mudo.")

        try:
            # 3. Renderiza o HTML com Jinja2
            template_obj = self.template_env.get_template(template_file)
            html_content = template_obj.render(**context)
            
            # 4. Executa o renderer do Playwright + FFmpeg
            logger.info(f"Renderizando vídeo {video_id} em: {output_path}")
            
            # Duração fixa de 15s (15000ms) conforme a timeline dos templates
            asyncio.run(render_video(
                html_content=html_content, 
                output_path=output_path, 
                audio_path=abs_audio_path,
                duration=15000
            ))
            
            status = "completed"
            error_msg = None
            
        except Exception as e:
            logger.error(f"Erro crítico ao renderizar vídeo: {str(e)}", exc_info=True)
            status = "failed"
            error_msg = str(e)

        # 5. Retorna o resultado
        result = {
            "video_id": video_id,
            "template": template,
            "status": status,
            "king_name": context.get("king_name"),
            "amount": context.get("amount"),
            "created_at": datetime.utcnow().isoformat(),
            "video_path": output_path
        }
        
        if error_msg:
            result["error"] = error_msg
            
        return result


class InstagramPublisher:
    """Handles publishing videos to Instagram."""
    
    def __init__(self, access_token: str, account_id: str):
        self.access_token = access_token
        self.account_id = account_id
        self.base_url = "https://graph.instagram.com/v18.0"
    
    def publish_video(self, video_data: Dict[str, Any]) -> bool:
        """
        Publish video to Instagram.
        """
        try:
            video_path = video_data.get("video_path")
            
            if not video_path or not os.path.exists(video_path):
                logger.error("Arquivo de vídeo não encontrado para publicação.")
                return False
                
            # Log de simulação de upload
            logger.info(f"🚀 Iniciando publicação no Instagram...")
            logger.info(f"📁 Arquivo: {video_path}")
            logger.info(f"📝 Legenda: 🎬 {video_data.get('king_name')} acabou de faturar R$ {video_data.get('amount')}!")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing video: {str(e)}")
            return False