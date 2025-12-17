import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_TITLE = "Video Creation API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API for automated video creation and Instagram publishing"
    
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    VIDEO_OUTPUT_DIR = os.getenv("VIDEO_OUTPUT_DIR", "./output")
    
    # Credenciais BR
    INSTAGRAM_ACCESS_TOKEN_BR = os.getenv("INSTAGRAM_ACCESS_TOKEN_BR")
    INSTAGRAM_ACCOUNT_ID_BR = os.getenv("INSTAGRAM_ACCOUNT_ID_BR")

    # Credenciais GLOBAL
    INSTAGRAM_ACCESS_TOKEN_GLOBAL = os.getenv("INSTAGRAM_ACCESS_TOKEN_GLOBAL")
    INSTAGRAM_ACCOUNT_ID_GLOBAL = os.getenv("INSTAGRAM_ACCOUNT_ID_GLOBAL")

    def ensure_output_dir(self):
        os.makedirs(self.VIDEO_OUTPUT_DIR, exist_ok=True)

    def validate(self):
        # Verifica se pelo menos um par de chaves existe para avisar no log
        br_ok = self.INSTAGRAM_ACCESS_TOKEN_BR and self.INSTAGRAM_ACCOUNT_ID_BR
        global_ok = self.INSTAGRAM_ACCESS_TOKEN_GLOBAL and self.INSTAGRAM_ACCOUNT_ID_GLOBAL
        
        if not br_ok and not global_ok:
            return False
        return True

settings = Settings()