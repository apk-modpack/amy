"""Módulo llm: backends de LLM intercambiables para el agente autónomo."""

from wiki_agent.llm.base import LLMBackend
from wiki_agent.llm.ollama import OllamaBackend
from wiki_agent.llm.llamacpp import LlamaCppBackend
from typing import Dict, Any


def get_llm_backend(config: Dict[str, Any]) -> LLMBackend:
    """Factory: instancia el backend de LLM según la configuración.

    Lee la sección `llm:` del config.yaml:

    Opción A — Ollama (requiere Ollama instalado):
        provider: "ollama"
        model: "llama3.2"
        base_url: "http://localhost:11434"
        temperature: 0.3

    Opción B — llama-cpp-python (portátil, sin dependencias externas):
        provider: "llamacpp"
        model_path: "./models/aaa.gguf"
        temperature: 1.5
        min_p: 0.1
        n_ctx: 4096
        n_gpu_layers: 0    # 0=CPU, -1=GPU completa
    """
    llm_cfg = config.get("llm", {})
    provider = llm_cfg.get("provider", "ollama")

    if provider == "ollama":
        return OllamaBackend(
            model=llm_cfg.get("model", "llama3.2"),
            base_url=llm_cfg.get("base_url", "http://localhost:11434"),
            temperature=llm_cfg.get("temperature", 0.3),
        )

    if provider == "llamacpp":
        return LlamaCppBackend(
            model_path=llm_cfg.get("model_path", "./models/llama3.2-finetuning-v0.4.gguf"),
            temperature=llm_cfg.get("temperature", 1.5),
            min_p=llm_cfg.get("min_p", 0.1),
            n_ctx=llm_cfg.get("n_ctx", 4096),
            n_gpu_layers=llm_cfg.get("n_gpu_layers", 0),
        )

    raise ValueError(
        f"Provider LLM no soportado: '{provider}'. "
        "Opciones disponibles: 'ollama', 'llamacpp'"
    )


__all__ = ["LLMBackend", "OllamaBackend", "LlamaCppBackend", "get_llm_backend"]
