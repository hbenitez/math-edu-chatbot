# Small Open-Weight VLMs for Mathematical & Geometric Analysis

This report identifies six open-weight vision-language models (VLMs) that offer strong performance in high-resolution OCR, LaTeX transcription, and structural diagram understanding, specifically to address hallucination issues encountered with smaller models in the Gemma 3 family.

## Model Recommendations

### 1. Qwen2.5-VL-7B (Alibaba)
*   **Key Feature:** NaViVit (Native Variable Resolution ViT) for processing any resolution and aspect ratio without distortion.
*   **Math/Geometry Strength:** Excels at document understanding and complex mathematical reasoning. Tops benchmarks like MathVista and OCRBench. Specially trained to output precise LaTeX and handle cluttered diagrams.

### 2. InternVL2.5-4B (OpenGVLab)
*   **Key Feature:** Dynamic high-resolution strategy, splitting high-res images into smaller patches to preserve fine details.
*   **Math/Geometry Strength:** Leader in mathematical vision benchmarks. "Zooms in" on small text and fine lines in geometric figures, reducing hallucinations from guessing blurred details.

### 3. MiniCPM-V 2.6 (ModelBest / Tsinghua)
*   **Key Feature:** 8B parameter model designed for low-latency edge deployment while maintaining "Pro" level performance.
*   **Math/Geometry Strength:** Unique visual-linguistic alignment robust for OCR and spatial reasoning. Excellent at extracting structured data from graphs and charts.

### 4. DeepSeek-Janus-Pro-7B (DeepSeek)
*   **Key Feature:** Decoupled visual encoding architecture for comprehension and generation via specialized pathways.
*   **Math/Geometry Strength:** Inherits the strong mathematical logic of the DeepSeek-V3/R1 series. Highly reliable for step-by-step geometric proofs and formula extraction.

### 5. Phi-3.5-Vision-Instruct (Microsoft)
*   **Key Feature:** 4.2B parameter model trained on high-quality synthetic and curated data to maximize dense knowledge reasoning.
*   **Math/Geometry Strength:** Exceptional instruction-following. Reduces hallucinated extra steps by interpreting both text and figures with high precision.

### 6. InternLM-XComposer2.5-7B (Shanghai AI Lab)
*   **Key Feature:** Specialized for high-resolution (up to 4K) image understanding and long-form document interpretation.
*   **Math/Geometry Strength:** Uses a "Global-Local" attention mechanism, critical for geometry where global structure and local markers (like degree symbols) must be seen simultaneously.

---

## Deployment Strategy

For projects where hallucination reduction is the priority:
- **Recommended 7B-8B:** `Qwen2.5-VL-7B` or `DeepSeek-Janus-Pro-7B`.
- **Recommended Small (<5B):** `InternVL2.5-4B`.
