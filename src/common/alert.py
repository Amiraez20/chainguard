from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


class FeatureContribution(BaseModel):
    name: str    # nom de la feature
    value: float # valeur observée pour cette entité
    shap: float  # contribution SHAP (> 0 = pousse vers « fraude »)


class Alert(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chain: Literal["ethereum", "bitcoin"]
    entity_type: Literal["wallet", "contract", "btc_tx"]
    address: str
    score: float = Field(ge=0, le=1)
    label: Literal["normal", "suspicious"]
    fraud_type: Literal["phishing", "scam", "hack", "ponzi",
                        "ransomware", "illicit", "unknown"]
    top_features: list[FeatureContribution] = []
    explanation_text: str = ""
    model_version: str
