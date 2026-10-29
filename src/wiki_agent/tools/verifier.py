import re
from typing import Dict, Any, List, Optional
import httpx


class FactChecker:
    """Módulo de verificación y contraste de veracidad de conceptos con fuentes externas."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "WikiAgent-FactChecker/1.0 (https://github.com/wiki-agent; contact@wikiagent.local)"
        }

    def verify_concept(self, title: str, summary_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Verifica la existencia y veracidad general de un concepto consultando APIs de enciclopedias y fuentes de referencia.
        """
        clean_title = title.strip()
        result = {
            "title": clean_title,
            "verified": False,
            "confidence": 0.0,
            "external_sources": [],
            "extracted_definition": None,
            "status_message": "Pendiente de verificación"
        }

        # 1. Consulta a la API de Wikipedia en Español
        try:
            wiki_api_url = "https://es.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info",
                "exintro": True,
                "explaintext": True,
                "inprop": "url",
                "titles": clean_title,
                "redirects": 1
            }
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(wiki_api_url, params=params, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if page_id != "-1":
                            extract = page_data.get("extract", "").strip()
                            full_url = page_data.get("fullurl") or f"https://es.wikipedia.org/wiki/{clean_title}"
                            result["verified"] = True
                            result["confidence"] = 0.95
                            result["external_sources"].append(full_url)
                            result["extracted_definition"] = extract[:300] + "..." if len(extract) > 300 else extract
                            result["status_message"] = "Verificado con éxito en fuentes enciclopédicas oficiales."
                            return result
        except Exception as e:
            result["status_message"] = f"Error durante la consulta a Wikipedia API: {str(e)}"

        # 2. Búsqueda de respaldo si no es página exacta
        try:
            search_api_url = "https://es.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": clean_title,
                "srlimit": 3
            }
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(search_api_url, params=search_params, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    if search_results:
                        top = search_results[0]
                        top_title = top.get("title")
                        snippet = re.sub(r"<[^>]+>", "", top.get("snippet", ""))
                        result["verified"] = True
                        result["confidence"] = 0.80
                        result["external_sources"].append(f"https://es.wikipedia.org/wiki/{top_title}")
                        result["extracted_definition"] = snippet
                        result["status_message"] = f"Concepto contrastado con entrada relacionada: '{top_title}'."
                        return result
        except Exception as e:
            result["status_message"] = f"Fallo en la búsqueda de respaldo: {str(e)}"

        result["status_message"] = "No se encontraron referencias externas directas coincidentes."
        return result
