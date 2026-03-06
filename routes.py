from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime

from data import DRUGS_DATA, PHARMACY_INFO, ORDERS, USERS
from models import UserRegister

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # pass pharmacy contact info to template for client-side use
    return templates.TemplateResponse("index.html", {"request": request, "drugs": DRUGS_DATA, "pharmacy_info": PHARMACY_INFO})

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

@router.get("/pharmacy/{name}")
async def pharmacy_profile(name: str):
    results = [d for d in DRUGS_DATA if d['pharmacy'].lower() == name.lower()]
    return results

@router.get("/pharmacy/info/{name}")
async def pharmacy_info(name: str):
    info = PHARMACY_INFO.get(name, {})
    return info

@router.post("/order/create/{drug_id}")
async def create_order(drug_id: int, customer_phone: str, contact_phone: Optional[str] = None):
    if customer_phone not in USERS or USERS[customer_phone]["role"] != "user":
        return {"success": False, "message": "Avval ro'yxatdan o'ting yoki foydalanuvchi sifatida tizimga kiring."}
    if contact_phone is None:
        return {"success": False, "message": "Iltimos, aloqa uchun telefon raqamini kiriting."}

    for drug in DRUGS_DATA:
        if drug["id"] == drug_id and drug["count"] > 0:
            order = {
                "id": len(ORDERS) + 1,
                "drug_name": drug["name"],
                "pharmacy": drug["pharmacy"],
                "customer_phone": customer_phone,
                "contact_phone": contact_phone,
                "status": "pending_pharmacy",
                "courier_id": None
            }
            ORDERS.append(order)
            return {"success": True, "order": order}
    return {"success": False, "message": "Dori qolmagan yoki xato!"}

@router.post("/order/checkout")
async def checkout_order(customer_phone: str, contact_phone: Optional[str] = None, drug_ids: str = ""):
    if customer_phone not in USERS or USERS[customer_phone]["role"] != "user":
        return {"success": False, "message": "Avval ro'yxatdan o'ting yoki foydalanuvchi sifatida tizimga kiring."}
    if contact_phone is None:
        return {"success": False, "message": "Iltimos, aloqa uchun telefon raqamini kiriting."}
    if not drug_ids:
        return {"success": False, "message": "Hech narsa tanlanmagan."}

    ids = [int(x) for x in drug_ids.split(",") if x.isdigit()]
    created = []
    for drug_id in ids:
        for drug in DRUGS_DATA:
            if drug["id"] == drug_id and drug["count"] > 0:
                order = {
                    "id": len(ORDERS) + 1,
                    "drug_name": drug["name"],
                    "pharmacy": drug["pharmacy"],
                    "customer_phone": customer_phone,
                    "contact_phone": contact_phone,
                    "status": "pending_pharmacy",
                    "courier_id": None,
                    "timestamp": datetime.now().isoformat()
                }
                ORDERS.append(order)
                created.append(order)
                break
    if not created:
        return {"success": False, "message": "Hech qanday buyurtma yaratilmadi."}
    return {"success": True, "orders": created}

@router.get("/orders")
async def get_orders(customer_phone: str):
    results = [o for o in ORDERS if o.get("customer_phone") == customer_phone]
    return results

@router.post("/order/confirm/{order_id}")
async def confirm_order(order_id: int):
    for order in ORDERS:
        if order["id"] == order_id:
            order["status"] = "searching_courier"
            return {"success": True, "message": "Kuryerlarga xabar yuborildi"}
    return {"success": False}

@router.post("/order/accept/{order_id}")
async def accept_order(order_id: int, courier_name: str):
    for order in ORDERS:
        if order["id"] == order_id and order["status"] == "searching_courier":
            order["status"] = "on_the_way"
            order["courier_id"] = courier_name
            return {"success": True, "message": "Buyurtma sizga biriktirildi"}
    return {"success": False}

@router.get("/ask")
async def ask_bot(text: str, phone: Optional[str] = None):
    if not phone or phone not in USERS:
        return {"reply": "Iltimos, avval ro'yxatdan o'ting."}

    text_lower = text.lower()
    smalltalk = {
        "salom": "Assalomu alaykum! Qanday yordam bera olaman?",
        "assalomu": "Va alaykum assalom! Savolingizni yozing.",
        "hayr": "Hayr! Tez orada yana murojaat qiling.",
        "qalesan": "Yaxshi, rahmat! Siz-chi?",
    }
    for key, resp in smalltalk.items():
        if key in text_lower:
            return {"reply": resp}

    disease_map = {
        "bosh": "Sitramon",
        "og'riq": "Sitramon",
        "ogriq": "Sitramon",
        "isitma": "Paratsetamol",
        "yurak": "Kardiamagnil",
        "allergiya": "Loratadine",
        "antibiotik": "Amoxicillin",
    }
    for disease_keyword, drug_name in disease_map.items():
        if disease_keyword in text_lower:
            matches = [d for d in DRUGS_DATA if drug_name.lower() in d['name'].lower()]
            if matches:
                d = matches[0]
                return {"reply": f"{drug_name} mavjud: {d['pharmacy']}da {d['count']} dona bor. Narxi {d['price']} so'm."}
            else:
                return {"reply": f"Afsuski, {drug_name} hozir omborda yo'q."}
    responses = {
        "bosh": "Bosh og'rig'i uchun Sitramon bor. Nevropatolog tavsiya etiladi.",
        "isitma": "Isitma uchun Paratsetamol bor. Terapevtga uchrashing.",
        "yurak": "Yurak uchun Kardiamagnil bor. Shifokor ko'rigi shart."
    }
    for key, resp in responses.items():
        if key in text_lower:
            return {"reply": resp}

    return {"reply": "Tushunmadim. Simptomni yozing yoki boshqa savol bering."}
