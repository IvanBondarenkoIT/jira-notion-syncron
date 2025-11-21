"""Service for storing Notion data locally."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger

from src.domain.models.notion_block import NotionPage


class NotionStorage:
    """Service for storing and loading Notion pages locally."""
    
    def __init__(self, storage_dir: Path = None):
        """Initialize storage service.
        
        Args:
            storage_dir: Directory for storing Notion data
        """
        if storage_dir is None:
            storage_dir = Path("data/notion_export")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.pages_dir = self.storage_dir / "pages"
        self.pages_dir.mkdir(exist_ok=True)
        
        self.markdown_dir = self.storage_dir / "markdown"
        self.markdown_dir.mkdir(exist_ok=True)
        
        self.index_file = self.storage_dir / "index.json"
    
    def save_page(self, page: NotionPage, save_markdown: bool = True) -> Path:
        """Save page to JSON file.
        
        Args:
            page: NotionPage to save
            save_markdown: Whether to also save markdown version
            
        Returns:
            Path to saved JSON file
        """
        # Create safe filename
        title = self._sanitize_filename(page.get_title())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{page.id[:8]}.json"
        
        json_path = self.pages_dir / filename
        
        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                page.model_dump(mode="json"),
                f,
                ensure_ascii=False,
                indent=2
            )
        
        logger.debug(f"Saved page JSON: {json_path}")
        
        # Save markdown version
        if save_markdown:
            md_filename = f"{title}_{page.id[:8]}.md"
            md_path = self.markdown_dir / md_filename
            
            markdown_content = self._generate_markdown(page)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            logger.debug(f"Saved page markdown: {md_path}")
        
        return json_path
    
    def save_pages(
        self,
        pages: List[NotionPage],
        save_markdown: bool = True
    ) -> List[Path]:
        """Save multiple pages.
        
        Args:
            pages: List of NotionPage objects
            save_markdown: Whether to also save markdown versions
            
        Returns:
            List of paths to saved files
        """
        saved_paths = []
        
        for page in pages:
            try:
                path = self.save_page(page, save_markdown)
                saved_paths.append(path)
            except Exception as e:
                logger.error(f"Error saving page {page.id}: {e}")
        
        logger.info(f"Saved {len(saved_paths)} pages to {self.storage_dir}")
        
        # Update index
        self._update_index(pages)
        
        return saved_paths
    
    def load_page(self, page_id: str) -> NotionPage:
        """Load page from storage.
        
        Args:
            page_id: Page ID
            
        Returns:
            NotionPage object
            
        Raises:
            FileNotFoundError: If page not found
        """
        # Find file by page ID
        for json_file in self.pages_dir.glob("*.json"):
            if page_id[:8] in json_file.stem:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return NotionPage(**data)
        
        raise FileNotFoundError(f"Page {page_id} not found in storage")
    
    def load_all_pages(self) -> List[NotionPage]:
        """Load all pages from storage.
        
        Returns:
            List of NotionPage objects
        """
        pages = []
        
        for json_file in self.pages_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pages.append(NotionPage(**data))
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Loaded {len(pages)} pages from {self.storage_dir}")
        return pages
    
    def _sanitize_filename(self, name: str, max_length: int = 50) -> str:
        """Create safe filename from text.
        
        Args:
            name: Original name
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        
        # Truncate if too long
        if len(name) > max_length:
            name = name[:max_length]
        
        # Remove leading/trailing spaces and dots
        name = name.strip(". ")
        
        # Ensure not empty
        if not name:
            name = "untitled"
        
        return name
    
    def _generate_markdown(self, page: NotionPage) -> str:
        """Generate complete markdown document for page.
        
        Args:
            page: NotionPage object
            
        Returns:
            Markdown content
        """
        lines = []
        
        # Title
        lines.append(f"# {page.get_title()}\n")
        
        # Metadata
        lines.append("---")
        lines.append(f"**Notion ID**: {page.id}")
        lines.append(f"**Created**: {page.created_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Last Edited**: {page.last_edited_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**URL**: {page.url}")
        lines.append("---\n")
        
        # Properties
        if page.properties:
            lines.append("## Properties\n")
            for prop_name, prop in page.properties.items():
                value = prop.get_value()
                if value is not None:
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value if v)
                    lines.append(f"- **{prop_name}**: {value}")
            lines.append("")
        
        # Content
        if page.blocks:
            lines.append("## Content\n")
            lines.append(page.get_content_markdown())
        
        # Attachments summary
        images = page.get_images()
        files = page.get_files()
        links = page.get_links()
        
        if images or files or links:
            lines.append("\n---\n")
            lines.append("## Attachments\n")
            
            if images:
                lines.append(f"**Images**: {len(images)}")
                for img in images:
                    if img.file:
                        lines.append(f"  - {img.file.url}")
            
            if files:
                lines.append(f"\n**Files**: {len(files)}")
                for file in files:
                    if file.file:
                        name = file.file.name or "file"
                        lines.append(f"  - [{name}]({file.file.url})")
            
            if links:
                lines.append(f"\n**Links**: {len(links)}")
                for link in set(links):  # Remove duplicates
                    lines.append(f"  - {link}")
        
        return "\n".join(lines)
    
    def _update_index(self, pages: List[NotionPage]):
        """Update index file with page metadata.
        
        Args:
            pages: List of pages to index
        """
        index_data = []
        
        for page in pages:
            index_data.append({
                "id": page.id,
                "title": page.get_title(),
                "created_time": page.created_time.isoformat(),
                "last_edited_time": page.last_edited_time.isoformat(),
                "url": page.url,
                "blocks_count": len(page.blocks),
                "has_todos": len(page.get_todo_items()) > 0,
                "has_images": len(page.get_images()) > 0,
                "has_files": len(page.get_files()) > 0
            })
        
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Updated index with {len(pages)} pages")
    
    def get_index(self) -> List[dict]:
        """Get index of stored pages.
        
        Returns:
            List of page metadata
        """
        if not self.index_file.exists():
            return []
        
        with open(self.index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def export_statistics(self) -> dict:
        """Get statistics about stored pages.
        
        Returns:
            Dictionary with statistics
        """
        pages = self.load_all_pages()
        
        stats = {
            "total_pages": len(pages),
            "total_blocks": sum(len(p.blocks) for p in pages),
            "pages_with_todos": sum(1 for p in pages if p.get_todo_items()),
            "pages_with_images": sum(1 for p in pages if p.get_images()),
            "pages_with_files": sum(1 for p in pages if p.get_files()),
            "total_todos": sum(len(p.get_todo_items()) for p in pages),
            "total_images": sum(len(p.get_images()) for p in pages),
            "total_files": sum(len(p.get_files()) for p in pages),
            "total_links": sum(len(p.get_links()) for p in pages)
        }
        
        return stats







