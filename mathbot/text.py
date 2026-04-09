from langchain_core.messages import HumanMessage, AIMessage, SystemMessage #type:ignore
from langchain_ollama import ChatOllama #type:ignore
import gradio as gr #type:ignore


SYSTEM_PROMPT = """Eres MathBot, un tutor amigable de matemáticas para niños 
de 8 a 14 años. Tus reglas son:

1. NUNCA des la respuesta directa. Guía al niño con preguntas y pistas.
2. Usa lenguaje simple y ejemplos del mundo real (frutas, juguetes, dinero).
3. Si el niño se equivoca, di "¡Casi! Pensemos juntos..." 
4. Si resuelve algo, celebra con entusiasmo: "¡Excelente!"
5. Divide cada problema en pasos pequeños.
6. Para niños de 8-10 años: suma, resta, multiplicación básica.
7. Para niños de 11-14 años: fracciones, álgebra básica, geometría.
8. Si no entiendes la pregunta, pide que la reformule con sus palabras.
9. Responde siempre en español, sin excepción.
10. Cuando escribas fórmulas usa siempre formato LaTeX entre signos de dólar.
    Ejemplos:
    - Inline: $x^2 + y^2 = z^2$
    - Bloque:  $$\frac{a+b}{2}$$"""

#llm = ChatOllama(model="qwen2.5:7b", temperature=0.3)
llm = ChatOllama(model="llama3.2", temperature=0.3)

def chat(message, history):
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for h in history:
        if isinstance(h, dict):
            role = h.get("role", "")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=h[0]))
            if h[1]:
                messages.append(AIMessage(content=h[1]))
                
    messages.append(HumanMessage(content=message))
    response = llm.invoke(messages)
    return response.content

chatbot = gr.Chatbot(
    latex_delimiters=[
        {"left": "$$", "right": "$$", "display": True},
        {"left": "$",  "right": "$",  "display": False}
    ]
)

demo = gr.ChatInterface(
    fn=chat,
    chatbot=chatbot,
    title="MathBot — Tu tutor de matemáticas",
    description="¡Hola! Soy MathBot. Cuéntame qué problema tienes hoy",
    examples=[
        "No entiendo cómo dividir fracciones",
        "¿Cómo calculo el área de un triángulo?",
        "Tengo que resolver: 3x + 5 = 20"
    ]
)

demo.launch(server_name="0.0.0.0", server_port=7860)