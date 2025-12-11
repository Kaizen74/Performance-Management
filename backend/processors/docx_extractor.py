"""
DOCX Extractor Module
Extracts text and structure from Word documents using pandoc (with python-docx fallback).
"""

import subprocess
import tempfile
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Section:
    """Represents a document section with heading and content."""
    heading: str
    content: str
    hierarchy: int


class DOCXExtractor:
    """
    Extracts text and structured content from DOCX documents.
    Primary: pandoc (preserves structure, handles track changes)
    Fallback: python-docx for basic extraction
    """

    def __init__(self):
        self.has_pandoc = self._check_pandoc()
        self.docx_module = None
        if not self.has_pandoc:
            self._import_python_docx()

    def _check_pandoc(self) -> bool:
        """Check if pandoc is available on the system."""
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _import_python_docx(self):
        """Lazy import of python-docx."""
        try:
            import docx
            self.docx_module = docx
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX extraction. "
                "Install it with: pip install python-docx"
            )

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and structure from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Dictionary containing extracted text and structured sections
        """
        if self.has_pandoc:
            return self._extract_with_pandoc(file_path)
        else:
            return self._extract_with_python_docx(file_path)

    def _extract_with_pandoc(self, file_path: str) -> Dict[str, Any]:
        """
        Extract using pandoc (preserves structure and track changes).

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extraction result dictionary
        """
        try:
            # Use pandoc to convert DOCX to markdown (preserves structure)
            result = subprocess.run(
                ['pandoc', '--track-changes=all', file_path, '-t', 'markdown'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise ValueError(f"Pandoc error: {result.stderr}")

            markdown_text = result.stdout

            # Parse sections from markdown
            sections = self._parse_markdown_sections(markdown_text)

            # Convert markdown to plain text for full text
            plain_text = self._markdown_to_plain(markdown_text)

            # Estimate page count (roughly 500 words per page)
            word_count = len(plain_text.split())
            estimated_pages = max(1, word_count // 500)

            return {
                'extractedText': plain_text,
                'structuredSections': [asdict(s) for s in sections],
                'metadata': {
                    'pageCount': estimated_pages,
                    'wordCount': word_count,
                    'extractionMethod': 'pandoc'
                }
            }

        except subprocess.TimeoutExpired:
            raise ValueError(f"Pandoc timed out processing: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to extract DOCX with pandoc: {str(e)}")

    def _extract_with_python_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Fallback extraction using python-docx.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extraction result dictionary
        """
        if not self.docx_module:
            self._import_python_docx()

        try:
            doc = self.docx_module.Document(file_path)
            sections = []
            all_text = []
            current_heading = "Document Content"
            current_content = []
            current_hierarchy = 0

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # Check if it's a heading style
                if para.style.name.startswith('Heading'):
                    # Save previous section
                    if current_content:
                        sections.append(Section(
                            heading=current_heading,
                            content="\n".join(current_content),
                            hierarchy=current_hierarchy
                        ))

                    # Extract heading level from style name
                    try:
                        level = int(para.style.name.replace('Heading ', ''))
                    except ValueError:
                        level = 1

                    current_heading = text
                    current_hierarchy = level
                    current_content = []
                else:
                    current_content.append(text)

                all_text.append(text)

            # Save last section
            if current_content:
                sections.append(Section(
                    heading=current_heading,
                    content="\n".join(current_content),
                    hierarchy=current_hierarchy
                ))

            # Extract tables
            table_text = self._extract_tables(doc)
            full_text = "\n".join(all_text)
            if table_text:
                full_text += "\n\n--- TABLES ---\n" + table_text

            word_count = len(full_text.split())

            return {
                'extractedText': full_text,
                'structuredSections': [asdict(s) for s in sections],
                'metadata': {
                    'pageCount': max(1, word_count // 500),
                    'wordCount': word_count,
                    'extractionMethod': 'python-docx'
                }
            }

        except Exception as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                raise ValueError(f"DOCX is password-protected: {file_path}")
            raise ValueError(f"Failed to extract DOCX: {str(e)}")

    def _extract_tables(self, doc) -> str:
        """Extract tables from DOCX document."""
        if not doc.tables:
            return ""

        table_texts = []
        for i, table in enumerate(doc.tables):
            table_texts.append(f"Table {i + 1}:")
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                table_texts.append(row_text)
            table_texts.append("")

        return "\n".join(table_texts)

    def _parse_markdown_sections(self, markdown: str) -> List[Section]:
        """
        Parse markdown content into structured sections.

        Args:
            markdown: Markdown text from pandoc

        Returns:
            List of Section objects
        """
        sections = []
        lines = markdown.split('\n')
        current_heading = "Document Content"
        current_content = []
        current_hierarchy = 0

        for line in lines:
            # Check for markdown headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                # Save previous section
                if current_content:
                    content_text = "\n".join(current_content).strip()
                    # Clean up markdown artifacts
                    content_text = self._clean_markdown(content_text)
                    sections.append(Section(
                        heading=current_heading,
                        content=content_text,
                        hierarchy=current_hierarchy
                    ))

                current_hierarchy = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            content_text = "\n".join(current_content).strip()
            content_text = self._clean_markdown(content_text)
            sections.append(Section(
                heading=current_heading,
                content=content_text,
                hierarchy=current_hierarchy
            ))

        return sections

    def _markdown_to_plain(self, markdown: str) -> str:
        """Convert markdown to plain text."""
        text = markdown

        # Remove heading markers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bold/italic markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)

        # Remove link formatting
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        # Remove track changes markers if present
        text = re.sub(r'\{[+-].*?\}', '', text)

        return text.strip()

    def _clean_markdown(self, text: str) -> str:
        """Remove common markdown artifacts from text."""
        # Remove emphasis markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)

        # Remove link syntax
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        # Remove excess whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def can_handle(self, file_path: str) -> bool:
        """Check if this extractor can handle the given file."""
        return file_path.lower().endswith('.docx')
