import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import router

app = FastAPI()

# Fayl joylashgan papkani aniqlash
base_path = os.path.dirname(file)

# Statik fayllar uchun mutloq yo'l (Vercel uchun muhim)
static_path = os.path.join(base_path, "static")
if not os.path.exists(static_path):
    os.makedirs(static_path) # Xatolik bermasligi uchun papka yaratish

app.mount("/static", StaticFiles(directory=static_path), name="static")
app.include_router(router)

# Vercel handler (ba'zan talab qilinadi)
handler = app