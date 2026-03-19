from transformers import AutoModelForCausalLM, AutoProcessor # type:ignore
from PIL import Image
import numpy as np
import torch # type:ignore
import cv2 # type:ignore

MODEL_ID = "microsoft/Phi-3.5-vision-instruct"

print("Cargando modelo...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
    _attn_implementation="eager"
)

processor = AutoProcessor.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)

print("Modelo cargado")

def preprocess_image(image_path):
    """
    Preprocesa la imagen para mejorar la lectura del texto matemático
    """
    img = cv2.imread(image_path)
    # convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # mejorar contraste
    gray = cv2.equalizeHist(gray)
    # reducir ruido
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    # umbral adaptativo
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    return Image.fromarray(thresh)

def ask_model(image, prompt):

    formatted_prompt = f"""
        <|user|>
        <|image_1|>
        {prompt}
        <|end|>
        <|assistant|>
    """

    inputs = processor(
        text=formatted_prompt,
        images=image,
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.2
    )

    generated_ids = output[:, inputs['input_ids'].shape[1]:]

    response = processor.tokenizer.batch_decode(
        generated_ids.cpu(),
        skip_special_tokens=True
    )[0]

    return response

def solve_math_from_image(image_path):

    print("Procesando imagen...")

    image = preprocess_image(image_path)

    print("Extrayendo problema matemático...")

    extract_prompt = """
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
    """

    problem_text = ask_model(image, extract_prompt)

    print("\nProblema detectado:")
    print(problem_text)

    print("\nResolviendo problema...")

    solve_prompt = f"""
        Este es un problema matemático extraído de una imagen:

        {problem_text}

        Resuélvelo paso a paso mostrando los cálculos.
    """

    solution = ask_model(image, solve_prompt)

    return solution

if __name__ == "__main__":

    image_path = "test_triangulos.jpg"

    result = solve_math_from_image(image_path)

    print("\nSolución:\n")
    print(result)