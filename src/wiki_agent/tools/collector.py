import re
from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.ingest import DocumentIngestor


class WebCollector:
    """Herramienta para recopilar, limpiar y catalogar contenido web en la Wiki."""

    def __init__(self, manager: WikiKnowledgeManager):
        self.manager = manager
        self.ingestor = DocumentIngestor(manager)

    def fetch_url(
        self,
        url: str,
        custom_title: Optional[str] = None,
        category: str = "Web",
        auto_link: bool = True
    ) -> Dict[str, Any]:
        """Descarga una pÃ¡gina web, elimina elementos no relevantes y la ingesta en la wiki."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WikiAgent/0.1"}
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            return {"status": "error", "message": f"Error al descargar URL {url}: {str(e)}"}

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            tag.decompose()

        page_title = custom_title or (soup.title.string.strip() if soup.title and soup.title.string else url)
        # Extraer texto limpio
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n\n".join(lines[:120])

        content = f"Fuente original: [{url}]({url})\n\n{clean_text}"
        return self.ingestor.ingest_text(
            title=page_title,
            text=content,
            category=category,
            tags=["web", "scraped"],
            source_name=url,
            auto_link=auto_link
        )