import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.collector import WebCollector
from wiki_agent.tools.ingest import DocumentIngestor
from wiki_agent.tools.verifier import FactChecker


class IngestionQueueItem:
    def __init__(
        self,
        item_id: str,
        title: str,
        source: str,
        source_type: str = "url",
        category: str = "General",
        priority: int = 10,
        status: str = "pending",
        created_at: Optional[str] = None,
        processed_at: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.item_id = item_id
        self.title = title
        self.source = source
        self.source_type = source_type
        self.category = category
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.processed_at = processed_at
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "source": self.source,
            "source_type": self.source_type,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IngestionQueueItem":
        return cls(
            item_id=data.get("item_id", ""),
            title=data.get("title", ""),
            source=data.get("source", ""),
            source_type=data.get("source_type", "url"),
            category=data.get("category", "General"),
            priority=data.get("priority", 10),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            processed_at=data.get("processed_at"),
            error_message=data.get("error_message")
        )


class GlobalIngestionQueueManager:
    """Gestiona la cola de ingesta ÚNICA Y GLOBAL para todo el sistema con historial externalizado en .log."""

    def __init__(self, manager: WikiKnowledgeManager, queue_path: str = "./data/queue/ingest_queue.json"):
        self.manager = manager
        self.queue_file = Path(queue_path).resolve()
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file = self.queue_file.parent / "ingest_history.log"
        self.collector = WebCollector(manager)
        self.ingestor = DocumentIngestor(manager)
        self.fact_checker = FactChecker()

    def _append_history_log(self, item: IngestionQueueItem, details: Optional[str] = None):
        """Registra un concepto ingerido en el archivo .log externo histórico."""
        timestamp = item.processed_at or datetime.utcnow().isoformat()
        log_line = (
            f"[{timestamp}] [COMPLETED] id={item.item_id} | title=\"{item.title}\" | "
            f"category=\"{item.category}\" | source=\"{item.source}\""
        )
        if details:
            log_line += f" | note=\"{details}\""
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    def _count_history_items(self) -> int:
        """Cuenta el total de elementos históricos archivados."""
        if not self.history_file.exists():
            return 0
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def _load_queue(self) -> List[IngestionQueueItem]:
        if not self.queue_file.exists():
            return []
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [IngestionQueueItem.from_dict(item) for item in data]
        except Exception:
            return []

    def _save_queue(self, items: List[IngestionQueueItem]):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in items], f, indent=2, ensure_ascii=False)
        self.sync_wiki_queue_page(items)

    def archive_completed(self) -> int:
        """
        Migra todos los conceptos con estado 'completed' de la cola JSON al archivo de log histórico,
        manteniendo la cola activa lo más liviana posible.
        """
        items = self._load_queue()
        completed = [it for it in items if it.status == "completed"]
        active = [it for it in items if it.status != "completed"]

        for it in completed:
            self._append_history_log(it, details="Archivado de cola activa")

        if len(active) != len(items):
            self._save_queue(active)

        return len(completed)

    def sync_wiki_queue_page(self, items: Optional[List[IngestionQueueItem]] = None):
        """Genera y actualiza la página física de la cola global dentro de la Wiki (data/wiki/Sistema/Cola_Global_Ingesta.md)."""
        if items is None:
            items = self._load_queue()

        pending = [i for i in items if i.status == "pending"]
        processing = [i for i in items if i.status == "processing"]
        failed = [i for i in items if i.status == "failed"]
        historical_total = self._count_history_items()

        lines = [
            "---",
            "title: Cola_Global_Ingesta",
            "category: Sistema",
            "tags:",
            "  - sistema",
            "  - cola",
            "  - ingesta",
            "  - pipeline",
            f"updated_at: {datetime.utcnow().isoformat()}",
            "---",
            "",
            "# 📋 Cola Global de Ingesta del Sistema",
            "",
            "> **OPTIMIZACIÓN:** Los conceptos completados se archivan automáticamente en `data/queue/ingest_history.log` para mantener un tamaño de archivo mínimo en la cola activa.",
            "",
            f"- **Conceptos pendientes en cola activa:** {len(pending)}",
            f"- **En procesamiento:** {len(processing)}",
            f"- **Fallidos / Reintentos:** {len(failed)}",
            f"- **Total de conceptos archivados históricamente (`ingest_history.log`):** {historical_total}",
            "",
            "---",
            "",
            "## ⏳ Elementos en Cola Activa de Ingesta",
            "",
            "| # | ID | Concepto | Categoría | Fuente | Prioridad | Estado |",
            "|---|---|---|---|---|---|---|"
        ]

        if not items:
            lines.append("|_No hay elementos en la cola activa. Todos los conceptos procesados residen en el registro de log._|||||||")
        else:
            for idx, it in enumerate(items, start=1):
                clean_src = it.source if len(it.source) <= 45 else (it.source[:42] + "...")
                lines.append(f"| {idx} | `{it.item_id}` | [[{it.title}]] | **{it.category}** | [{clean_src}]({it.source}) | {it.priority} | `{it.status}` |")

        lines.extend([
            "",
            "---",
            "",
            "## 📜 Registro de Historial Externalizado",
            f"- **Archivo de Log:** [`ingest_history.log`](file:///c:/Users/ENEKO/Desktop/SAUCE/IA/data/queue/ingest_history.log)",
            f"- **Total de Registros en Log:** {historical_total}",
            "",
            f"_Cola sincronizada: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        ])

        wiki_page_path = Path(self.manager.config["wiki"]["local_path"]).resolve() / "Sistema" / "Cola_Global_Ingesta.md"
        wiki_page_path.parent.mkdir(parents=True, exist_ok=True)
        wiki_page_path.write_text("\n".join(lines), encoding="utf-8")

    def add_item(
        self,
        title: str,
        source: str,
        source_type: str = "url",
        category: str = "General",
        priority: int = 10
    ) -> IngestionQueueItem:
        """Añade una tarea a la cola global si no existe ya activa."""
        items = self._load_queue()
        for it in items:
            if it.title.strip().lower() == title.strip().lower() and it.status in ["pending", "processing"]:
                return it

        item_id = f"item_{int(time.time() * 1000)}_{len(items) + 1}"
        new_item = IngestionQueueItem(
            item_id=item_id,
            title=title,
            source=source,
            source_type=source_type,
            category=category,
            priority=priority,
            status="pending"
        )
        items.append(new_item)
        self._save_queue(items)
        return new_item

    def get_status(self) -> Dict[str, Any]:
        """Estado de la cola global y del log histórico."""
        items = self._load_queue()
        pending = sum(1 for i in items if i.status == "pending")
        failed = sum(1 for i in items if i.status == "failed")
        historical = self._count_history_items()
        return {
            "active_in_queue": len(items),
            "pending": pending,
            "failed": failed,
            "historical_log_total": historical,
            "queue_file": str(self.queue_file),
            "history_file": str(self.history_file)
        }

    def list_items(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._load_queue()
        if status_filter:
            items = [i for i in items if i.status == status_filter]
        return [i.to_dict() for i in items]

    def clear(self, keep_failed: bool = False):
        if keep_failed:
            items = [i for i in self._load_queue() if i.status == "failed"]
            self._save_queue(items)
        else:
            self._save_queue([])

    def process_next(self, auto_link: bool = True, fact_check: bool = False) -> Dict[str, Any]:
        """Procesa estrictamente el SIGUIENTE elemento de la cola global (uno solo)."""
        return self.process_queue(count=1, delay_seconds=0.0, auto_link=auto_link, fact_check=fact_check)

    def process_queue(
        self,
        count: Optional[int] = None,
        until_empty: bool = False,
        delay_seconds: float = 1.0,
        auto_link: bool = True,
        fact_check: bool = False
    ) -> Dict[str, Any]:
        """Procesa elementos de la cola global, archivando los completados inmediatamente en ingest_history.log."""
        items = self._load_queue()
        pending_indices = [i for i, item in enumerate(items) if item.status == "pending"]

        if not pending_indices:
            return {"processed": 0, "remaining": 0, "message": "No hay elementos pendientes en la cola global."}

        limit = len(pending_indices) if (until_empty or count is None) else min(count, len(pending_indices))
        processed_items = []
        errors = []

        for step in range(limit):
            # Recargar índices pendientes frescos
            items = self._load_queue()
            pending_items = [item for item in items if item.status == "pending"]
            if not pending_items:
                break

            item = pending_items[0]
            item.status = "processing"
            self._save_queue(items)

            # Fact-check opcional previo a la ingesta
            fc_report = None
            if fact_check:
                fc_report = self.fact_checker.verify_concept(title=item.title, summary_hint=item.source)

            try:
                if item.source_type == "url":
                    res = self.collector.fetch_url(
                        url=item.source,
                        custom_title=item.title,
                        category=item.category,
                        auto_link=auto_link
                    )
                elif item.source_type == "file":
                    res = self.ingestor.ingest_file(
                        file_path=item.source,
                        category=item.category,
                        auto_link=auto_link
                    )
                else:
                    res = self.ingestor.ingest_text(
                        title=item.title,
                        text=item.source,
                        category=item.category,
                        auto_link=auto_link
                    )

                if res.get("status") == "success":
                    item.status = "completed"
                    item.processed_at = datetime.utcnow().isoformat()
                    item.error_message = None

                    # Registro en historial log externo
                    details = f"Fact-Check: {fc_report.get('status_message')}" if fc_report else None
                    self._append_history_log(item, details=details)

                    entry = {"item_id": item.item_id, "title": item.title, "category": item.category}
                    if fc_report:
                        entry["fact_check"] = fc_report
                        if fc_report.get("verified"):
                            self.manager.append_note(
                                title=item.title,
                                note=f"Verificación externa: {fc_report.get('status_message')} (Fuentes: {', '.join(fc_report.get('external_sources', []))})",
                                section="Verificación y Fuentes Externas"
                            )
                    processed_items.append(entry)

                    # Eliminar de la cola activa para mantener el JSON ultraligero
                    items = [it for it in items if it.item_id != item.item_id]
                else:
                    item.status = "failed"
                    item.error_message = res.get("message", "Fallo en la ingesta")
                    errors.append({"item_id": item.item_id, "title": item.title, "error": item.error_message})

            except Exception as e:
                item.status = "failed"
                item.error_message = str(e)
                errors.append({"item_id": item.item_id, "title": item.title, "error": str(e)})

            self._save_queue(items)

            if step < limit - 1 and delay_seconds > 0:
                time.sleep(delay_seconds)

        remaining_count = sum(1 for i in self._load_queue() if i.status == "pending")

        return {
            "processed": len(processed_items),
            "processed_items": processed_items,
            "remaining": remaining_count,
            "errors": errors,
            "completed_all": remaining_count == 0
        }


IngestionQueueManager = GlobalIngestionQueueManager