import ollama
import time
import statistics

def benchmark_text(model_name="gemma3n:e4b", prompt="¿Por qué es importante aprender álgebra?"):
    print(f"--- Benchmarking Text Inference ({model_name}) ---")
    latencies = []
    
    for i in range(3):
        start_time = time.time()
        try:
            response = ollama.chat(model=model_name, messages=[{'role': 'user', 'content': prompt}])
            end_time = time.time()
            latency = end_time - start_time
            latencies.append(latency)
            print(f"Run {i+1}: {latency:.2f}s")
        except Exception as e:
            print(f"Error: {e}")
            return

    avg_latency = statistics.mean(latencies)
    print(f"Average Latency: {avg_latency:.2f}s")

if __name__ == "__main__":
    # Asegúrate de que Ollama esté corriendo y el modelo descargado
    try:
        benchmark_text()
    except Exception as e:
        print(f"No se pudo ejecutar el benchmark. ¿Está Ollama corriendo? Error: {e}")
