# 🧮 MathBot

Tutor de matemáticas basado en IA local (Ollama) con interfaz Gradio. Incluye dos modos: chat de texto y chat multimodal (texto + imagen).

## Scripts

### `text.py` — Chat de texto
Chatbot socrático que guía a estudiantes de 8 a 14 años a resolver problemas matemáticos sin dar la respuesta directa. Usa LangChain con el modelo `llama3.2` a través de Ollama y renderiza fórmulas en LaTeX.

```bash
python text.py
```

### `visual.py` — Chat multimodal (texto + imagen)
Chatbot que recibe fotos de problemas matemáticos (desde el libro o cuaderno), transcribe el contenido, identifica qué se pide y resuelve paso a paso. Usa el modelo `qwen2.5vl:7b` con la librería `ollama` directamente. Incluye panel para subir/pegar imágenes y un historial de conversación.

```bash
python visual.py
```

Ambos scripts lanzan una interfaz web en `http://localhost:7860`.

## Requisitos previos

- [Ollama](https://ollama.ai/) instalado y corriendo
- Modelos descargados:
  ```bash
  ollama pull llama3.2        # para text.py
  ollama pull qwen2.5vl:7b    # para visual.py
  ```
- Python 3.10+

## Instalación

1. Crear y activar un ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Despliegue en aula sin Internet

Para usar MathBot en una escuela rural —con la laptop del docente como servidor
local (Ollama), una red Wi-Fi sin Internet y los teléfonos de los estudiantes como
clientes— sigue la guía paso a paso:

- 📘 [Guía de despliegue "Classroom Cloud"](docs/deployment-classroom-cloud.md)
