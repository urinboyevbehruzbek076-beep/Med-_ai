from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    name: str
    phone: str
    role: str  # "user", "pharmacy", "courier"
    lat: Optional[float] = None
    lon: Optional[float] = None
