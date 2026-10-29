import os
import re
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Set
from wiki_agent.backends.base import BaseWikiBackend
from wiki_agent.models import WikiPage, PageMetadata, SearchResult

WIKILINK_REGEX = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")
FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class LocalMarkdownBackend(BaseWikiBackend):
    """Adaptador de Wiki local basado en ficheros Markdown con Frontmatter YAML y caché indexada."""

    def __init__(self, base_path: str = "./data/wiki"):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._cache_loaded = False
        self._page_cache: Dict[str, WikiPage] = {}

    def _load_cache(self):
        if self._cache_loaded:
            return
            
        cache_data = {}
        index_file = self.base_path / "wiki_index.json"
        
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            except Exception:
                cache_data = {}
                
        self._page_cache = {}
        cache_updated = False
        
        for p in self.base_path.rglob("*.md"):
            path_str = str(p)
            try:
                mtime = p.stat().st_mtime
            except FileNotFoundError:
                continue
                
            if path_str in cache_data and cache_data[path_str].get("mtime") == mtime:
                # Parse from cache
                data = cache_data[path_str]["data"]
                meta = PageMetadata(
                    title=data.get("title", p.stem),
                    category=data.get("category", "General"),
                    tags=data.get("tags", []),
                    aliases=data.get("aliases", []),
                    created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
                    source_documents=data.get("source_documents", []),
                    extra=data.get("extra", {})
                )
                page = WikiPage(metadata=meta, content=data.get("content", ""), outgoing_links=data.get("outgoing_links", []))
                self._page_cache[path_str] = page
            else:
                # Parse from file
                page = self._parse_file(p)
                if page:
                    self._page_cache[path_str] = page
                    cache_updated = True
                    
        self._cache_loaded = True
        if cache_updated:
            self._save_cache()
            
    def _save_cache(self):
        index_file = self.base_path / "wiki_index.json"
        cache_data = {}
        for path_str, page in self._page_cache.items():
            try:
                p = Path(path_str)
                if p.exists():
                    cache_data[path_str] = {
                        "mtime": p.stat().st_mtime,
                        "data": {
                            "title": page.metadata.title,
                            "category": page.metadata.category,
                            "tags": page.metadata.tags,
                            "aliases": page.metadata.aliases,
                            "created_at": page.metadata.created_at.isoformat() if page.metadata.created_at else datetime.utcnow().isoformat(),
                            "updated_at": page.metadata.updated_at.isoformat() if page.metadata.updated_at else datetime.utcnow().isoformat(),
                            "source_documents": page.metadata.source_documents,
                            "extra": page.metadata.extra,
                            "content": page.content,
                            "outgoing_links": page.outgoing_links
                        }
                    }
            except Exception:
                continue
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _title_to_path(self, title: str, category: str = "General") -> Path:
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title.strip())
        safe_category = re.sub(r'[\\/*?:"<>|]', "_", category.strip())
        cat_dir = self.base_path / safe_category
        cat_dir.mkdir(parents=True, exist_ok=True)
        return cat_dir / f"{safe_title}.md"

    def _find_file_by_title(self, title: str) -> Optional[Path]:
        self._load_cache()
        target_title = title.strip().lower()
        for path_str, page in self._page_cache.items():
            if page.title.strip().lower() == target_title:
                return Path(path_str)
        return None

    def _extract_links(self, content: str) -> List[str]:
        matches = WIKILINK_REGEX.findall(content)
        seen: Set[str] = set()
        links = []
        for m in matches:
            cleaned = m.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                links.append(cleaned)
        return links

    def _parse_file(self, file_path: Path) -> Optional[WikiPage]:
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        frontmatter_match = FRONTMATTER_REGEX.match(raw_text)
        metadata_dict: Dict = {}
        body = raw_text

        if frontmatter_match:
            try:
                metadata_dict = yaml.safe_load(frontmatter_match.group(1)) or {}
            except Exception:
                metadata_dict = {}
            body = raw_text[frontmatter_match.end():]

        title = metadata_dict.get("title", file_path.stem)
        category = metadata_dict.get("category", file_path.parent.name if file_path.parent != self.base_path else "General")
        tags = metadata_dict.get("tags", [])
        aliases = metadata_dict.get("aliases", [])
        created_at = metadata_dict.get("created_at", datetime.fromtimestamp(file_path.stat().st_ctime))
        updated_at = metadata_dict.get("updated_at", datetime.fromtimestamp(file_path.stat().st_mtime))
        source_docs = metadata_dict.get("source_documents", [])
        extra = {k: v for k, v in metadata_dict.items() if k not in ["title", "category", "tags", "aliases", "created_at", "updated_at", "source_documents"]}

        meta = PageMetadata(
            title=title,
            category=category,
            tags=tags if isinstance(tags, list) else [str(tags)],
            aliases=aliases if isinstance(aliases, list) else [str(aliases)],
            created_at=created_at if isinstance(created_at, datetime) else datetime.utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else datetime.utcnow(),
            source_documents=source_docs if isinstance(source_docs, list) else [str(source_docs)],
            extra=extra
        )

        outgoing = self._extract_links(body)
        return WikiPage(metadata=meta, content=body, outgoing_links=outgoing)

    def read_page(self, title: str) -> Optional[WikiPage]:
        self._load_cache()
        file_path = self._find_file_by_title(title)
        if not file_path:
            return None
        page = self._page_cache.get(str(file_path))
        if page:
            page.backlinks = self.get_backlinks(page.title)
        return page

    def write_page(self, page: WikiPage) -> bool:
        self._load_cache()
        file_path = self._find_file_by_title(page.title)
        if not file_path:
            file_path = self._title_to_path(page.title, page.metadata.category)

        page.metadata.updated_at = datetime.utcnow()
        meta_dict = {
            "title": page.metadata.title,
            "category": page.metadata.category,
            "tags": page.metadata.tags,
            "aliases": page.metadata.aliases,
            "created_at": page.metadata.created_at.isoformat(),
            "updated_at": page.metadata.updated_at.isoformat(),
            "source_documents": page.metadata.source_documents,
            **page.metadata.extra
        }

        yaml_str = yaml.dump(meta_dict, sort_keys=False, allow_unicode=True)
        content_with_frontmatter = f"---\n{yaml_str}---\n\n{page.content.strip()}\n"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_with_frontmatter, encoding="utf-8")
        
        # Update cache
        self._page_cache[str(file_path)] = page
        self._save_cache()
        return True

    def delete_page(self, title: str) -> bool:
        self._load_cache()
        file_path = self._find_file_by_title(title)
        if file_path and file_path.exists():
            file_path.unlink()
            if str(file_path) in self._page_cache:
                del self._page_cache[str(file_path)]
                self._save_cache()
            return True
        return False

    def list_pages(self, category: Optional[str] = None, tag: Optional[str] = None) -> List[str]:
        self._load_cache()
        titles = []
        for page in self._page_cache.values():
            if category and page.metadata.category.lower() != category.lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in page.metadata.tags]:
                continue
            titles.append(page.title)
        return sorted(titles)

    def get_all_pages(self) -> List[WikiPage]:
        self._load_cache()
        return list(self._page_cache.values())

    def get_backlinks(self, title: str) -> List[str]:
        self._load_cache()
        target = title.strip().lower()
        backlinks = []
        for page in self._page_cache.values():
            if page.title.lower() == target:
                continue
            for link in page.outgoing_links:
                if link.strip().lower() == target:
                    backlinks.append(page.title)
                    break
        return sorted(backlinks)

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        self._load_cache()
        q_raw = query.lower()
        
        import string
        q_clean = q_raw.translate(str.maketrans('', '', string.punctuation))
        # Extended stopwords to filter out conversational filler
        stopwords = {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "de", "en", "a", "que", "es", "por", "para", "con",
            "dime", "di", "dijera", "cual", "quien", "como", "cuando", "donde", "nombre", "sistema", "informacion", "quiero",
            "saber", "explicame", "sobre", "del", "al"
        }
        keywords = [w for w in q_clean.split() if w not in stopwords and len(w) > 2]
        
        if not keywords:
            keywords = [q_raw.strip()]
            
        results: List[SearchResult] = []
        max_score = 0.0
        
        for path_str, page in self._page_cache.items():
            # Excluir páginas de categorías internas del sistema
            _internal_categories = {"sistema", "sistema_wiki", "moc", "índice"}
            if page.metadata.category.lower() in _internal_categories:
                continue
            
            score = 0.0
            title_lower = page.title.lower()
            content_lower = page.content.lower()
            
            if q_raw in title_lower:
                score += 20.0
            if q_raw in content_lower:
                score += 10.0
                
            matched_keywords = 0
            for kw in keywords:
                kw_matched = False
                if kw in title_lower:
                    score += 5.0
                    kw_matched = True
                for tag in page.metadata.tags:
                    if kw in tag.lower():
                        score += 3.0
                        kw_matched = True
                for alias in page.metadata.aliases:
                    if kw in alias.lower():
                        score += 4.0
                        kw_matched = True
                
                occurrences = content_lower.count(kw)
                if occurrences > 0:
                    score += min(occurrences * 1.0, 5.0)
                    kw_matched = True
                    
                if kw_matched:
                    matched_keywords += 1

            if keywords and len(keywords) > 1:
                match_ratio = matched_keywords / len(keywords)
                # Penaliza fuertemente si solo coincide con 1 de varias palabras clave (ej: solo "principal" pero no "usuario")
                score *= match_ratio

            if score > max_score:
                max_score = score

            # Initial inclusion threshold
            if score >= 3.0:
                search_term = q_raw if q_raw in content_lower else next((kw for kw in keywords if kw in content_lower), keywords[0] if keywords else q_raw)
                idx = content_lower.find(search_term)
                if idx != -1:
                    start = max(0, idx - 60)
                    end = min(len(page.content), idx + len(search_term) + 60)
                    snippet = f"...{page.content[start:end].strip()}..."
                else:
                    snippet = page.content[:120].strip() + "..."

                results.append(SearchResult(
                    title=page.title,
                    category=page.metadata.category,
                    tags=page.metadata.tags,
                    snippet=snippet,
                    score=score,
                    path=path_str
                ))

        # Dynamic thresholding: keep only results that are reasonably close to the best match
        # or have a solid absolute score.
        if max_score > 0:
            threshold = max(3.0, max_score * 0.3)
            results = [r for r in results if r.score >= threshold]

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]