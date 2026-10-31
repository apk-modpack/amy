"""Backend LlamaCpp para inferencia local directa sobre el fichero GGUF.

Modo Portátil nativo: Utiliza el binario embebido `bin/llama/llama-server.exe`
incluido en el propio proyecto, garantizando compatibilidad total con cualquier CPU
(incluido Intel Sandy Bridge / i7-2600 sin AVX2) sin requerir Ollama instalado.
"""

import atexit
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional

import httpx

from wiki_agent.llm.base import LLMBackend

logger = logging.getLogger(__name__)

LLAMA3_STOP_TOKENS = [
    "<|start_header_id|>",
    "<|end_header_id|>",
    "<|eot_id|>",
    "<|eom_id|>",
]


class LlamaCppBackend(LLMBackend):
    """Backend de LLM 100% portable para modelos GGUF."""

    def __init__(
        self,
        model_path: str,
        temperature: float = 1.5,
        min_p: float = 0.1,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        verbose: bool = False,
        port: int = 8089,
    ):
        self._model_path = Path(model_path).resolve()
        self.temperature = temperature
        self.min_p = min_p
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self.port = port
        self.base_url = f"http://127.0.0.1:{self.port}"

        self._server_process: Optional[subprocess.Popen] = None
        self._client = httpx.Client(base_url=self.base_url, timeout=300.0)

        # Buscar binario local embebido
        self._project_root = Path(__file__).resolve().parent.parent.parent.parent
        self._embedded_bin = self._project_root / "bin" / "llama" / "llama-server.exe"

        logger.info(
            "LlamaCppBackend configurado. model_path=%s | portable_bin=%s | n_ctx=%d",
            self._model_path, self._embedded_bin.exists(), n_ctx
        )

    def _kill_existing_server_on_port(self):
        """Si ya existe un proceso escuchando en el puerto configurado, lo termina para evitar usar instancias huérfanas o con flags obsoletos."""
        try:
            out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            target_suffix = f":{self.port}"
            for line in out.splitlines():
                if target_suffix in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = int(parts[-1])
                    if pid > 0:
                        logger.warning("Terminando proceso previo huérfano (PID %d) en puerto %d...", pid, self.port)
                        try:
                            if os.name == "nt":
                                subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            else:
                                os.kill(pid, 9)
                        except Exception as e:
                            logger.debug("No se pudo terminar PID %d: %s", pid, e)
            time.sleep(0.5)
        except Exception as e:
            logger.debug("Error verificando procesos previos en puerto %d: %s", self.port, e)

    def _ensure_server_running(self):
        """Asegura que el servidor portátil local está iniciado y el modelo cargado."""
        if self._is_server_healthy() and self._server_process is not None:
            return

        # Si hay un servidor huérfano escuchando en el puerto pero no lo iniciamos nosotros, cerrarlo
        self._kill_existing_server_on_port()

        if not self._model_path.exists():
            raise FileNotFoundError(f"Fichero GGUF no encontrado: {self._model_path}")

        bin_path = str(self._embedded_bin) if self._embedded_bin.exists() else "llama-server"

        cmd = [
            bin_path,
            "-m", str(self._model_path),
            "--port", str(self.port),
            "-c", str(self.n_ctx),
            "-np", "1",
            "--jinja",
        ]

        logger.info("Iniciando motor portable llama-server: %s", " ".join(cmd))
        self._server_process = subprocess.Popen(
            cmd,
            cwd=str(self._project_root),
            stdout=subprocess.DEVNULL if not self.verbose else None,
            stderr=subprocess.DEVNULL if not self.verbose else None,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        # Registrar cierre limpio al terminar el proceso de Python
        atexit.register(self.shutdown)

        # Esperar a que el modelo cargue y el endpoint responda ok
        max_attempts = 40
        for i in range(max_attempts):
            time.sleep(1.0)
            if self._is_server_healthy():
                logger.info("Motor llama-server iniciado y listo en intento %d.", i + 1)
                return

        raise TimeoutError("El motor local llama-server no respondió a tiempo durante la carga del modelo.")

    def _is_server_healthy(self) -> bool:
        """Verifica si el servidor local ya está escuchando y listo (status 'ok')."""
        try:
            resp = self._client.get("/health", timeout=1.5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status") == "ok"
            return False
        except Exception:
            return False

    def shutdown(self):
        """Detiene el proceso del servidor local al salir."""
        if self._server_process is not None:
            logger.info("Deteniendo motor llama-server local...")
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=3.0)
            except Exception:
                try:
                    self._server_process.kill()
                except Exception:
                    pass
            self._server_process = None

    @property
    def model_name(self) -> str:
        return self._model_path.name

    def is_available(self) -> bool:
        """Comprueba si el archivo GGUF existe y si disponemos del ejecutable."""
        return self._model_path.exists() and (self._embedded_bin.exists() or bool(shutil.which("llama-server")))

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True,
        stream_callback: Optional[Callable[[str], None]] = None,
        bytes_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        self._ensure_server_running()

        payload = {
            "messages": messages,
            "temperature": self.temperature,
            "min_p": self.min_p,
            "stop": LLAMA3_STOP_TOKENS,
            "stream": stream,
        }

        if stream:
            return self._chat_streaming(payload, stream_callback, bytes_callback)
        else:
            return self._chat_blocking(payload)

    def _chat_streaming(
        self,
        payload: Dict[str, Any],
        stream_callback: Optional[Callable[[str], None]],
        bytes_callback: Optional[Callable[[int], None]],
    ) -> str:
        full_response = []
        bytes_received = 0

        with self._client.stream("POST", "/v1/chat/completions", json=payload, timeout=300.0) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Error HTTP del servidor portable: {response.status_code}")

            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    token = chunk["choices"][0]["delta"].get("content", "")
                    if token:
                        bytes_received += len(token.encode("utf-8"))
                        if stream_callback:
                            stream_callback(token)
                        else:
                            print(token, end="", flush=True)
                        full_response.append(token)
                        if bytes_callback:
                            bytes_callback(bytes_received)
                except Exception:
                    continue

        if not stream_callback:
            print()

        return "".join(full_response)

    def _chat_blocking(self, payload: Dict[str, Any]) -> str:
        resp = self._client.post("/v1/chat/completions", json=payload, timeout=300.0)
        if resp.status_code != 200:
            raise RuntimeError(f"Error HTTP del servidor portable: {resp.status_code}")
        data = resp.json()
        return data["choices"][0]["message"].get("content", "")
