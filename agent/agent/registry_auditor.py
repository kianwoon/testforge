import ast
import inspect
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .models import RegistryEntry

class RegistryAuditor:
    def __init__(self, page_objects_path: str = "/testforge/page_objects"):
        self.page_objects_path = Path(page_objects_path)

    async def audit(self) -> Dict[str, RegistryEntry]:
        registry = {}

        if not self.page_objects_path.exists():
            return registry

        for py_file in self.page_objects_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            classes = await self._extract_classes_from_file(py_file)
            for class_name, methods in classes.items():
                registry[class_name] = RegistryEntry(
                    class_name=class_name,
                    file_path=py_file.name,
                    methods=list(methods),
                    selectors={},
                    last_modified=datetime.fromtimestamp(py_file.stat().st_mtime)
                )

        return registry

    async def _extract_classes_from_file(self, file_path: Path) -> Dict[str, set]:
        source = file_path.read_text()
        tree = ast.parse(source)

        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = set()
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef):
                        methods.add(item.name)
                    elif isinstance(item, ast.FunctionDef):
                        methods.add(item.name)
                classes[node.name] = methods

        return classes

    async def find_existing_class(self, page_name: str) -> Optional[RegistryEntry]:
        registry = await self.audit()
        class_name = f"{page_name.replace('_', ' ').title().replace(' ', '')}Page"
        return registry.get(class_name)

    async def find_available_methods(self, class_name: str) -> List[str]:
        registry = await self.audit()
        entry = registry.get(class_name)
        return entry.methods if entry else []
