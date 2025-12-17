import os
import asyncio
import subprocess
import glob
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

def get_ffmpeg_path():
    """Tenta localizar o FFmpeg baixado pelo Playwright ou do sistema."""
    # 1. Tenta no PATH do sistema
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "ffmpeg"
    except FileNotFoundError:
        pass

    # 2. Procura na pasta do Playwright (Windows)
    user_home = os.path.expanduser("~")
    pw_paths = glob.glob(os.path.join(user_home, "AppData", "Local", "ms-playwright", "ffmpeg-*", "ffmpeg.exe"))
    
    if pw_paths:
        return pw_paths[0]
        
    return None

async def render_video(
    html_content: str, 
    output_path: str, 
    audio_path: str = None,
    width: int = 1080, 
    height: int = 1920, 
    duration: int = 15000
) -> str:
    
    output_dir = os.path.dirname(os.path.abspath(output_path))
    temp_html_path = os.path.join(output_dir, f"temp_{os.path.basename(output_path)}.html")
    raw_video_path = os.path.join(output_dir, f"raw_{os.path.basename(output_path)}") # Vídeo sem áudio
    
    # Salva HTML
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    abs_html_url = f"file:///{os.path.abspath(temp_html_path).replace(os.sep, '/')}"
    
    logger.info(f"🎥 Renderizando visual...")
    
    async with async_playwright() as p:
        # 'color_scheme': 'dark' ajuda a evitar o flash branco inicial
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=output_dir,
            record_video_size={"width": width, "height": height},
            color_scheme='dark' 
        )
        
        page = await context.new_page()

        # Garante fundo preto antes de carregar
        await page.add_style_tag(content="html, body { background-color: #000 !important; }")

        await page.goto(abs_html_url, wait_until="load")

        # Aguarda conteúdo estar visível (evita frames em branco no início)
        await page.wait_for_selector('.frame.active', state='visible', timeout=5000)

        # Pequeno delay para garantir que animações CSS iniciaram
        await page.wait_for_timeout(50)

        # Grava a duração completa
        await page.wait_for_timeout(duration)
        await context.close()
        await browser.close()
        
        # Renomeia o vídeo cru
        video_obj = page.video
        if video_obj:
            saved_path = await video_obj.path()
            if os.path.exists(raw_video_path): os.remove(raw_video_path)
            os.rename(saved_path, raw_video_path)
    
    # --- FASE 2: PÓS-PROCESSAMENTO (FFMPEG) ---
    ffmpeg_exe = get_ffmpeg_path()
    
    if not ffmpeg_exe:
        logger.error("FFmpeg não encontrado! O vídeo ficará sem áudio e pode não funcionar no WhatsApp.")
        if os.path.exists(output_path): os.remove(output_path)
        os.rename(raw_video_path, output_path)
        return output_path

    logger.info("🎵 Adicionando áudio e convertendo para WhatsApp...")
    
    # Comando FFmpeg para adicionar áudio e converter para H.264 compatível

    cmd = [
        ffmpeg_exe, "-y",
        "-ss", "0.05",          # Corte mínimo do início (conteúdo já carregado)
        "-r", "60",             # Força 60 FPS de entrada
        "-i", raw_video_path,
    ]

    if audio_path and os.path.exists(audio_path):
        cmd.extend(["-i", audio_path])
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-shortest"])

    # Encoding 60 FPS de alta qualidade
    cmd.extend([
        "-c:v", "libx264",
        "-c:a", "aac",
        "-vf", "fps=60",        # 60 FPS constante
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-g", "60",             # Keyframe a cada 1 segundo (60 frames)
        "-bf", "2",
        "-movflags", "+faststart",
        output_path
    ])
    
    try:
        # Roda o comando silenciosamente
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"✅ Vídeo final pronto: {output_path}")
        
        # Limpa arquivos temporários
        if os.path.exists(raw_video_path): os.remove(raw_video_path)
        if os.path.exists(temp_html_path): os.remove(temp_html_path)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro no FFmpeg: {e}")
        # Se falhar, entrega o vídeo cru
        if os.path.exists(raw_video_path):
            os.rename(raw_video_path, output_path)

    return output_path