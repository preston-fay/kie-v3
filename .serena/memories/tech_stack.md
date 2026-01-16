# KIE v3 Tech Stack

## Core Language & Version
- **Python**: 3.11+ (required)
- **Node.js**: 20+ (for web dashboard only)

## Python Dependencies

### Data Processing
- pandas (2.1.0+)
- polars (0.19.0+)
- numpy (1.24.0+)
- openpyxl, xlsxwriter (Excel I/O)

### Document Generation
- python-pptx (PowerPoint)
- python-docx (Word)
- reportlab (PDF)
- cairosvg (SVG→PNG conversion)
- pygal (SVG chart generation, replaces Node.js Recharts SSR)

### API (FastAPI)
- fastapi (0.104.0+)
- uvicorn (0.24.0+)
- pydantic (2.5.0+)

### Configuration
- pyyaml (6.0+)

### CLI/UI
- rich (13.0.0+, terminal formatting)
- click (8.1.0+)

### Optional Extras
- **geo**: geopandas, shapely, folium (for /map command)
- **dev**: pytest, mypy, ruff, black

## Frontend (web/)
- React 18+
- TypeScript
- Recharts (chart rendering library, KDS-enforced)
- Tailwind CSS (styling)
- Vite (build tool)

## Architecture Pattern
- **Backend**: Python (kie/) - generates JSON chart configs
- **Frontend**: React (web/) - renders charts from JSON
- **Validation**: Multi-level QC pipeline blocks non-compliant outputs
