from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional

class LLMBackend(ABC):
    """Clase base abstracta para los backends de LLM."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Devuelve el nombre del modelo configurado."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el backend (API/Servidor) está disponible y el modelo existe."""
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], stream: bool = True, stream_callback: Optional[Callable[[str], None]] = None, bytes_callback: Optional[Callable[[int], None]] = None) -> str:
        """Envía una lista de mensajes al LLM y devuelve la respuesta completa.
        
        Args:
            messages: Lista de diccionarios con 'role' y 'content'.
            stream: Si True, el backend puede hacer streaming de la respuesta a la consola.
            stream_callback: Callback opcional llamado en cada token recibido durante streaming.
            
        Returns:
            El string con la respuesta completa del modelo.
        """
        pass
