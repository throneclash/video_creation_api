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
        # Assume que a pasta 'video_api' é a raiz de execução ou ajusta o caminho
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        if not os.path.exists(template_dir):
            # Fallback se estiver rodando de dentro de video_api
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
        """Configura dados específicos do Template A - Drama."""
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
        """Configura dados específicos do Template B - FOMO."""
        context = self._prepare_common_context(params)
        context.update({
            "hook": params.get("hook", "ÚLTIMA CHANCE<br>ANTES QUE ACABE"),
            "cta": params.get("cta", "NÃO FIQUE<br>DE FORA!"),
            "badge_text": "⏳ TEMPO ESGOTANDO",
            "primary_color": params.get("primary_color", "#ffd700"),
            "accent_color": params.get("accent_color", "#ff6b35"),
            "badge_color": "#ff4400",
            "gold_color": "#ffffff"
        })
        return context
    
    def process_template_c(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configura dados específicos do Template C - Aspiracional."""
        context = self._prepare_common_context(params)
        context.update({
            "hook": params.get("hook", "SEU NOME PODE<br>ESTAR AQUI"),
            "cta": "CONQUISTE<br>SEU LUGAR",
            "badge_text": "✨ FUTURE KING",
            "primary_color": params.get("primary_color", "#bc13fe"),
            "accent_color": params.get("accent_color", "#00d4ff"),
            "badge_color": "#bc13fe",
            "gold_color": params.get("gold_color", "#ffd700")
        })
        return context
    
    def process_video(self, template: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera o vídeo real renderizando o HTML.
        """
        logger.info(f"Iniciando processamento do Template {template}...")
        
        # 1. Prepara o contexto baseado no template
        if template == "A":
            context = self.process_template_a(params)
        elif template == "B":
            context = self.process_template_b(params)
        elif template == "C":
            context = self.process_template_c(params)
        else:
            raise ValueError(f"Unknown template type: {template}")

        video_id = str(uuid.uuid4())
        filename = f"template_{template.lower()}_{video_id}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            # 2. Renderiza o HTML com Jinja2
            template_html = self.template_env.get_template("reel_template.html")
            html_content = template_html.render(**context)
            
            # 3. Executa o renderer do Playwright
            # Como estamos em um contexto síncrono (process_video), usamos asyncio.run
            # para chamar a função assíncrona de renderização
            logger.info(f"Renderizando vídeo {video_id} em: {output_path}")
            
            # Duração fixa de 15s (15000ms) conforme o template HTML
            asyncio.run(render_video(html_content, output_path, duration=15000))
            
            status = "completed"
            error_msg = None
            
        except Exception as e:
            logger.error(f"Erro ao renderizar vídeo: {str(e)}", exc_info=True)
            status = "failed"
            error_msg = str(e)

        # 4. Retorna o resultado
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
            # Placeholder: Em produção, você precisa fazer o upload do binário do vídeo
            # para o container do Facebook antes de publicar.
            # Aqui vamos apenas logar o sucesso da "intenção" de publicar o arquivo real.
            video_path = video_data.get("video_path")
            
            if not video_path or not os.path.exists(video_path):
                logger.error("Arquivo de vídeo não encontrado para publicação.")
                return False
                
            logger.info(f"Preparando publicação do arquivo real: {video_path}")
            logger.info(f"Legenda: 🎬 {video_data.get('king_name')} - {video_data.get('amount')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing video: {str(e)}")
            return False