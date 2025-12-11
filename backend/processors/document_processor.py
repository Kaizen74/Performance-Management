"""
Unified Document Processor
Handles multi-format document ingestion and text extraction.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .pptx_extractor import PPTXExtractor
from .xlsx_extractor import XLSXExtractor


@dataclass
class ProcessedDocument:
    """Standardized output structure for processed documents."""
    documentId: str
    fileName: str
    documentType: str  # 'strategy' or 'goals'
    extractedText: str
    structuredSections: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DocumentProcessor:
    """
    Unified document processor that handles multiple file formats.
    Provides standardized JSON output structure.
    """

    SUPPORTED_FORMATS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'docx',  # Will attempt conversion
        '.pptx': 'pptx',
        '.ppt': 'pptx',  # Will attempt conversion
        '.xlsx': 'xlsx',
        '.xls': 'xlsx'
    }

    def __init__(self):
        """Initialize the document processor with all extractors."""
        self._extractors = {}
        self._init_extractors()

    def _init_extractors(self):
        """Initialize all available extractors."""
        try:
            self._extractors['pdf'] = PDFExtractor()
        except ImportError as e:
            print(f"PDF extractor not available: {e}")

        try:
            self._extractors['docx'] = DOCXExtractor()
        except ImportError as e:
            print(f"DOCX extractor not available: {e}")

        try:
            self._extractors['pptx'] = PPTXExtractor()
        except ImportError as e:
            print(f"PPTX extractor not available: {e}")

        try:
            self._extractors['xlsx'] = XLSXExtractor()
        except ImportError as e:
            print(f"XLSX extractor not available: {e}")

    def extract(self, file_path: str, document_type: str = 'strategy') -> Dict[str, Any]:
        """
        Extract content from a document file.

        Args:
            file_path: Path to the document file
            document_type: Type of document ('strategy' or 'goals')

        Returns:
            Standardized document structure as dictionary
        """
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension and determine extractor
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {list(self.SUPPORTED_FORMATS.keys())}"
            )

        extractor_type = self.SUPPORTED_FORMATS[ext]
        extractor = self._extractors.get(extractor_type)

        if not extractor:
            raise RuntimeError(
                f"Extractor for {extractor_type} is not available. "
                "Please install required dependencies."
            )

        # Extract content
        extraction_result = extractor.extract(file_path)

        # Build standardized output
        processed = ProcessedDocument(
            documentId=str(uuid.uuid4()),
            fileName=os.path.basename(file_path),
            documentType=document_type,
            extractedText=extraction_result['extractedText'],
            structuredSections=extraction_result['structuredSections'],
            metadata={
                **extraction_result['metadata'],
                'extractionTimestamp': datetime.utcnow().isoformat() + 'Z',
                'fileSize': os.path.getsize(file_path),
                'fileFormat': ext[1:]  # Remove leading dot
            }
        )

        return asdict(processed)

    def extract_batch(
        self,
        file_paths: List[str],
        document_type: str = 'strategy'
    ) -> List[Dict[str, Any]]:
        """
        Extract content from multiple document files.

        Args:
            file_paths: List of paths to document files
            document_type: Type of documents ('strategy' or 'goals')

        Returns:
            List of standardized document structures
        """
        results = []
        errors = []

        for file_path in file_paths:
            try:
                result = self.extract(file_path, document_type)
                results.append(result)
            except Exception as e:
                errors.append({
                    'file': file_path,
                    'error': str(e)
                })

        if errors:
            # Include error information in results
            for error in errors:
                results.append({
                    'documentId': str(uuid.uuid4()),
                    'fileName': os.path.basename(error['file']),
                    'documentType': document_type,
                    'extractedText': '',
                    'structuredSections': [],
                    'metadata': {
                        'error': error['error'],
                        'extractionTimestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                })

        return results

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.SUPPORTED_FORMATS.keys())

    def is_supported(self, file_path: str) -> bool:
        """Check if a file format is supported."""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_FORMATS

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a file before processing.

        Args:
            file_path: Path to the file

        Returns:
            Validation result dictionary
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check if file exists
        if not os.path.exists(file_path):
            result['valid'] = False
            result['errors'].append('File does not exist')
            return result

        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.SUPPORTED_FORMATS:
            result['valid'] = False
            result['errors'].append(f'Unsupported format: {ext}')
            return result

        # Check file size (max 25MB)
        file_size = os.path.getsize(file_path)
        max_size = 25 * 1024 * 1024  # 25MB

        if file_size > max_size:
            result['valid'] = False
            result['errors'].append(f'File too large: {file_size / 1024 / 1024:.1f}MB (max 25MB)')
        elif file_size > 10 * 1024 * 1024:
            result['warnings'].append('Large file may take longer to process')

        # Check if file is empty
        if file_size == 0:
            result['valid'] = False
            result['errors'].append('File is empty')

        # Check extractor availability
        extractor_type = self.SUPPORTED_FORMATS.get(ext.lower())
        if extractor_type and extractor_type not in self._extractors:
            result['valid'] = False
            result['errors'].append(f'Extractor for {extractor_type} not available')

        return result

    def get_extractor_status(self) -> Dict[str, bool]:
        """Get availability status of all extractors."""
        return {
            'pdf': 'pdf' in self._extractors,
            'docx': 'docx' in self._extractors,
            'pptx': 'pptx' in self._extractors,
            'xlsx': 'xlsx' in self._extractors
        }


def create_processor() -> DocumentProcessor:
    """Factory function to create a configured DocumentProcessor."""
    return DocumentProcessor()
