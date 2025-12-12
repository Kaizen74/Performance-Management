# Document Processors Package
from .document_processor import DocumentProcessor
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .pptx_extractor import PPTXExtractor
from .xlsx_extractor import XLSXExtractor
from .goals_table_processor import GoalsTableProcessor

__all__ = [
    'DocumentProcessor',
    'PDFExtractor',
    'DOCXExtractor',
    'PPTXExtractor',
    'XLSXExtractor',
    'GoalsTableProcessor'
]
