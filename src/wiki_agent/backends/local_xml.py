"""Backend XML estructurado para la Wiki.

Cada concepto se almacena en un fichero .xml autoexplicativo con la estructura:
    <concept>
      <metadata>...</metadata>
      <content>
        <definition>Texto principal del concepto.</definition>
        <sections>
          <section name="NombreSección">Texto de la sección.</section>
        </sections>
      </content>
      <relations>
        <relation type="relates_to" target="OtroConcepto">Descripción opcional.</relation>
      </relations>
    </concept>

Al arrancar, migra automáticamente los ficheros .md existentes al nuevo formato XML.
"""

import os
import re
import json
import shutil
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from wiki_agent.backends.base import BaseWikiBackend
from wiki_agent.models import WikiPage, PageMetadata, ConceptRelation, SearchResult

WIKILINK_REGEX = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")
FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _prettify_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent="  ")
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip()


class LocalXMLBackend(BaseWikiBackend):
    """Adaptador de Wiki local basado en ficheros XML estructurados con caché indexada."""

    def __init__(self, base_path: str = "./data/wiki"):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._cache_loaded = False
        self._page_cache: Dict[str, WikiPage] = {}
        self._migrate_legacy_markdown()

    def _migrate_legacy_markdown(self):
        migrated_dir = self.base_path / "_migrated"
        migrated_count = 0
        for md_path in list(self.base_path.rglob("*.md")):
            if "_migrated" in md_path.parts:
                continue
            xml_path = md_path.with_suffix(".xml")
            if xml_path.exists():
                dest = migrated_dir / md_path.relative_to(self.base_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(md_path), str(dest))
                continue
            page = self._parse_markdown_file(md_path)
            if page:
                self._write_xml_file(xml_path, page)
                dest = migrated_dir / md_path.relative_to(self.base_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(md_path), str(dest))
                migrated_count += 1
        if migrated_count:
            import logging
            logging.getLogger(__name__).info(
                "LocalXMLBackend: Migrados %d fichero(s) .md al formato XML. Originales en: %s",
                migrated_count, migrated_dir
            )

    def _parse_markdown_file(self, file_path: Path) -> Optional[WikiPage]:
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
        meta = PageMetadata(
            title=title,
            category=category,
            tags=tags if isinstance(tags, list) else [str(tags)],
            aliases=aliases if isinstance(aliases, list) else [str(aliases)],
            created_at=created_at if isinstance(created_at, datetime) else datetime.utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else datetime.utcnow(),
            source_documents=source_docs if isinstance(source_docs, list) else [str(source_docs)],
        )
        wikilinks = list(dict.fromkeys(WIKILINK_REGEX.findall(body)))
        relations = [ConceptRelation(source=title, target=l.strip(), relation_type="relates_to") for l in wikilinks]
        return WikiPage(metadata=meta, content=body.strip(), sections={}, relations=relations, outgoing_links=[r.target for r in relations])

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
        for p in self.base_path.rglob("*.xml"):
            if "_migrated" in p.parts:
                continue
            path_str = str(p)
            try:
                mtime = p.stat().st_mtime
            except FileNotFoundError:
                continue
            cached = cache_data.get(path_str)
            if cached and cached.get("mtime") == mtime:
                page = self._deserialize_cache_entry(cached["data"])
                if page:
                    self._page_cache[path_str] = page
            else:
                page = self._parse_xml_file(p)
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
                    cache_data[path_str] = {"mtime": p.stat().st_mtime, "data": self._serialize_page_for_cache(page)}
            except Exception:
                continue
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _serialize_page_for_cache(self, page: WikiPage) -> dict:
        return {
            "title": page.metadata.title, "category": page.metadata.category,
            "tags": page.metadata.tags, "aliases": page.metadata.aliases,
            "created_at": page.metadata.created_at.isoformat() if page.metadata.created_at else datetime.utcnow().isoformat(),
            "updated_at": page.metadata.updated_at.isoformat() if page.metadata.updated_at else datetime.utcnow().isoformat(),
            "source_documents": page.metadata.source_documents, "extra": page.metadata.extra,
            "content": page.content, "sections": page.sections,
            "relations": [{"source": r.source, "target": r.target, "relation_type": r.relation_type, "description": r.description} for r in page.relations],
            "outgoing_links": page.outgoing_links,
        }

    def _deserialize_cache_entry(self, data: dict) -> Optional[WikiPage]:
        try:
            meta = PageMetadata(
                title=data.get("title", ""), category=data.get("category", "General"),
                tags=data.get("tags", []), aliases=data.get("aliases", []),
                created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
                updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
                source_documents=data.get("source_documents", []), extra=data.get("extra", {}),
            )
            relations = [ConceptRelation(source=r["source"], target=r["target"], relation_type=r.get("relation_type", "relates_to"), description=r.get("description")) for r in data.get("relations", [])]
            return WikiPage(metadata=meta, content=data.get("content", ""), sections=data.get("sections", {}), relations=relations, outgoing_links=data.get("outgoing_links", []))
        except Exception:
            return None

    def _title_to_path(self, title: str, category: str = "General") -> Path:
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title.strip())
        safe_category = re.sub(r'[\\/*?:"<>|]', "_", category.strip())
        cat_dir = self.base_path / safe_category
        cat_dir.mkdir(parents=True, exist_ok=True)
        return cat_dir / f"{safe_title}.xml"

    def _find_file_by_title(self, title: str) -> Optional[Path]:
        self._load_cache()
        target = title.strip().lower()
        # 1. Coincidencia exacta insensible a mayúsculas
        for path_str, page in self._page_cache.items():
            if page.title.strip().lower() == target:
                return Path(path_str)
        # 2. Coincidencia normalizada sin diacríticos/acentos
        import unicodedata
        def _norm(t: str) -> str:
            return ''.join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn')
        target_norm = _norm(title.strip())
        for path_str, page in self._page_cache.items():
            if _norm(page.title.strip()) == target_norm:
                return Path(path_str)
        # 3. Coincidencia por aliases
        for path_str, page in self._page_cache.items():
            for alias in page.metadata.aliases:
                if _norm(alias.strip()) == target_norm:
                    return Path(path_str)
        return None

    def _parse_xml_file(self, file_path: Path) -> Optional[WikiPage]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception:
            return None
        meta_el = root.find("metadata")
        if meta_el is None:
            return None

        def _text(parent, tag, default="") -> str:
            el = parent.find(tag)
            return (el.text or "").strip() if el is not None else default

        def _text_list(parent, tag, item_tag) -> List[str]:
            container = parent.find(tag)
            if container is None:
                return []
            return [(el.text or "").strip() for el in container.findall(item_tag) if el.text]

        title = _text(meta_el, "title") or file_path.stem
        category = _text(meta_el, "category") or "General"
        tags = _text_list(meta_el, "tags", "tag")
        aliases = _text_list(meta_el, "aliases", "alias")
        source_docs = _text_list(meta_el, "source_documents", "source")
        created_raw = _text(meta_el, "created_at")
        updated_raw = _text(meta_el, "updated_at")
        try:
            created_at = datetime.fromisoformat(created_raw) if created_raw else datetime.utcnow()
        except ValueError:
            created_at = datetime.utcnow()
        try:
            updated_at = datetime.fromisoformat(updated_raw) if updated_raw else datetime.utcnow()
        except ValueError:
            updated_at = datetime.utcnow()

        meta = PageMetadata(title=title, category=category, tags=tags, aliases=aliases, created_at=created_at, updated_at=updated_at, source_documents=source_docs)

        content_el = root.find("content")
        definition = ""
        sections: Dict[str, str] = {}
        if content_el is not None:
            def_el = content_el.find("definition")
            definition = (def_el.text or "").strip() if def_el is not None else ""
            sections_el = content_el.find("sections")
            if sections_el is not None:
                for sec in sections_el.findall("section"):
                    sec_name = sec.get("name", "").strip()
                    sec_text = (sec.text or "").strip()
                    if sec_name:
                        sections[sec_name] = sec_text

        relations: List[ConceptRelation] = []
        relations_el = root.find("relations")
        if relations_el is not None:
            for rel in relations_el.findall("relation"):
                rel_type = rel.get("type", "relates_to")
                rel_target = rel.get("target", "").strip()
                rel_desc = (rel.text or "").strip() or None
                if rel_target:
                    relations.append(ConceptRelation(source=title, target=rel_target, relation_type=rel_type, description=rel_desc))

        return WikiPage(metadata=meta, content=definition, sections=sections, relations=relations, outgoing_links=[r.target for r in relations])

    def _write_xml_file(self, file_path: Path, page: WikiPage) -> None:
        root = ET.Element("concept")
        meta_el = ET.SubElement(root, "metadata")
        ET.SubElement(meta_el, "title").text = page.metadata.title
        ET.SubElement(meta_el, "category").text = page.metadata.category
        tags_el = ET.SubElement(meta_el, "tags")
        for tag in page.metadata.tags:
            ET.SubElement(tags_el, "tag").text = tag
        aliases_el = ET.SubElement(meta_el, "aliases")
        for alias in page.metadata.aliases:
            ET.SubElement(aliases_el, "alias").text = alias
        ET.SubElement(meta_el, "created_at").text = page.metadata.created_at.isoformat() if page.metadata.created_at else datetime.utcnow().isoformat()
        ET.SubElement(meta_el, "updated_at").text = page.metadata.updated_at.isoformat() if page.metadata.updated_at else datetime.utcnow().isoformat()
        sources_el = ET.SubElement(meta_el, "source_documents")
        for src in page.metadata.source_documents:
            ET.SubElement(sources_el, "source").text = src

        content_el = ET.SubElement(root, "content")
        def_el = ET.SubElement(content_el, "definition")
        def_el.text = page.content.strip() if page.content else ""
        if page.sections:
            sections_el = ET.SubElement(content_el, "sections")
            for sec_name, sec_text in page.sections.items():
                sec_el = ET.SubElement(sections_el, "section")
                sec_el.set("name", sec_name)
                sec_el.text = sec_text.strip()

        relations_el = ET.SubElement(root, "relations")
        for rel in page.relations:
            rel_el = ET.SubElement(relations_el, "relation")
            rel_el.set("type", rel.relation_type)
            rel_el.set("target", rel.target)
            if rel.description:
                rel_el.text = rel.description

        xml_str = '<?xml version="1.0" encoding="utf-8"?>\n' + _prettify_xml(root)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(xml_str, encoding="utf-8")

    # --- BaseWikiBackend interface ---

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
        page.outgoing_links = page.get_relation_targets()
        self._write_xml_file(file_path, page)
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
            for rel in page.relations:
                if rel.target.strip().lower() == target:
                    backlinks.append(page.title)
                    break
        return sorted(backlinks)

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        self._load_cache()
        import string
        import unicodedata

        def _normalize(text: str) -> str:
            """Elimina acentos/diacríticos y convierte a minúsculas para comparación robusta."""
            return ''.join(
                c for c in unicodedata.normalize('NFD', text.lower())
                if unicodedata.category(c) != 'Mn'
            )

        q_raw = query.lower()
        q_norm = _normalize(query)
        q_clean = q_norm.translate(str.maketrans('', '', string.punctuation))
        stopwords = {"el","la","los","las","un","una","unos","unas","y","o","de","en","a","que","es","por","para","con","dime","di","dijera","cual","quien","como","cuando","donde","nombre","sistema","informacion","quiero","saber","explicame","sobre","del","al"}
        keywords = [w for w in q_clean.split() if w not in stopwords and len(w) > 2]
        if not keywords:
            keywords = [q_norm.strip()]

        results: List[SearchResult] = []
        max_score = 0.0
        _internal_categories = {"sistema", "sistema_wiki", "moc", "índice"}

        for path_str, page in self._page_cache.items():
            if page.metadata.category.lower() in _internal_categories:
                continue
            full_text = page.content
            for sec_text in page.sections.values():
                full_text += " " + sec_text
            for rel in page.relations:
                full_text += " " + rel.target
                if rel.description:
                    full_text += " " + rel.description
            # Normalizar tanto título como contenido para comparación sin acentos
            title_lower = page.title.lower()
            title_norm = _normalize(page.title)
            content_lower = full_text.lower()
            content_norm = _normalize(full_text)
            score = 0.0
            # Coincidencia de la query completa normalizada
            if q_norm in title_norm:
                score += 20.0
            if q_norm in content_norm:
                score += 10.0
            matched_keywords = 0
            for kw in keywords:
                kw_matched = False
                if kw in title_norm:
                    score += 5.0; kw_matched = True
                for tag in page.metadata.tags:
                    if kw in _normalize(tag):
                        score += 3.0; kw_matched = True
                for alias in page.metadata.aliases:
                    if kw in _normalize(alias):
                        score += 4.0; kw_matched = True
                occurrences = content_norm.count(kw)
                if occurrences > 0:
                    score += min(occurrences * 1.0, 5.0); kw_matched = True
                if kw_matched:
                    matched_keywords += 1
            # Penalización suave por keywords no encontradas:
            # solo penaliza si hay más de 1 keyword Y ninguna tiene match en título.
            # Fórmula: en vez de multiplicar por matched/total (que puede llegar a 0.33),
            # usamos sqrt(matched/total) para suavizar el castigo a queries conversacionales.
            if keywords and len(keywords) > 1 and matched_keywords < len(keywords):
                import math
                ratio = matched_keywords / len(keywords)
                score *= math.sqrt(ratio) if ratio > 0 else 0.0
            if score > max_score:
                max_score = score
            if score >= 3.0:
                search_term = q_norm if q_norm in content_norm else next((kw for kw in keywords if kw in content_norm), keywords[0] if keywords else q_norm)
                idx = content_norm.find(search_term)
                if idx != -1:
                    start = max(0, idx - 60)
                    end = min(len(full_text), idx + len(search_term) + 60)
                    snippet = f"...{full_text[start:end].strip()}..."
                else:
                    snippet = full_text[:120].strip() + "..."
                results.append(SearchResult(title=page.title, category=page.metadata.category, tags=page.metadata.tags, snippet=snippet, score=score, path=path_str))

        if max_score > 0:
            threshold = max(3.0, max_score * 0.3)
            results = [r for r in results if r.score >= threshold]
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
