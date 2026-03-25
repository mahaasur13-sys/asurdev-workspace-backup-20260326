"""Document Loader для Obsidian Vault и астрологических файлов"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """Единица документа для RAG"""
    content: str
    metadata: Dict[str, Any]
    source: str


class ObsidianLoader:
    """Загрузчик документов из Obsidian Vault"""
    
    # Markdown файлы астрологии
    ASTRO_PATTERNS = [
        "nakshatr", "choghadiya", "muhurta", "dasha", "rasi",
        "yoga", "jyotish", "vedic", "western", "lilly"
    ]
    
    # Файлы исключения
    EXCLUDE_PATTERNS = [
        ".obsidian", ".git", "node_modules", ".trash",
        "Pasted image", "Obsidian Vault_old"
    ]
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
    
    def load_all(self) -> List[Document]:
        """Загрузить все документы из vault"""
        documents = []
        
        # Markdown файлы
        for md_file in self.vault_path.rglob("*.md"):
            if self._should_exclude(md_file):
                continue
            doc = self._load_markdown(md_file)
            if doc:
                documents.append(doc)
        
        # Астрологические Python файлы
        astro_path = Path("/home/workspace/asurdevSentinel/astrology")
        if astro_path.exists():
            for py_file in astro_path.rglob("*.py"):
                if py_file.name != "__init__.py":
                    doc = self._load_python_astro(py_file)
                    if doc:
                        documents.append(doc)
        
        return documents
    
    def _should_exclude(self, path: Path) -> bool:
        """Проверить нужно ли исключить файл"""
        path_str = str(path)
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.lower() in path_str.lower():
                return True
        return False
    
    def _load_markdown(self, path: Path) -> Optional[Document]:
        """Загрузить markdown файл"""
        try:
            content = path.read_text(encoding="utf-8")
            
            # Извлечь frontmatter если есть
            frontmatter = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm_text = parts[1]
                    content = parts[2].strip()
                    # Парсить frontmatter
                    for line in fm_text.split("\n"):
                        if ":" in line:
                            key, val = line.split(":", 1)
                            frontmatter[key.strip()] = val.strip()
            
            # Очистить текст
            content = self._clean_content(content)
            
            if len(content) < 100:  # Пропустить слишком короткие
                return None
            
            # Определить категорию
            category = self._categorize(path.name, content)
            
            return Document(
                content=content,
                metadata={
                    "source": str(path),
                    "filename": path.name,
                    "category": category,
                    "language": "ru" if self._is_russian(content) else "en",
                    **frontmatter
                },
                source=str(path)
            )
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
    
    def _load_python_astro(self, path: Path) -> Optional[Document]:
        """Загрузить астрологический Python файл"""
        try:
            content = path.read_text(encoding="utf-8")
            
            # Извлечь docstring
            docstring = ""
            in_docstring = False
            lines = content.split("\n")
            for i, line in enumerate(lines[:20]):  # Первые 20 строк
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring += line.split('"""')[1].split("'''")[1] + "\n"
                    else:
                        in_docstring = False
            
            # Комбинировать docstring с кодом
            full_content = docstring + "\n\n" + content[:3000]  # Ограничить размер
            
            return Document(
                content=full_content,
                metadata={
                    "source": str(path),
                    "filename": path.name,
                    "category": "astrology_code",
                    "language": "en"
                },
                source=str(path)
            )
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """Очистить контент от мусора"""
        # Удалить изображения
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        # Удалить ссылки
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        # Удалить HTML теги
        content = re.sub(r'<[^>]+>', '', content)
        # Удалить повторяющиеся пробелы
        content = re.sub(r'\s+', ' ', content)
        # Удалить спецсимволы в начале строк
        content = re.sub(r'^[\#\*\-]+', '', content, flags=re.MULTILINE)
        return content.strip()
    
    def _categorize(self, filename: str, content: str) -> str:
        """Определить категорию документа"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        for pattern in self.ASTRO_PATTERNS:
            if pattern in filename_lower or pattern in content_lower:
                if "nakshatr" in pattern or "choghadiya" in pattern or "muhurta" in pattern:
                    return "vedic_astrology"
                elif "dasha" in pattern:
                    return "dasha_system"
                elif "western" in pattern or "lilly" in pattern:
                    return "western_astrology"
                else:
                    return "general_astrology"
        
        if "астролог" in content_lower or "зодиак" in content_lower:
            return "astrology"
        elif "gann" in filename_lower or "andrews" in filename_lower:
            return "technical_analysis"
        
        return "general"
    
    def _is_russian(self, text: str) -> bool:
        """Проверить есть ли русский текст"""
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        total_chars = len(re.findall(r'[а-яА-ЯёЁa-zA-Z]', text))
        return total_chars > 0 and russian_chars / total_chars > 0.3
