import numpy as np
import ollama # type:ignore
import time
import cv2 # type:ignore
import os


# =========================
# CONFIGURACIÓN
# =========================

IMAGE_PATH = "test_triangulos.jpg"  # 
PROCESSED_PATH = "img_procesada.jpg"

MODELS = {
    "Qwen2.5-VL-7B": "qwen2.5vl:7b",
    "MiniCPM-V": "minicpm-v:latest"
}

TEMPERATURE = 0.1

# =========================
# PREPROCESAMIENTO
# =========================

def preprocess_image(input_path, output_path, rotate_degrees=0):
    image = cv2.imread(input_path)

    # 1️⃣ Escalar imagen
    image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # 2️⃣ Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3️⃣ Aumentar contraste (CLAHE suave)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # 4️⃣ Binarización simple
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 5️⃣ Rotación opcional (si sabes que la foto viene girada)
    if rotate_degrees != 0:
        (h, w) = thresh.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, rotate_degrees, 1.0)
        thresh = cv2.warpAffine(thresh, M, (w, h))

    cv2.imwrite(output_path, thresh)

    
# =========================
# VALIDAR IMAGEN
# =========================

if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError("La imagen no existe en la ruta especificada")

print("\nPreprocesando imagen...\n")
preprocess_image(IMAGE_PATH, PROCESSED_PATH)

# =========================
# PROMPT DIRECTO OPTIMIZADO
# =========================

PROMPT = """
Estás resolviendo un problema de geometría.

La imagen contiene un enunciado con cuatro subejercicios: a), b), c) y d).

En cada subejercicio se presenta una figura geométrica con algunos ángulos conocidos y algunos ángulos desconocido.

Tu objetivo es:

1. Analizar cuidadosamente cada figura.
2. Identificar las relaciones geométricas (ángulos suplementarios, complementarios, opuestos por el vértice, suma de ángulos en triángulo, líneas paralelas, etc.).
3. Resolver cada subejercicio por separado.
4. Calcular el valor del o los ángulos desconocido en cada caso.
 
Responde exactamente en este formato:

a)
- Procedimiento:
- Resultado final:

b)
- Procedimiento:
- Resultado final:

c)
- Procedimiento:
- Resultado final:

d)
- Procedimiento:
- Resultado final:

No describas la imagen.
No repitas el enunciado.
Ve directamente a la resolución matemática.
"""


# =========================
# FUNCIÓN DE EVALUACIÓN
# =========================

def evaluar_modelo(model_name, model_id, image_path):
    print("\n" + "="*60)
    print(f"MODELO: {model_name}")
    print("="*60)

    inicio = time.time()

    response = ollama.chat(
        model=model_id,
        messages=[
            {
                "role": "user",
                "content": PROMPT,
                "images": [image_path]
            }
        ],
        options={
            "temperature": TEMPERATURE,
            "num_predict": 1024
        }
    )

    respuesta = response["message"]["content"]

    print("\n🧮 RESPUESTA:\n")
    print(respuesta)

    fin = time.time()
    tiempo = round(fin - inicio, 2)

    print(f"\n⏱ Tiempo total: {tiempo} segundos")

    return {
        "respuesta": respuesta,
        "tiempo": tiempo
    }


# =========================
# EJECUCIÓN
# =========================

resultados = {}

for nombre, modelo in MODELS.items():
    try:
        #resultados[nombre] = evaluar_modelo(nombre, modelo, IMAGE_PATH)
        resultados[nombre] = evaluar_modelo(nombre, modelo, PROCESSED_PATH)
    except Exception as e:
        print(f"\n❌ Error con {nombre}: {e}")

# =========================
# RESUMEN FINAL
# =========================

print("\n" + "="*60)
print("RESUMEN DE TIEMPOS")
print("="*60)

for nombre, data in resultados.items():
    print(f"{nombre}: {data['tiempo']} segundos")