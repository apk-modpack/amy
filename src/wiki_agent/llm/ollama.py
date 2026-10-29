import httpx
import logging
from typing import List, Dict, Any, Iterator, Callable, Optional
from wiki_agent.llm.base import LLMBackend

logger = logging.getLogger(__name__)


class OllamaBackend(LLMBackend):
    """Backend de LLM que usa la API REST local de Ollama.

    Llama a POST /api/chat con el formato de mensajes OpenAI-compatible.
    Usa httpx (ya dependencia del proyecto) sin añadir librerías nuevas.
    """

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434", temperature: float = 0.3):
        self._model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        logger.info(
            "OllamaBackend inicializado. Modelo: %s | base_url: %s | temperature: %.2f",
            model, self.base_url, temperature
        )

    @property
    def model_name(self) -> str:
        return self._model

    def is_available(self) -> bool:
        """Comprueba que Ollama está corriendo y el modelo existe."""
        logger.debug("is_available | Verificando conexión con Ollama en %s/api/tags", self.base_url)
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            logger.debug("is_available | Respuesta HTTP: %d", resp.status_code)
            if resp.status_code != 200:
                logger.warning("is_available | Estado HTTP inesperado: %d", resp.status_code)
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            logger.debug("is_available | Modelos disponibles en Ollama: %s", models)
            # Acepta coincidencia parcial: "llama3.2" coincide con "llama3.2:latest"
            found = any(self._model in m for m in models)
            if found:
                logger.info("is_available | Modelo '%s' encontrado y disponible.", self._model)
            else:
                logger.warning("is_available | Modelo '%s' NO encontrado. Modelos disponibles: %s", self._model, models)
            return found
        except Exception as e:
            logger.error("is_available | Error al conectar con Ollama: %s", e, exc_info=True)
            return False

    def chat(self, messages: List[Dict[str, str]], stream: bool = True, stream_callback: Optional[Callable[[str], None]] = None, bytes_callback: Optional[Callable[[int], None]] = None) -> str:
        """Envía la conversación a Ollama y devuelve la respuesta completa.

        Si stream=True, utiliza stream_callback si se proporciona, 
        de lo contrario imprime los tokens en tiempo real.
        Retorna el texto completo al terminar.
        """
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
            }
        }

        logger.info(
            "chat | Enviando petición a Ollama. Modelo: %s | stream: %s | num_mensajes: %d | temperature: %.2f",
            self._model, stream, len(messages), self.temperature
        )
        logger.debug(
            "chat | PAYLOAD COMPLETO (messages):\n%s",
            "\n".join(
                f"  [{i}] role={m['role']} | chars={len(m['content'])} | preview: {m['content'][:300]}{'...' if len(m['content']) > 300 else ''}"
                for i, m in enumerate(messages)
            )
        )

        if stream:
            return self._chat_streaming(payload, stream_callback, bytes_callback)
        else:
            return self._chat_blocking(payload)

    def _chat_streaming(self, payload: Dict, stream_callback: Optional[Callable[[str], None]] = None, bytes_callback: Optional[Callable[[int], None]] = None) -> str:
        """Streaming de tokens: usa callback o imprime y retorna el texto completo.
        
        Args:
            payload: El payload JSON para la API de Ollama.
            stream_callback: Llamado con cada token recibido.
            bytes_callback: Llamado con el total de bytes acumulados tras cada token.
        """
        import json
        full_response = []
        bytes_received = 0
        token_count = 0

        logger.debug("_chat_streaming | Iniciando stream HTTP hacia %s/api/chat", self.base_url)

        with httpx.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=None  # Sin límite: modelos locales pueden tardar indefinidamente
        ) as resp:
            resp.raise_for_status()
            logger.debug("_chat_streaming | Conexión establecida. HTTP %d. Leyendo tokens...", resp.status_code)
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        token_count += 1
                        bytes_received += len(token.encode("utf-8"))
                        logger.debug(
                            "_chat_streaming | Token #%d | bytes_acumulados=%d | token=%r",
                            token_count, bytes_received, token
                        )
                        if stream_callback:
                            stream_callback(token)
                        else:
                            print(token, end="", flush=True)
                        full_response.append(token)
                        if bytes_callback:
                            bytes_callback(bytes_received)
                    if chunk.get("done"):
                        # Log de estadísticas finales del modelo si están disponibles
                        logger.info(
                            "_chat_streaming | Stream completado. Tokens: %d | Bytes: %d | done_reason: %s",
                            token_count, bytes_received, chunk.get("done_reason", "N/A")
                        )
                        if "prompt_eval_count" in chunk or "eval_count" in chunk:
                            logger.debug(
                                "_chat_streaming | Stats Ollama — prompt_tokens: %s | eval_tokens: %s | eval_duration_ns: %s",
                                chunk.get("prompt_eval_count", "N/A"),
                                chunk.get("eval_count", "N/A"),
                                chunk.get("eval_duration", "N/A"),
                            )
                        break
                except json.JSONDecodeError as e:
                    logger.warning("_chat_streaming | JSON decode error en línea: %r — %s", line[:100], e)
                    continue

        full_text = "".join(full_response)
        if not stream_callback:
            print()  # newline al terminar el stream
        logger.debug("_chat_streaming | Respuesta completa ensamblada (%d chars):\n%s", len(full_text), full_text)
        return full_text

    def _chat_blocking(self, payload: Dict) -> str:
        """Llamada bloqueante: espera la respuesta completa antes de retornar."""
        logger.debug("_chat_blocking | Enviando petición bloqueante a %s/api/chat", self.base_url)
        payload["stream"] = False
        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=None  # Sin límite: modelos locales pueden tardar indefinidamente
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            logger.info("_chat_blocking | Respuesta recibida. Longitud: %d chars", len(content))
            logger.debug("_chat_blocking | Respuesta completa:\n%s", content)
            return content
        except httpx.HTTPStatusError as e:
            logger.error(
                "_chat_blocking | Error HTTP %d al llamar a Ollama: %s",
                e.response.status_code, e, exc_info=True
            )
            raise
        except Exception as e:
            logger.error("_chat_blocking | Error inesperado: %s", e, exc_info=True)
            raise
