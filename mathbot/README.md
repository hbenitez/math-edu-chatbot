# 🧮 MathBot

Tutor de matemáticas basado en IA local (Ollama) con interfaz Gradio. Incluye dos modos: chat de texto y chat multimodal (texto + imagen).

## Scripts

### `text.py` — Chat de texto
Chatbot socrático que guía a estudiantes de 8 a 14 años a resolver problemas matemáticos sin dar la respuesta directa. Usa LangChain con el modelo `llama3.2` a través de Ollama y renderiza fórmulas en LaTeX.

```bash
uv run text.py
```

### `visual.py` — Chat multimodal (texto + imagen)
Chatbot que recibe fotos de problemas matemáticos (desde el libro o cuaderno), transcribe el contenido, identifica qué se pide y resuelve paso a paso. Usa el modelo `qwen2.5vl:7b` con la librería `ollama` directamente. Incluye panel para subir/pegar imágenes y un historial de conversación.

```bash
uv run visual.py
```

Ambos scripts lanzan una interfaz web en `http://localhost:7860`.

## Requisitos previos

- [uv](https://docs.astral.sh/uv/) instalado (gestiona Python y las dependencias)
- [Ollama](https://ollama.ai/) instalado y corriendo
- Modelos descargados:
  ```bash
  ollama pull llama3.2        # para text.py
  ollama pull qwen2.5vl:7b    # para visual.py
  ```

> uv se encarga de Python (se requiere 3.10+); no hace falta instalarlo aparte.

## Instalación

uv crea el entorno virtual e instala las dependencias declaradas en
`pyproject.toml` (fijadas en `uv.lock`) con un solo comando:

```bash
uv sync
```

Luego ejecuta cualquiera de los scripts con `uv run` (activa el entorno
automáticamente):

```bash
uv run text.py      # chat de texto
uv run visual.py    # chat multimodal
```

## Documentación

- 📘 **[Guía de despliegue "Classroom Cloud"](docs/deployment-classroom-cloud.md)** —
  cómo usar MathBot en una escuela rural: la laptop del docente como servidor local
  (Ollama), una red Wi-Fi sin Internet y los teléfonos de los estudiantes como clientes.
- 🔎 **[Enfoques para mejorar la tutoría socrática](docs/socratic-tutor-improvement-approaches.md)** —
  análisis de las fallas del tutor con modelos pequeños y tres soluciones
  complementarias (pipeline con verificador, RLHF/DPO y destilación).
- 🛠️ **[Plan de implementación del Enfoque 1 (LangGraph)](docs/approach1-langgraph-implementation-plan.md)** —
  plan detallado para reconstruir el tutor como un pipeline de agentes en LangGraph
  con un verificador determinista (SymPy).
