# SGAA Session Notes

## Architecture Decisions

### Backend
- **Document Processing**: Python with specialized libraries
  - PDF: pdfplumber (better table extraction than pypdf)
  - DOCX: pandoc (preserves structure, track changes support)
  - PPTX: markitdown (converts to markdown)
  - XLSX: pandas + openpyxl (sheet enumeration, table handling)
- **API Layer**: Node.js with Express (or Python FastAPI for simplicity)
- **AI Integration**: Anthropic Claude API via user-provided key

### Frontend
- React 18+ with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- React Context + localStorage for state management

## File Structure
```
/strategic-goal-analyzer
├── /frontend          # React TypeScript app
├── /backend           # Python processors + API
├── /tests             # Test suites and fixtures
├── PROGRESS.md        # Current development progress
├── SESSION_NOTES.md   # Architecture decisions
└── RESUME.md          # Quick resume context
```

## Dependencies

### Python Backend
- pdfplumber: PDF text and table extraction
- python-docx: DOCX reading (fallback)
- pandas: XLSX processing
- openpyxl: Excel file support
- markitdown: PPTX to markdown conversion
- fastapi: API framework
- uvicorn: ASGI server
- anthropic: Claude API client

### Frontend
- react, react-dom
- typescript
- tailwindcss
- recharts
- axios

## Known Issues / Technical Debt
- None yet

## API Design Notes
- All document processing returns standardized JSON structure
- documentId uses UUID v4
- Timestamps in ISO8601 format
