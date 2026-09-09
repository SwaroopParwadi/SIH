# SecureDoc AI

**AI-Based Fake Identity & Document Screening System**

Smart India Hackathon 2026 Project

---

## Project Structure

```
SIH Solution/
├── SecureDoc-Dataset/   # Existing synthetic dataset (DO NOT modify)
├── frontend/            # React + Vite dashboard
├── backend/             # FastAPI + PyMongo backend
├── ml/                  # ML training/inference scripts
├── models/              # Trained model artifacts
├── demo/                # Demo assets
├── tests/               # Test suites
├── scripts/             # Utility scripts
├── database/            # DB initialization scripts
├── .env                 # Environment variables (MongoDB Atlas URI)
├── .env.example         # Example env template
├── .gitignore
└── README.md
```

## Tech Stack

- **Frontend:** React + Vite, Tailwind CSS, Lucide Icons, Recharts
- **Backend:** Python, FastAPI, Pydantic, PyMongo
- **Database:** MongoDB Atlas Free M0 cluster (cloud only, no local MongoDB)
- **Dataset:** 2,000 synthetic identity document images (SecureDoc-Dataset)

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB Atlas account (free M0 cluster)

### 1. Configure Environment

Copy `.env.example` to `.env` and fill in your MongoDB Atlas connection string:

```bash
cp .env.example .env
```

Edit `.env`:

```
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGODB_DATABASE=securedoc
```

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## Pages

1. **Dashboard** — Overview metrics, risk distribution chart, recent cases, system health
2. **New Screening** — Upload document for analysis
3. **Analysis Results** — Detailed screening results and visualizations
4. **Case History** — Paginated list of all screened cases
5. **Case Details** — Full case information and evidence
6. **Model Performance** — Training metrics and performance charts
7. **Audit** — Audit log of all system actions
8. **Settings** — System configuration

## Database

MongoDB Atlas stores:
- Cases
- OCR results
- MRZ results
- Barcode results
- Verification results
- Risk scores
- Evidence
- Audit logs

Images are **not** stored in MongoDB. They remain local/temporary.

## Dataset

The `SecureDoc-Dataset/` directory contains 2,000 synthetic identity document images:

- 1,000 authentic + 1,000 manipulated
- Train/Validation/Test splits (70/15/15)
- 8 manipulation types
- Annotation files: labels.csv, metadata.csv, regions.json

**DO NOT delete, rename, move, regenerate, or modify this dataset.**

## License

Smart India Hackathon 2026 — Government of India
