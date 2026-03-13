import ollama # type:ignore
import os

def test_multimodal():
    image_path = 'test_triangulos.jpg'
    if not os.path.exists(image_path):
        print("Imagen no encontrada.")
        return

    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    print("Enviando imagen a Gemma 3n E4B...")
    try:
        response = ollama.chat(
            model='gemma3n:e4b',
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un Tutor de Matemáticas Socrático. "
                        "INSTRUCCIÓN: Analiza la imagen buscando etiquetas como 'a.', 'b.', 'c.', 'd.' y figuras de TRIÁNGULOS. "
                        "1. Describe qué figuras geométricas ves (específicamente si son triángulos o rectángulos). "
                        "2. Lee el título de la página. "
                        "3. Pregunta al estudiante por cuál de las letras (a, b, c, d) quiere empezar."
                    )
                },
                {
                    "role": "user",
                    "content": "Hola profe, describe qué ves y cómo podemos empezar.",
                    "images": [image_bytes]
                }
            ],
            options={
                "temperature": 0.1,
            }
        )
        print("\n--- RESPUESTA DEL MODELO ---")
        print(response['message']['content'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_multimodal()

    #"Hola profe, ¿me ayudas con este ejercicio de la foto? No me des la respuesta, solo ayúdame a entender qué debo hacer."