"""
PDF Extractor Module
Extracts text and structure from PDF documents using pdfplumber.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Section:
    """Represents a document section with heading and content."""
    heading: str
    content: str
    hierarchy: int


class PDFExtractor:
    """
    Extracts text and structured content from PDF documents.
    Uses pdfplumber for text and table extraction.
    """

    # Common heading patterns
    HEADING_PATTERNS = [
        # All caps headings
        (r'^([A-Z][A-Z\s&\-]+)$', 1),
        # Numbered headings (1. Section, 1.1 Subsection)
        (r'^(\d+\.?\d*\.?\s+[A-Z][A-Za-z\s]+)', 2),
        # Bold-style markers (often appear differently in PDFs)
        (r'^((?:Chapter|Section|Part)\s+\d+[:\.]?\s*.+)$', 1),
        # Title case lines that are short (likely headings)
        (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,5})\s*$', 2),
    ]

    def __init__(self):
        self.pdfplumber = None
        self._import_pdfplumber()

    def _import_pdfplumber(self):
        """Lazy import of pdfplumber."""
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber is required for PDF extraction. "
                "Install it with: pip install pdfplumber"
            )

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and structure from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing extracted text and structured sections
        """
        try:
            with self.pdfplumber.open(file_path) as pdf:
                all_text = []
                all_tables = []
                page_count = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text() or ""
                    all_text.append(page_text)

                    # Extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            all_tables.append({
                                'page': page_num + 1,
                                'data': table
                            })

                full_text = "\n\n".join(all_text)

                # Parse sections from text
                sections = self._parse_sections(full_text)

                # Convert tables to text representation
                table_text = self._tables_to_text(all_tables)
                if table_text:
                    full_text += "\n\n--- TABLES ---\n" + table_text

                return {
                    'extractedText': full_text,
                    'structuredSections': [asdict(s) for s in sections],
                    'metadata': {
                        'pageCount': page_count,
                        'wordCount': len(full_text.split()),
                        'tableCount': len(all_tables)
                    }
                }

        except Exception as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise ValueError(f"PDF is password-protected: {file_path}")
            raise ValueError(f"Failed to extract PDF: {str(e)}")

    def _parse_sections(self, text: str) -> List[Section]:
        """
        Parse text into structured sections based on heading detection.

        Args:
            text: Full extracted text

        Returns:
            List of Section objects
        """
        lines = text.split('\n')
        sections = []
        current_heading = "Document Content"
        current_content = []
        current_hierarchy = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line is a heading
            heading_match = self._detect_heading(line)
            if heading_match:
                # Save previous section if it has content
                if current_content:
                    sections.append(Section(
                        heading=current_heading,
                        content="\n".join(current_content).strip(),
                        hierarchy=current_hierarchy
                    ))

                current_heading = heading_match[0]
                current_hierarchy = heading_match[1]
                current_content = []
            else:
                current_content.append(line)

        # Don't forget the last section
        if current_content:
            sections.append(Section(
                heading=current_heading,
                content="\n".join(current_content).strip(),
                hierarchy=current_hierarchy
            ))

        return sections

    def _detect_heading(self, line: str) -> Optional[tuple]:
        """
        Detect if a line is a heading.

        Args:
            line: Text line to check

        Returns:
            Tuple of (heading_text, hierarchy_level) or None
        """
        # Skip very long lines (unlikely to be headings)
        if len(line) > 100:
            return None

        # Skip lines that look like sentences
        if line.endswith('.') and len(line) > 50:
            return None

        for pattern, hierarchy in self.HEADING_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                heading_text = match.group(1).strip()
                # Validate it looks like a real heading
                if len(heading_text) >= 3 and len(heading_text) <= 80:
                    return (heading_text, hierarchy)

        return None

    def _tables_to_text(self, tables: List[Dict]) -> str:
        """
        Convert extracted tables to text representation.

        Args:
            tables: List of table dictionaries with page and data

        Returns:
            Text representation of tables
        """
        if not tables:
            return ""

        text_parts = []
        for i, table in enumerate(tables):
            text_parts.append(f"Table {i + 1} (Page {table['page']}):")
            for row in table['data']:
                if row:
                    # Filter out None values and convert to strings
                    row_text = " | ".join(str(cell) if cell else "" for cell in row)
                    text_parts.append(row_text)
            text_parts.append("")

        return "\n".join(text_parts)

    def can_handle(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.lower().endswith('.pdf')
