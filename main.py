import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router

app = FastAPI()

# Fayl joylashgan papkani aniqlash (Ikkita pastki chiziq bilan!)
base_path = os.path.dirname(os.path.abspath(__file__))

# Static fayllar papkasi mavjudligini tekshirish va ulash
static_path = os.path.join(base_path, "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

app.mount("/static", StaticFiles(directory=static_path), name="static")

# Routerni ulash
app.include_router(router)

# Vercel uchun
handler = app