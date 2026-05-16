# PDF-to-LaTeX Reconstruction Engine

An AI-powered system that converts any PDF document into production-quality LaTeX source code with near pixel-perfect visual fidelity.

## Features

- **Intelligent Document Parsing** — Extracts text, images, tables, equations with full formatting metadata
- **Exact Visual Reconstruction** — Preserves colors, fonts, layouts, margins, spacing, and styling
- **Table Reconstruction** — Detects and reproduces tables with borders, merged cells, and formatting
- **Equation Detection** — Identifies and converts mathematical equations to LaTeX math syntax
- **Image Extraction** — Extracts images at original quality with position preservation
- **Visual Fidelity Engine** — SSIM-based comparison between original and generated PDFs
- **Modern Web UI** — React + Tailwind with dark/light mode, glassmorphism design
- **Export Options** — Download .tex source, compiled PDF, or complete ZIP package
- **Real-time Progress** — WebSocket-based live conversion progress tracking

## Architecture

```
Frontend (React + Vite + Tailwind)
     ↓ REST API / WebSocket
Backend (Python + FastAPI)
     ├── PDF Parser (PyMuPDF)
     ├── Text Extractor (formatting-aware)
     ├── Image Extractor (original quality)
     ├── Table Detector (structure-aware)
     ├── Equation Detector (math recognition)
     ├── Layout Analyzer (margins, columns)
     ├── LaTeX Generator (clean, modular output)
     ├── LaTeX Compiler (xelatex/pdflatex)
     └── Fidelity Engine (SSIM comparison)
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- LaTeX distribution (TeX Live or MiKTeX) — optional for compilation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Docker Setup

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:5173 (dev) or http://localhost:3000 (Docker)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload a PDF file |
| POST | `/api/convert/{job_id}` | Start conversion |
| GET | `/api/status/{job_id}` | Get conversion status |
| GET | `/api/result/{job_id}` | Get conversion result |
| WS | `/api/ws/{job_id}` | WebSocket progress updates |
| GET | `/api/export/tex/{job_id}` | Download .tex file |
| GET | `/api/export/pdf/{job_id}` | Download compiled PDF |
| GET | `/api/export/zip/{job_id}` | Download ZIP package |

## Supported Document Types

- Research papers (IEEE, ACM, etc.)
- Books and journals
- Thesis documents
- Reports and resumes
- Scientific articles
- Financial documents
- Multi-language PDFs

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI |
| PDF Processing | PyMuPDF (fitz), pdfplumber |
| Image Processing | Pillow, OpenCV |
| Visual Comparison | SSIM (scikit-image) |
| Containerization | Docker, docker-compose |

## License

MIT
