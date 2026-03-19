import torch # type:ignore
from PIL import Image
from transformers import AutoModel, AutoTokenizer # type:ignore
from torchvision import transforms # type:ignore

MODEL_ID = "OpenGVLab/InternVL2-2B"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)

model = AutoModel.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
).eval()

image = Image.open("test_triangulos.jpg").convert("RGB")

# transformar imagen a tensor
transform = transforms.Compose([
    transforms.Resize((448, 448)),
    transforms.ToTensor(),
])

pixel_values = transform(image).unsqueeze(0)
pixel_values = pixel_values.to(model.device).half()

question = """
Observa cuidadosamente la figura de geometría.

La imagen contiene cuatro subejercicios: a), b), c) y d).  
En cada uno hay ángulos conocidos y ángulos desconocidos.

Resuelve cada subejercicio utilizando propiedades geométricas como:
- ángulos opuestos por el vértice
- ángulos suplementarios
- ángulos complementarios
- suma de ángulos de un triángulo
- líneas paralelas y transversales

Calcula el valor del ángulo desconocido en cada caso.

Responde exactamente con este formato:

a)
Procedimiento:
Resultado final:

b)
Procedimiento:
Resultado final:

c)
Procedimiento:
Resultado final:

d)
Procedimiento:
Resultado final:
"""

generation_config = {
    "max_new_tokens": 512,
    "do_sample": False,
    "temperature": 0.2
}

response = model.chat(
    tokenizer,
    pixel_values,
    question,
    generation_config
)

print(response)