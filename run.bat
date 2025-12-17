@echo off
TITLE Video Creation API
CLS

echo ================================
echo Video Creation API - Inicializando
echo ================================
echo.

REM 1. Verifica Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado! Instale o Python e marque "Add to PATH".
    pause
    exit /b 1
)

REM 2. Cria/Ativa Ambiente Virtual
if not exist "venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat

REM 3. Instala Dependencias
echo [INFO] Verificando bibliotecas...
pip install -q -r requirements.txt

REM 4. Instala Navegadores do Playwright (Essencial)
echo [INFO] Verificando navegadores...
python -m playwright install chromium

REM 5. Cria pasta de saida
if not exist "output" mkdir output

echo.
echo ================================
echo INICIANDO SERVIDOR
echo ================================
echo.
echo API disponivel em: http://localhost:8000
echo Docs disponiveis em: http://localhost:8000/docs
echo.
echo Pressione Ctrl+C para parar.
echo.

REM 6. Roda a API
python main.py

REM 7. Pausa final para ler erros caso o python feche
echo.
echo O servidor parou. Verifique o erro acima.
pause