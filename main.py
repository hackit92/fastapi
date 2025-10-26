import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from resend import Resend

# ---- Config ----
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

app = FastAPI(
    title="Trending Topic Contact API",
    version="1.0.0",
)

# CORS: pon aquí tu dominio real de la landing
allowed_origins = [
    "http://localhost:3000",
    "https://tu-landing-oficial.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resend_client = Resend(api_key=RESEND_API_KEY)


# ------- Modelos de entrada/salida ---------

class ContactRequest(BaseModel):
    nombre: str
    email: EmailStr
    mensaje: str | None = None

class ContactResponse(BaseModel):
    ok: bool


# ------- Rutas ---------

@app.get("/health")
def health():
    return {"ok": True, "service": "tt-contact-api-fastapi"}

@app.post("/contact", response_model=ContactResponse)
def contact(data: ContactRequest):
    if not RESEND_API_KEY:
        # Esto ayuda en debug si olvidaste setear la variable en Railway
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not configured")

    try:
        # Armamos el HTML del correo
        html_body = f"""
        <h2>Nuevo contacto desde la landing</h2>
        <p><strong>Nombre:</strong> {data.nombre}</p>
        <p><strong>Email:</strong> {data.email}</p>
        <p><strong>Mensaje:</strong></p>
        <p>{data.mensaje or "(sin mensaje)"}</p>
        <hr />
        <p style="font-size:12px;color:#666;">
          Este lead entró vía landing institucional TT.
        </p>
        """

        resend_client.emails.send({
            "from": "Trending Topic <contact@trendingtopic.mx>",
            "to": ["informes@ttgroupmx.com"],
            "reply_to": data.email,
            "subject": "Nuevo lead - Trending Topic Landing",
            "html": html_body,
        })

        return {"ok": True}

    except Exception as e:
        # log server-side (Railway logs)
        print("Error enviando correo:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="No se pudo enviar el mensaje."
        )
