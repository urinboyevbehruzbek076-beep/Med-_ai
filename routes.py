import os
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# --- MODELLAR VA MA'LUMOTLAR (Database o'rniga) ---
class UserRegister(BaseModel):
    phone: str
    name: str
    role: str
    lat: float
    lon: float

USERS = {}
ORDERS = []
DRUGS_DATA = [
    {"id": 1, "name": "Sitramon", "pharmacy": "Dori-Darmon", "price": 5000, "count": 10},
    {"id": 2, "name": "Paratsetamol", "pharmacy": "Arzon Apteka", "price": 3000, "count": 5}
]
PHARMACY_INFO = {"Dori-Darmon": {"address": "Toshkent sh.", "phone": "998901234567"}}

# --- ROUTER VA TEMPLATES ---
router = APIRouter()

base_path = os.path.dirname(file)
templates = Jinja2Templates(directory=os.path.join(base_path, "templates"))

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/auth/register")
async def register(user: UserRegister):
    USERS[user.phone] = {
        "name": user.name,
        "role": user.role,
        "lat": user.lat,
        "lon": user.lon
    }
    return {"status": "success", "message": f"{user.role} sifatida ro'yxatga olindi"}

@router.get("/search")
async def search_drug(q: str):
    results = [d for d in DRUGS_DATA if q.lower() in d['name'].lower()]
    return results

@router.get("/ask")
async def ask_bot(text: str, phone: Optional[str] = None):
    text_lower = text.lower()
    
    # Oddiy muloqot
    smalltalk = {"salom": "Salom!", "hayr": "Xayr!"}
    for key, resp in smalltalk.items():
        if key in text_lower: return {"reply": resp}

    # Kasalliklar bo'yicha qidiruv
    disease_map = {"bosh": "Sitramon", "isitma": "Paratsetamol"}
    for key, drug_name in disease_map.items():
        if key in text_lower:
            matches = [d for d in DRUGS_DATA if drug_name.lower() in d['name'].lower()]
            if matches:
                d = matches[0]
                return {"reply": f"{drug_name} mavjud: {d['pharmacy']}da. Narxi {d['price']} so'm."}
    
    return {"reply": "Tushunmadim, simptomni yozing."}

# Qolgan barcha POST/GET metodlaringizni shu tartibda davom ettirishingiz mumkin