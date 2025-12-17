import os
import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def render_video(
    html_content: str, 
    output_path: str, 
    width: int = 1080, 
    height: int = 1920, 
    duration: int = 15000
) -> str:
    """
    Renderiza uma string HTML em um vídeo MP4 usando Playwright.
    
    Args:
        html_content: O código HTML completo a ser renderizado.
        output_path: Caminho final onde o vídeo .mp4 será salvo.
        width: Largura do vídeo (padrão 1080 para Reels).
        height: Altura do vídeo (padrão 1920 para Reels).
        duration: Duração da gravação em milissegundos.
        
    Returns:
        O caminho do arquivo gerado.
    """
    # Define caminhos absolutos
    output_dir = os.path.dirname(os.path.abspath(output_path))
    temp_html_path = os.path.join(output_dir, f"temp_{os.path.basename(output_path)}.html")
    
    # Salva o HTML temporariamente para o navegador ler
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Prepara URL do arquivo local (corrige barras para Windows/Linux)
    abs_html_path = os.path.abspath(temp_html_path)
    abs_html_url = f"file:///{abs_html_path.replace(os.sep, '/')}"
    
    logger.info(f"Iniciando renderização Playwright. HTML: {abs_html_path}")
    
    try:
        async with async_playwright() as p:
            # Inicia o navegador
            browser = await p.chromium.launch(headless=True)
            
            # Cria um contexto com gravação de vídeo habilitada
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=output_dir,
                record_video_size={"width": width, "height": height},
                device_scale_factor=1
            )
            
            page = await context.new_page()
            
            # Carrega o HTML
            logger.info(f"Carregando página: {abs_html_url}")
            await page.goto(abs_html_url)
            
            # Tenta clicar no botão de play
            try:
                # Espera o botão estar presente no DOM
                button = page.locator("button.btn-primary")
                if await button.count() > 0:
                    await button.click()
                    logger.info("Botão de play acionado.")
                else:
                    logger.warning("Botão de play não encontrado. Verifique se o HTML tem button.btn-primary")
            except Exception as e:
                logger.warning(f"Aviso ao tentar clicar no play: {e}")

            logger.info(f"Gravando por {duration/1000} segundos...")
            
            # Aguarda o tempo da animação
            await page.wait_for_timeout(duration)
            
            # Fecha o contexto para finalizar e salvar o arquivo de vídeo
            await context.close()
            await browser.close()
            
            # Renomeia o arquivo aleatório do Playwright para o nome final
            video_obj = page.video
            if video_obj:
                saved_path = await video_obj.path()
                logger.info(f"Vídeo temporário salvo em: {saved_path}")
                
                # Remove o arquivo de destino se já existir (evita erro no Windows)
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                os.rename(saved_path, output_path)
                logger.info(f"Vídeo final movido para: {output_path}")
            else:
                raise Exception("O Playwright não gerou o arquivo de vídeo.")

    except Exception as e:
        logger.error(f"Falha na renderização: {str(e)}")
        # Limpa arquivo temporário em caso de erro também
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        raise e
            
    # Limpeza final (sucesso)
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)
            
    return output_path