import os
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# --- MODELLAR ---
class UserRegister(BaseModel):
    phone: str
    name: str
    role: str
    lat: float
    lon: float

# --- MA'LUMOTLAR (Database o'rniga) ---
USERS = {}
ORDERS = []
DRUGS_DATA = [
    {"id": 1, "name": "Sitramon", "pharmacy": "Dori-Darmon", "price": 5000, "count": 10},
    {"id": 2, "name": "Paratsetamol", "pharmacy": "Arzon Apteka", "price": 3000, "count": 5},
    {"id": 3, "name": "Kardiamagnil", "pharmacy": "Grand Pharm", "price": 15000, "count": 8}
]
PHARMACY_INFO = {
    "Dori-Darmon": {"address": "Toshkent sh.", "phone": "998901234567"},
    "Arzon Apteka": {"address": "Samarqand sh.", "phone": "998911112233"}
}

# --- ROUTER VA TEMPLATES ---
router = APIRouter()

base_path = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory= "shablonlar")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # HTML faylingiz ichida {{ pharmacy_info | tojson }} kabi qismlar bo'lgani uchun
    # barcha o'zgaruvchilarni context sifatida yuborish shart:
    return templates.TemplateResponse("index.html", {
        "request": request,
        "pharmacy_info": PHARMACY_INFO,
        "drugs_data": DRUGS_DATA,
        "users": USERS,
        "orders": ORDERS
    })

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
    
    # Oddiy muloqot qismi
    smalltalk = {"salom": "Assalomu alaykum!", "hayr": "Xayr, salomat bo'ling!"}
    for key, resp in smalltalk.items():
        if key in text_lower:
            return {"reply": resp}

    # Kasallik bo'yicha dori tavsiyasi
    disease_map = {"bosh": "Sitramon", "isitma": "Paratsetamol", "yurak": "Kardiamagnil"}
    for key, drug_name in disease_map.items():
        if key in text_lower:
            matches = [d for d in DRUGS_DATA if drug_name.lower() in d['name'].lower()]
            if matches:
                d = matches[0]
                return {"reply": f"{drug_name} bor: {d['pharmacy']}da. Narxi {d['price']} so'm."}
    
    return {"reply": "Tushunmadim, iltimos simptomni yozing (masalan: bosh og'riyapti)."}