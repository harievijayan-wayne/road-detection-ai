import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RoadDamageAI (RoadWatch)"
    VERSION: str = "2.1.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite:///./road_damage.db"
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    REPORTS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    SAMPLE_DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
    
    # AI Engine Thresholds
    CONF_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    PROCESS_EVERY_N_FRAMES: int = 2
    DEVICE: str = "cpu"
    
    # Severity & Priority Defaults
    WEIGHT_AREA: float = 0.30
    WEIGHT_DIMENSION: float = 0.20
    WEIGHT_RISK: float = 0.20
    WEIGHT_CONFIDENCE: float = 0.15
    WEIGHT_PERSISTENCE: float = 0.15

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
os.makedirs(settings.SAMPLE_DATA_DIR, exist_ok=True)
