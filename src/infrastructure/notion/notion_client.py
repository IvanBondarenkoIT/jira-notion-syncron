"""Notion API client for fetching pages and blocks."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from src.domain.models.notion_block import (
    BlockType,
    FileInfo,
    NotionBlock,
    NotionPage,
    NotionProperty,
    RichText,
)


class NotionClientError(Exception):
    """Base Notion client error."""
    pass


class NotionRateLimitError(NotionClientError):
    """Rate limit exceeded."""
    pass


class NotionClient:
    """Client for Notion API."""
    
    def __init__(self, token: str, version: str = "2022-06-28"):
        """Initialize Notion client.
        
        Args:
            token: Notion integration token
            version: Notion API version
        """
        self.token = token
        self.version = version
        self.base_url = "https://api.notion.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Notion-Version": version,
            "Content-Type": "application/json"
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
            
        Raises:
            NotionClientError: On API error
            NotionRateLimitError: On rate limit
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", retry_delay))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue
                
                # Check for errors
                if response.status_code >= 400:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("message", response.text)
                    raise NotionClientError(
                        f"Notion API error {response.status_code}: {error_msg}"
                    )
                
                return response.json()
                
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise NotionClientError(f"Request failed: {e}")
                logger.warning(f"Request failed, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay * (attempt + 1))
        
        raise NotionClientError("Max retries exceeded")
    
    def query_database(
        self,
        database_id: str,
        filter_params: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Query database for pages.
        
        Args:
            database_id: Database ID
            filter_params: Filter parameters
            sorts: Sort parameters
            
        Returns:
            List of page objects
        """
        all_results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            body = {}
            if filter_params:
                body["filter"] = filter_params
            if sorts:
                body["sorts"] = sorts
            if start_cursor:
                body["start_cursor"] = start_cursor
            
            data = self._request(
                "POST",
                f"/databases/{database_id}/query",
                json=body
            )
            
            results = data.get("results", [])
            all_results.extend(results)
            
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
            
            logger.debug(f"Fetched {len(results)} pages, total: {len(all_results)}")
        
        logger.info(f"Fetched {len(all_results)} pages from database {database_id}")
        return all_results
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page object
        """
        return self._request("GET", f"/pages/{page_id}")
    
    def get_block_children(
        self,
        block_id: str,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """Get block children.
        
        Args:
            block_id: Block/Page ID
            recursive: Whether to fetch children recursively
            
        Returns:
            List of block objects
        """
        all_blocks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            params = {}
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            data = self._request(
                "GET",
                f"/blocks/{block_id}/children",
                params=params
            )
            
            blocks = data.get("results", [])
            
            # Recursively fetch children
            if recursive:
                for block in blocks:
                    if block.get("has_children"):
                        block["children"] = self.get_block_children(
                            block["id"],
                            recursive=True
                        )
            
            all_blocks.extend(blocks)
            
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return all_blocks
    
    def get_page_content(self, page_id: str) -> NotionPage:
        """Get complete page with content.
        
        Args:
            page_id: Page ID
            
        Returns:
            NotionPage model
        """
        # Get page metadata
        page_data = self.get_page(page_id)
        
        # Get page content (blocks)
        blocks_data = self.get_block_children(page_id, recursive=True)
        
        # Parse into model
        return self._parse_page(page_data, blocks_data)
    
    def get_database_pages(
        self,
        database_id: str,
        include_content: bool = True
    ) -> List[NotionPage]:
        """Get all pages from database with content.
        
        Args:
            database_id: Database ID
            include_content: Whether to fetch page content (blocks)
            
        Returns:
            List of NotionPage models
        """
        # Query database for pages
        pages_data = self.query_database(database_id)
        
        pages = []
        for page_data in pages_data:
            try:
                if include_content:
                    # Get full page with blocks
                    page = self.get_page_content(page_data["id"])
                else:
                    # Just parse metadata
                    page = self._parse_page(page_data, [])
                
                pages.append(page)
                logger.debug(f"Parsed page: {page.get_title()}")
                
            except Exception as e:
                logger.error(f"Error parsing page {page_data.get('id')}: {e}")
                continue
        
        logger.info(f"Parsed {len(pages)} pages from database")
        return pages
    
    def _parse_page(
        self,
        page_data: Dict[str, Any],
        blocks_data: List[Dict[str, Any]]
    ) -> NotionPage:
        """Parse page data into NotionPage model.
        
        Args:
            page_data: Raw page data from API
            blocks_data: Raw blocks data from API
            
        Returns:
            NotionPage model
        """
        # Parse properties
        properties = {}
        for prop_name, prop_data in page_data.get("properties", {}).items():
            properties[prop_name] = self._parse_property(prop_name, prop_data)
        
        # Parse blocks
        blocks = [self._parse_block(block_data) for block_data in blocks_data]
        
        return NotionPage(
            id=page_data["id"],
            created_time=datetime.fromisoformat(
                page_data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                page_data["last_edited_time"].replace("Z", "+00:00")
            ),
            archived=page_data.get("archived", False),
            url=page_data.get("url", ""),
            icon=page_data.get("icon"),
            cover=page_data.get("cover"),
            properties=properties,
            blocks=blocks,
            parent=page_data.get("parent")
        )
    
    def _parse_property(
        self,
        name: str,
        prop_data: Dict[str, Any]
    ) -> NotionProperty:
        """Parse property data.
        
        Args:
            name: Property name
            prop_data: Raw property data
            
        Returns:
            NotionProperty model
        """
        prop_type = prop_data.get("type", "")
        
        # Extract type-specific data
        type_data = prop_data.get(prop_type, {})
        
        # Parse rich text fields
        title = None
        rich_text = None
        
        if prop_type == "title" and type_data:
            title = [self._parse_rich_text(rt) for rt in type_data]
        elif prop_type == "rich_text" and type_data:
            rich_text = [self._parse_rich_text(rt) for rt in type_data]
        
        # Parse date
        date_value = None
        if prop_type == "date" and type_data:
            date_value = type_data
        
        # Parse people
        people = None
        if prop_type == "people" and type_data:
            people = type_data
        
        # Parse times
        created_time = None
        last_edited_time = None
        
        if prop_type == "created_time" and prop_data.get("created_time"):
            created_time = datetime.fromisoformat(
                prop_data["created_time"].replace("Z", "+00:00")
            )
        
        if prop_type == "last_edited_time" and prop_data.get("last_edited_time"):
            last_edited_time = datetime.fromisoformat(
                prop_data["last_edited_time"].replace("Z", "+00:00")
            )
        
        return NotionProperty(
            id=prop_data.get("id", ""),
            type=prop_type,
            name=name,
            title=title,
            rich_text=rich_text,
            number=type_data if prop_type == "number" else None,
            select=type_data if prop_type == "select" else None,
            multi_select=type_data if prop_type == "multi_select" else None,
            date=date_value,
            people=people,
            checkbox=type_data if prop_type == "checkbox" else None,
            url=type_data if prop_type == "url" else None,
            email=type_data if prop_type == "email" else None,
            phone_number=type_data if prop_type == "phone_number" else None,
            status=type_data if prop_type == "status" else None,
            created_time=created_time,
            last_edited_time=last_edited_time
        )
    
    def _parse_block(self, block_data: Dict[str, Any]) -> NotionBlock:
        """Parse block data.
        
        Args:
            block_data: Raw block data
            
        Returns:
            NotionBlock model
        """
        block_type = block_data.get("type", "unsupported")
        
        try:
            block_type_enum = BlockType(block_type)
        except ValueError:
            block_type_enum = BlockType.UNSUPPORTED
        
        # Get type-specific data
        type_data = block_data.get(block_type, {})
        
        # Parse rich text
        rich_text = []
        if "rich_text" in type_data:
            rich_text = [
                self._parse_rich_text(rt) for rt in type_data["rich_text"]
            ]
        elif "text" in type_data:  # Some blocks use "text" instead
            rich_text = [
                self._parse_rich_text(rt) for rt in type_data["text"]
            ]
        
        # Parse type-specific fields
        checked = type_data.get("checked") if block_type == "to_do" else None
        language = type_data.get("language") if block_type == "code" else None
        
        # Parse file/image
        file_info = None
        if block_type in ["image", "file", "video", "pdf"]:
            file_data = type_data.get("file") or type_data.get("external")
            if file_data:
                file_info = FileInfo(
                    type=type_data.get("type", "file"),
                    url=file_data.get("url", ""),
                    name=file_data.get("name"),
                    expiry_time=None  # TODO: parse if needed
                )
        
        # Parse caption
        caption = []
        if "caption" in type_data:
            caption = [
                self._parse_rich_text(rt) for rt in type_data["caption"]
            ]
        
        # Parse URL (for bookmarks, embeds)
        url = type_data.get("url")
        
        # Parse children (recursive)
        children = []
        if "children" in block_data:
            children = [
                self._parse_block(child) for child in block_data["children"]
            ]
        
        return NotionBlock(
            id=block_data["id"],
            type=block_type_enum,
            created_time=datetime.fromisoformat(
                block_data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                block_data["last_edited_time"].replace("Z", "+00:00")
            ),
            has_children=block_data.get("has_children", False),
            archived=block_data.get("archived", False),
            rich_text=rich_text,
            checked=checked,
            language=language,
            file=file_info,
            caption=caption,
            url=url,
            children=children
        )
    
    def _parse_rich_text(self, rt_data: Dict[str, Any]) -> RichText:
        """Parse rich text data.
        
        Args:
            rt_data: Raw rich text data
            
        Returns:
            RichText model
        """
        return RichText(
            type=rt_data.get("type", "text"),
            plain_text=rt_data.get("plain_text", ""),
            href=rt_data.get("href"),
            annotations=rt_data.get("annotations", {})
        )
    
    def close(self):
        """Close the session."""
        self.session.close()







