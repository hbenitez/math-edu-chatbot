# Guía Matemático de la Nube: Socratic AI Tutor

An offline-first educational chatbot designed for rural Colombia. It uses local AI to guide students through mathematical problems using the Socratic method, focusing on pedagogical identification rather than direct answers.

> 📦 **MathBot moved.** The standalone Gradio tutors (`text.py` / `visual.py`) that
> used to live under `mathbot/` are now their own MIT-licensed repository:
> **https://github.com/hbenitez/mathbot**

## 🚀 Installation

### Prerequisites
- **Ollama:** [Install Ollama](https://ollama.ai/)
- **Model:** Download the multimodal model:
  ```bash
  ollama pull gemma3n:e4b
  ```
- **Python:** 3.10+

### Setup
1. Clone the repository and enter the project directory:
   ```bash
   cd math_edu_chatbot
   ```
2. Create and activate the virtual environment:
   ```bash
   make create_environment
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🏗️ Codebase Structure

- `math_edu_chatbot/server/app.py`: FastAPI backend handling chat history, image processing, and Ollama integration.
- `math_edu_chatbot/client/index.html`: Lightweight frontend with chat history persistence.
- `math_edu_chatbot/server/test_gemma_vision.py`: CLI testing tool for multimodal capabilities.
- `docs/docs/architecture-prompt.md`: Original design document for the "Classroom Cloud" architecture.

## 🧠 Socratic Prompting Strategy

The system uses a **Phase-based Socratic Prompt**:
1. **Description & Identification:** The model must first describe the image content and read labels (a, b, c, d) to ground its response in reality.
2. **Pedagogical Questions:** Instead of solving, it asks 2-3 questions following the Polya Method (e.g., "What data can you see?", "What is the problem asking?").
3. **Progressive Guidance:** Only after 3+ exchanges or demonstrated reasoning can the model provide direct hints toward the solution.

## 🖼️ Multimodal Model: Gemma 3 Nano (4B)

The project utilizes `gemma3n:e4b`, a 4-billion parameter multimodal model optimized for efficiency.
- **Why 4B?** It balances the need for visual understanding with the constraint of running on low-end hardware (teacher's laptop) without a dedicated GPU.
- **Inference Config:**
  - `Temperature: 0.1` (Strictly controlled to prevent creative hallucinations).
  - `num_ctx: 4096` (Ensures enough memory for image-text context).

## 🧪 Test Results & Hallucinations

### Successes
- **Pedagogical Tone:** High adherence to the "Colombian Teacher" persona and Socratic method.
- **Context Persistence:** Successfully maintains history across multimodal and text turns.

### The Hallucination Issue
During development, the model (4B) initially misidentified a page of triangles as "rectangles and squares" or "area problems" not present in the text.
- **Root Cause:** Small vision-language models can have weak grounding. When visual "confidence" is low, the model defaults to common training patterns (like area/perimeter) instead of performing strict OCR.
- **Current Fix:** We implemented **"Grounded Prompting"**, which forces the model to look for specific markers (a, b, c, d) and describe figures before interpreting them.

## 🛠️ Further Work
- **Visual Pre-processing:** Implement OpenCV-based edge detection or contrast enhancement before sending images to Ollama to help the small model "see" thin lines in textbook scans.
- **OCR Pre-step:** Use a dedicated lightweight OCR engine (like Tesseract) to extract text and feed it as a "caption" to the multimodal model to eliminate text-reading hallucinations.
- **Model Quantization:** Explore further quantization to increase inference speed on older dual-core CPUs found in rural schools.

---