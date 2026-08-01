from PIL import Image  # type: ignore
import gradio as gr  # type: ignore
import ollama # type: ignore
import io
import re


SYSTEM_PROMPT = """Eres MathBot, un tutor socrático de matemáticas para niños
de 8 a 14 años. Tu misión es que el estudiante APRENDA resolviendo él mismo,
no darle la respuesta hecha.

Cuando recibas una imagen:
1. TRANSCRIBE exactamente el texto y los datos que aparecen en la imagen,
   para confirmar que entendiste bien el problema.
2. IDENTIFICA claramente qué se pide resolver y compártelo con el estudiante.
3. NUNCA des la respuesta ni la resolución completa de inmediato. En su lugar,
   GUÍA al estudiante con preguntas para que él descubra cómo resolverlo.

Reglas de la interacción socrática:
- Haz UNA sola pregunta clara por turno y espera la respuesta del estudiante
  antes de continuar. No adelantes varios pasos de golpe.
- Divide el problema en pasos pequeños y avanza un paso por turno.
- Si el estudiante se equivoca, no lo corrijas dándole la respuesta: dale una
  pista y anímalo ("¡Casi! Pensemos juntos...").
- Si acierta un paso, celébralo ("¡Excelente!") y pasa a la siguiente pregunta.
- Usa lenguaje simple y ejemplos del mundo real (frutas, juguetes, dinero).
- Revela la RESPUESTA FINAL solo después de haber guiado al estudiante por
  todos los pasos y de que él haya participado en el razonamiento.

Reglas de formato:
- Usa siempre LaTeX para las fórmulas: inline $formula$ o bloque $$formula$$
- Si hay varios ejercicios en la imagen, trabájalos en orden, uno a la vez.
- Si un dato no se ve claramente, indícalo y pregúntale al estudiante.
- Responde siempre en español.

Ejemplo de estructura esperada en tu PRIMER mensaje:

**Lo que veo en la imagen:**
[transcripción del problema]

**Lo que se pide:**
[qué hay que encontrar]

**Empecemos juntos:**
[una primera pregunta que invite al estudiante a dar el primer paso]"""

MODEL = "qwen2.5vl:7b"


# ──────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────

def pil_a_bytes(imagen: Image.Image) -> bytes:
    buf = io.BytesIO()
    imagen.save(buf, format="PNG")
    return buf.getvalue()

def limpiar_latex(texto: str) -> str:
    texto = texto.replace("\\\\", "\\")
    texto = texto.replace("\\[", "$$").replace("\\]", "$$")
    texto = texto.replace("\\(", "$").replace("\\)", "$")
    return texto

# ──────────────────────────────────────────────
# Función principal
# ──────────────────────────────────────────────

def chat(mensaje, imagen, hist_llm, hist_ui):
    texto = (mensaje or "").strip()
    if not texto and imagen is None:
        return hist_llm, hist_ui, hist_ui, None

    # Reconstruir historial para ollama
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user_msg, bot_msg in hist_llm:
        if user_msg:
            mensajes.append({"role": "user",      "content": user_msg})
        if bot_msg:
            mensajes.append({"role": "assistant", "content": bot_msg})

    # Mensaje actual — con o sin imagen
    if imagen is not None:
        texto_llm = texto if texto else (
            "Por favor: "
            "1) transcribe todo el texto y datos que ves en la imagen, "
            "2) identifica qué se pide resolver, "
            "3) NO resuelvas el ejercicio: en su lugar, hazme UNA primera "
            "pregunta para guiarme a resolverlo yo mismo paso a paso, "
            "4) escribe las fórmulas en LaTeX entre signos de dólar."
        )
        msg_actual = {"role": "user", "content": texto_llm, "images": [pil_a_bytes(imagen)]}
        texto_display = f"📷 {texto if texto else 'Resolver problema de la imagen'}"
    else:
        msg_actual = {"role": "user", "content": texto}
        texto_display = texto

    mensajes.append(msg_actual)

    try:
        resp = ollama.chat(model=MODEL, messages=mensajes)
        reply = resp["message"]["content"] if isinstance(resp, dict) else resp.message.content
        reply = limpiar_latex(reply)    
    except Exception as e:
        reply = (
            f"⚠️ Error: {e}\n\n"
            "Verifica que Ollama esté corriendo:\n"
            "  OLLAMA_ORIGINS='*' ollama serve\n\n"
            f"Y que el modelo esté instalado:\n  ollama pull {MODEL}"
        )

    hist_llm = hist_llm + [(texto_display, reply)]
    hist_ui  = hist_ui  + [
        {"role": "user",      "content": texto_display},
        {"role": "assistant", "content": reply},
    ]
    return hist_llm, hist_ui, hist_ui, None


def limpiar():
    return [], [], [], None, ""


# ──────────────────────────────────────────────
# Interfaz
# ──────────────────────────────────────────────

with gr.Blocks(title="MathBot") as demo:

    hist_llm_state = gr.State([])
    hist_ui_state  = gr.State([])

    gr.Markdown("# 🧮 MathBot — Tu tutor de matemáticas")
    gr.Markdown("¡Hola! Soy MathBot. Escribe tu problema o sube una foto y te ayudo paso a paso.")

    with gr.Row(equal_height=True):

        with gr.Column(scale=1, min_width=240):
            gr.Markdown("### 📷 Foto del problema")
            imagen_input = gr.Image(
                label="Sube, arrastra o pega (Ctrl+V)",
                type="pil",
                height=260,
            )
            gr.Markdown(f"<small style='color:#888'>Powered by {MODEL}</small>")
            btn_limpiar = gr.Button("🗑 Nueva conversación", variant="secondary", size="sm")

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversación",
                height=460,
                render_markdown=True, 
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                    {"left": "$",  "right": "$",  "display": False},
                ],
            )
            with gr.Row():
                texto_input = gr.Textbox(
                    placeholder="Escribe tu pregunta aquí...",
                    label="",
                    lines=2,
                    max_lines=4,
                    scale=5,
                    show_label=False,
                )
                btn_enviar = gr.Button("Enviar", variant="primary", scale=1, min_width=80)

    gr.Markdown("### Ejemplos")
    gr.Examples(
        examples=[
            "No entiendo cómo dividir fracciones",
            "¿Cómo calculo el área de un triángulo?",
            "Tengo que resolver: 3x + 5 = 20",
        ],
        inputs=texto_input,
    )

    def enviar(msg, img, h_llm, h_ui):
        h_llm_new, h_ui_new, chat_new, img_limpia = chat(msg, img, h_llm, h_ui)
        return h_llm_new, h_ui_new, chat_new, img_limpia, ""

    btn_enviar.click(
        fn=enviar,
        inputs=[texto_input, imagen_input, hist_llm_state, hist_ui_state],
        outputs=[hist_llm_state, hist_ui_state, chatbot, imagen_input, texto_input],
    )
    texto_input.submit(
        fn=enviar,
        inputs=[texto_input, imagen_input, hist_llm_state, hist_ui_state],
        outputs=[hist_llm_state, hist_ui_state, chatbot, imagen_input, texto_input],
    )
    btn_limpiar.click(
        fn=limpiar,
        outputs=[hist_llm_state, hist_ui_state, chatbot, imagen_input, texto_input],
    )

demo.launch(server_name="0.0.0.0", server_port=7860)