"""Notion block models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    """Notion block types."""
    
    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    TO_DO = "to_do"
    TOGGLE = "toggle"
    CODE = "code"
    QUOTE = "quote"
    CALLOUT = "callout"
    DIVIDER = "divider"
    IMAGE = "image"
    FILE = "file"
    VIDEO = "video"
    PDF = "pdf"
    BOOKMARK = "bookmark"
    EMBED = "embed"
    LINK_TO_PAGE = "link_to_page"
    TABLE = "table"
    TABLE_ROW = "table_row"
    COLUMN_LIST = "column_list"
    COLUMN = "column"
    CHILD_PAGE = "child_page"
    CHILD_DATABASE = "child_database"
    UNSUPPORTED = "unsupported"


class RichText(BaseModel):
    """Rich text content."""
    
    type: str = "text"
    plain_text: str
    href: Optional[str] = None
    annotations: Dict[str, Any] = Field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        text = self.plain_text
        
        # Apply formatting
        if self.annotations.get("bold"):
            text = f"**{text}**"
        if self.annotations.get("italic"):
            text = f"*{text}*"
        if self.annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if self.annotations.get("code"):
            text = f"`{text}`"
        
        # Add link
        if self.href:
            text = f"[{text}]({self.href})"
        
        return text


class FileInfo(BaseModel):
    """File or image information."""
    
    type: str  # "file", "external"
    url: str
    name: Optional[str] = None
    expiry_time: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NotionBlock(BaseModel):
    """Base Notion block model."""
    
    id: str
    type: BlockType
    created_time: datetime
    last_edited_time: datetime
    has_children: bool = False
    archived: bool = False
    
    # Content fields (depend on block type)
    rich_text: List[RichText] = Field(default_factory=list)
    checked: Optional[bool] = None  # For to_do blocks
    language: Optional[str] = None  # For code blocks
    file: Optional[FileInfo] = None  # For image/file blocks
    caption: List[RichText] = Field(default_factory=list)
    url: Optional[str] = None  # For bookmarks, embeds
    
    # Child blocks (for nested content)
    children: List["NotionBlock"] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def get_plain_text(self) -> str:
        """Get plain text content."""
        return "".join([rt.plain_text for rt in self.rich_text])
    
    def get_markdown_text(self) -> str:
        """Get markdown formatted text."""
        return "".join([rt.to_markdown() for rt in self.rich_text])
    
    def to_markdown(self, indent: int = 0) -> str:
        """Convert block to markdown format."""
        indent_str = "  " * indent
        text = self.get_markdown_text()
        
        result = ""
        
        if self.type == BlockType.HEADING_1:
            result = f"# {text}\n"
        elif self.type == BlockType.HEADING_2:
            result = f"## {text}\n"
        elif self.type == BlockType.HEADING_3:
            result = f"### {text}\n"
        elif self.type == BlockType.PARAGRAPH:
            result = f"{text}\n"
        elif self.type == BlockType.BULLETED_LIST_ITEM:
            result = f"{indent_str}- {text}\n"
        elif self.type == BlockType.NUMBERED_LIST_ITEM:
            result = f"{indent_str}1. {text}\n"
        elif self.type == BlockType.TO_DO:
            checkbox = "[x]" if self.checked else "[ ]"
            result = f"{indent_str}- {checkbox} {text}\n"
        elif self.type == BlockType.CODE:
            lang = self.language or ""
            result = f"```{lang}\n{text}\n```\n"
        elif self.type == BlockType.QUOTE:
            result = f"> {text}\n"
        elif self.type == BlockType.DIVIDER:
            result = "---\n"
        elif self.type == BlockType.IMAGE:
            if self.file:
                caption_text = self.get_caption_text()
                result = f"![{caption_text}]({self.file.url})\n"
        elif self.type == BlockType.FILE:
            if self.file:
                name = self.file.name or "file"
                result = f"[{name}]({self.file.url})\n"
        elif self.type == BlockType.BOOKMARK:
            if self.url:
                result = f"[Bookmark]({self.url})\n"
        else:
            result = f"{text}\n" if text else ""
        
        # Add children
        if self.children:
            for child in self.children:
                result += child.to_markdown(indent + 1)
        
        return result
    
    def get_caption_text(self) -> str:
        """Get caption as plain text."""
        return "".join([rt.plain_text for rt in self.caption])


class NotionProperty(BaseModel):
    """Notion page property."""
    
    id: str
    type: str
    name: Optional[str] = None
    
    # Values depend on type
    title: Optional[List[RichText]] = None
    rich_text: Optional[List[RichText]] = None
    number: Optional[float] = None
    select: Optional[Dict[str, str]] = None
    multi_select: Optional[List[Dict[str, str]]] = None
    date: Optional[Dict[str, Any]] = None
    people: Optional[List[Dict[str, Any]]] = None
    files: Optional[List[FileInfo]] = None
    checkbox: Optional[bool] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    formula: Optional[Dict[str, Any]] = None
    relation: Optional[List[Dict[str, str]]] = None
    rollup: Optional[Dict[str, Any]] = None
    created_time: Optional[datetime] = None
    created_by: Optional[Dict[str, Any]] = None
    last_edited_time: Optional[datetime] = None
    last_edited_by: Optional[Dict[str, Any]] = None
    status: Optional[Dict[str, str]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def get_value(self) -> Any:
        """Get the actual value of the property."""
        if self.title:
            return "".join([rt.plain_text for rt in self.title])
        elif self.rich_text:
            return "".join([rt.plain_text for rt in self.rich_text])
        elif self.number is not None:
            return self.number
        elif self.select:
            return self.select.get("name")
        elif self.multi_select:
            return [s.get("name") for s in self.multi_select]
        elif self.date:
            return self.date.get("start")
        elif self.people:
            return [p.get("name") for p in self.people]
        elif self.checkbox is not None:
            return self.checkbox
        elif self.url:
            return self.url
        elif self.email:
            return self.email
        elif self.phone_number:
            return self.phone_number
        elif self.status:
            return self.status.get("name")
        else:
            return None


class NotionPage(BaseModel):
    """Complete Notion page model."""
    
    id: str
    created_time: datetime
    last_edited_time: datetime
    archived: bool = False
    url: str
    
    # Icon and cover
    icon: Optional[Dict[str, Any]] = None
    cover: Optional[Dict[str, Any]] = None
    
    # Properties (metadata)
    properties: Dict[str, NotionProperty] = Field(default_factory=dict)
    
    # Content (blocks)
    blocks: List[NotionBlock] = Field(default_factory=list)
    
    # Parent info
    parent: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def get_title(self) -> str:
        """Get page title."""
        # Try common title property names
        for prop_name in ["Task name", "Name", "Title", "title"]:
            if prop_name in self.properties:
                value = self.properties[prop_name].get_value()
                if value:
                    return str(value)
        return "Untitled"
    
    def get_property_value(self, name: str) -> Any:
        """Get property value by name."""
        if name in self.properties:
            return self.properties[name].get_value()
        return None
    
    def get_content_markdown(self) -> str:
        """Get all page content as markdown."""
        return "".join([block.to_markdown() for block in self.blocks])
    
    def get_todo_items(self) -> List[NotionBlock]:
        """Get all to-do items from the page."""
        todos = []
        
        def collect_todos(blocks: List[NotionBlock]):
            for block in blocks:
                if block.type == BlockType.TO_DO:
                    todos.append(block)
                if block.children:
                    collect_todos(block.children)
        
        collect_todos(self.blocks)
        return todos
    
    def get_images(self) -> List[NotionBlock]:
        """Get all images from the page."""
        images = []
        
        def collect_images(blocks: List[NotionBlock]):
            for block in blocks:
                if block.type == BlockType.IMAGE and block.file:
                    images.append(block)
                if block.children:
                    collect_images(block.children)
        
        collect_images(self.blocks)
        return images
    
    def get_files(self) -> List[NotionBlock]:
        """Get all files from the page."""
        files = []
        
        def collect_files(blocks: List[NotionBlock]):
            for block in blocks:
                if block.type == BlockType.FILE and block.file:
                    files.append(block)
                if block.children:
                    collect_files(block.children)
        
        collect_files(self.blocks)
        return files
    
    def get_links(self) -> List[str]:
        """Get all links from the page."""
        links = []
        
        def collect_links(blocks: List[NotionBlock]):
            for block in blocks:
                # Links in rich text
                for rt in block.rich_text:
                    if rt.href:
                        links.append(rt.href)
                
                # Bookmark blocks
                if block.type == BlockType.BOOKMARK and block.url:
                    links.append(block.url)
                
                # Check children
                if block.children:
                    collect_links(block.children)
        
        collect_links(self.blocks)
        return links


# Allow forward references
NotionBlock.model_rebuild()







