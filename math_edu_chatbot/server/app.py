import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama
from typing import List, Optional
import logging
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gemma3n:e4b")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
TOP_P = float(os.getenv("TOP_P", 0.9))

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Guía Matemático de la Nube")

# Habilitar CORS para permitir acceso desde la red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir rutas de archivos estáticos (Frontend)
# La ruta se ajustará dinámicamente según la ubicación del archivo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "client", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "client")

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return """
    <html>
        <head><title>Guía Matemático</title></head>
        <body><h1>Bienvenido al Guía Matemático de la Nube</h1>
        <p>El archivo index.html no se encuentra en la carpeta client.</p></body>
    </html>
    """

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Prompt del sistema para forzar el comportamiento socrático progresivo
        system_prompt = {
            "role": "system",
            "content": (
                "Eres un Tutor de Matemáticas Socrático experto para estudiantes colombianos (6-16 años). "
                "TU REGLA DE ORO: No entregues la respuesta final de inmediato. "
                "FASE 1: Descripción e Identificación. Si el usuario pregunta por una imagen o un problema, comienza describiendo brevemente lo que se observa y cuál es el desafío matemático. "
                "FASE 2: Preguntas Guía. Haz 2 o 3 preguntas que estimulen el pensamiento crítico (ej. '¿Qué datos identificas?', '¿Qué operación crees que necesitamos?'). "
                "FASE 3: Guía Progresiva. Solo tras un intercambio de al menos 3 mensajes o si el estudiante demuestra razonamiento, puedes guiarlo hacia la solución final. "
                "ESTILO: Usa un lenguaje motivador, sencillo y cercano. Sigue el método de Polya."
            )
        }
        
        formatted_messages = [system_prompt] + [m.model_dump() for m in request.messages]
        
        response = ollama.chat(
            model=MODEL_NAME,
            messages=formatted_messages,
            options={
                "temperature": TEMPERATURE,
                "top_p": TOP_P
            }
        )
        
        return {"response": response["message"]["content"]}
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import io
from PIL import Image

@app.post("/api/multimodal")
async def multimodal_endpoint(
    text: Optional[str] = Form(None),
    history: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    start_time = time.time()
    try:
        logger.info(f"Recibida solicitud multimodal: {file.filename}")
        image_data = await file.read()
        
        # Procesar historial si existe
        messages = []
        if history:
            try:
                import json
                history_data = json.loads(history)
                messages = [m for m in history_data if isinstance(m, dict) and "role" in m and "content" in m]
            except Exception as e:
                logger.warning(f"Error parseando historial: {e}")

        # Comprimir imagen para mejorar velocidad
        img = Image.open(io.BytesIO(image_data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        max_size = 1024
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Imagen redimensionada a {new_size}")

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        final_image_bytes = img_byte_arr.getvalue()
        
        # Prompt socrático general mejorado con mayor énfasis en la observación real
        system_prompt = (
            "Eres un Tutor de Matemáticas Socrático experto. "
            "INSTRUCCIÓN CRÍTICA: Primero, lee cuidadosamente TODO el texto que aparece en la imagen. "
            "No inventes problemas de áreas si no los ves. "
            "\nPASO 1: Descripción Objetiva. Describe exactamente qué figuras geométricas y números ves escritos. "
            "(Ej: 'Veo una lista de ejercicios con triángulos', 'Veo una operación de suma'). "
            "\nPASO 2: Identificación del Desafío. Basándote SOLO en el texto de la imagen, identifica qué debe resolver el estudiante. "
            "\nPASO 3: Preguntas Socráticas. Haz 2 preguntas cortas para que el niño empiece a pensar. "
            "\nREGLA: Nunca des la respuesta final. Usa un lenguaje motivador y sencillo para niños colombianos."
        )

        user_content = text or "Hola profe, ¿qué ves en esta imagen y qué debo hacer?"
        
        # Construir mensajes para Ollama
        ollama_messages = [{"role": "system", "content": system_prompt}]
        ollama_messages.extend(messages)
        ollama_messages.append({
            "role": "user",
            "content": user_content,
            "images": [final_image_bytes]
        })
        
        logger.info(f"Llamando a Ollama ({MODEL_NAME}) para análisis general...")
        response = ollama.chat(
            model=MODEL_NAME,
            messages=ollama_messages,
            options={
                "temperature": 0.1,  # Reducimos temperatura para evitar alucinaciones
                "top_p": 0.9,
                "num_ctx": 4096      # Aseguramos suficiente contexto
            }
        )
        
        duration = time.time() - start_time
        logger.info(f"Respuesta multimodal recibida en {duration:.2f}s")
        return {"response": response["message"]["content"]}
    except Exception as e:
        logger.error(f"Error multimodal después de {time.time() - start_time:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Se recomienda ejecutar en 0.0.0.0 para ser accesible desde la red local (Hotspot)
    uvicorn.run(app, host="0.0.0.0", port=8000)
