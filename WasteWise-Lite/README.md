# WasteWise AI - Lite (no database, no login)

Opens straight to the output pages: Dashboard, Products, Inventory, Sales History, Demand Forecast, Expiry Risk,
Recommendations, Waste Reports, Model Metrics. Data comes from the CSV files in `ml/data/raw/`
(simulated batch data) - nothing to install except Python and Node.

## Run (Windows)
Double-click `run.bat`, or in a terminal inside this folder:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
uvicorn app.main:app --port 8000
```
Open a SECOND terminal in this folder:
```
cd frontend
npm install
npm run dev
```
Then open http://localhost:5173   (API docs: http://localhost:8000/docs)

The first API start trains the two models (about 10-20 seconds). Approve/reject choices on the Recommendations page
are kept in memory and reset when the API restarts.

Needs Python 3.10+ and Node 18+.
