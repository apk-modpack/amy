from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from wiki_agent.models import WikiPage, SearchResult


class BaseWikiBackend(ABC):
    """Interfaz abstracta que define las operaciones de almacenamiento de la Wiki."""

    @abstractmethod
    def read_page(self, title: str) -> Optional[WikiPage]:
        """Obtiene una pÃ¡gina por su tÃ­tulo."""
        pass

    @abstractmethod
    def write_page(self, page: WikiPage) -> bool:
        """Crea o actualiza una pÃ¡gina en la wiki."""
        pass

    @abstractmethod
    def delete_page(self, title: str) -> bool:
        """Elimina una pÃ¡gina de la wiki."""
        pass

    @abstractmethod
    def list_pages(self, category: Optional[str] = None, tag: Optional[str] = None) -> List[str]:
        """Lista todos los tÃ­tulos de pÃ¡ginas, opcionalmente filtrados por categorÃ­a o tag."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Busca texto o conceptos dentro de la wiki."""
        pass

    @abstractmethod
    def get_backlinks(self, title: str) -> List[str]:
        """Obtiene las pÃ¡ginas que enlazan al tÃ­tulo indicado."""
        pass

    @abstractmethod
    def get_all_pages(self) -> List[WikiPage]:
        """Obtiene todas las pÃ¡ginas para anÃ¡lisis o exportaciÃ³n."""
        pass