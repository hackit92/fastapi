import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import resend

# ---- Config ----
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

app = FastAPI(
    title="Trending Topic Contact API",
    version="1.1.0",
)

# CORS
allowed_origins = [
    "http://localhost:3000",
    "https://trendingtopic.mx",
    "https://landing.trendingtopic.mx"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar resend
resend.api_key = RESEND_API_KEY


# ------- Modelos ---------
class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    countryCode: str | None = None
    phone: str | None = None
    company: str | None = None
    service: str | None = None
    message: str

class ContactResponse(BaseModel):
    ok: bool


# ------- Rutas ---------
@app.get("/health")
def health():
    return {"ok": True, "service": "tt-contact-api-fastapi"}

@app.post("/contact", response_model=ContactResponse)
def contact(data: ContactRequest):
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not configured")

    html_body = f"""
    <h2>Nuevo contacto desde la landing</h2>
    <p><strong>Nombre:</strong> {data.name}</p>
    <p><strong>Email:</strong> {data.email}</p>
    <p><strong>Teléfono:</strong> {data.countryCode or ''} {data.phone or ''}</p>
    <p><strong>Empresa:</strong> {data.company or '(no especificada)'}</p>
    <p><strong>Servicio de interés:</strong> {data.service or '(no especificado)'}</p>
    <p><strong>Mensaje:</strong></p>
    <p>{data.message or '(sin mensaje)'}</p>
    <hr />
    <p style="font-size:12px;color:#666;">
      Este lead entró vía landing institucional TT.
    </p>
    """

    try:
        resend.Emails.send({
            "from": "Trending Topic <contact@trendingtopic.mx>",
            "to": ["informes@ttgroupmx.com"],
            "reply_to": data.email,
            "subject": "Nuevo lead - Trending Topic Landing",
            "html": html_body,
        })

        return {"ok": True}

    except Exception as e:
        print("Error enviando correo:", repr(e))
        raise HTTPException(status_code=500, detail="No se pudo enviar el mensaje.")
