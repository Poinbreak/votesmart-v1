# VoteSmart TN — Setup Guide

Complete step-by-step instructions to get the VoteSmart TN platform running locally.

---

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Supabase account** (free tier works)
- **Google AI Studio** API key (for Gemini 1.5 Flash)

---

## Step 1: Supabase Project Creation

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to India (e.g., Mumbai or Singapore)
3. Note down these values from **Settings → API**:
   - `Project URL` → `SUPABASE_URL`
   - `anon / public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY`

---

## Step 2: Run Database Migrations

1. In the Supabase dashboard, go to **SQL Editor**
2. Open the file `supabase/migrations/001_init.sql`
3. Copy the entire contents and paste into the SQL Editor
4. Click **Run** to execute

This will:
- Create all 5 tables (constituencies, candidates, news_articles, ml_features, predictions)
- Create indexes for performance
- Seed all 234 Tamil Nadu constituencies with district mappings
- Set up Row-Level Security policies

### Verify the seed data:
```sql
SELECT COUNT(*) FROM constituencies;
-- Should return 234

SELECT district, COUNT(*) FROM constituencies GROUP BY district ORDER BY district;
```

---

## Step 3: Environment Configuration

The `.env` file should already be configured with your keys. Verify it:

```bash
# In the project root: votesmart-tn/
cat .env
```

It should contain:
```
GEMINI_API_KEY=your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
DJANGO_SECRET_KEY=auto-generated
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## Step 4: Backend Setup

```powershell
# Navigate to backend
cd votesmart-tn\backend

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (for ECI scraper)
playwright install chromium

# Run Django migrations (for auth/admin only)
python manage.py migrate

# Verify Django
python manage.py check
```

---

## Step 5: Trigger First Scrape (Manual)

Since there's no candidate data yet, run the ECI scraper first:

```powershell
# Make sure you're in the backend directory with venv activated
cd votesmart-tn\backend

# Run ECI scraper (this will take a while — scrapes affidavit.eci.gov.in)
python scrapers\eci_playwright.py

# After ECI scraper completes, run news spider
python scrapers\news_scrapy\spiders\news_spider.py

# Compute ML features for all candidates
python ml\feature_engineer.py
```

**Note:** The ECI portal may require multiple runs if the website is slow. 
The scraper has exponential backoff retry built in.

---

## Step 6: Train the XGBoost Model

After scraping some data:

```powershell
cd votesmart-tn\backend

# Train the model (requires at least 10 candidates with features)
python ml\train_xgboost.py
```

This will:
1. Pull data from Supabase (candidates + ml_features)
2. If no prior predictions exist, generate synthetic training targets
3. Train XGBRegressor with 5-fold cross-validation
4. Save model to `backend/ml/xgboost_model.json`
5. Write predictions back to Supabase

---

## Step 7: Run Dev Servers

### Backend (Django)
```powershell
cd votesmart-tn\backend
python manage.py runserver
# Runs at http://127.0.0.1:8000
```

### Frontend (React + Vite) — in a separate terminal
```powershell
cd votesmart-tn\frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

The Vite dev server proxies `/api/*` requests to Django at `http://127.0.0.1:8000`.

---

## Step 8: GitHub Actions Secrets

If you want automated daily scraping, configure these secrets in your 
GitHub repo (Settings → Secrets and variables → Actions):

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `GEMINI_API_KEY` | Your Google AI Studio API key |

### Workflows:
- **Scrape ECI Data** (`scrape_eci.yml`): Runs daily at 23:30 IST
- **Scrape News** (`scrape_news.yml`): Runs daily at 00:00 IST
- Both can be triggered manually via **Actions → Run workflow**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/constituencies/` | List all 234 constituencies grouped by district |
| `GET` | `/api/constituencies/?search=kolathur` | Search constituencies |
| `GET` | `/api/candidates/<constituency_id>/` | Get candidates for a constituency |
| `POST` | `/api/moral-match/` | Run moral alignment scoring |
| `GET` | `/api/reality-predict/<constituency_id>/` | Get win predictions |

### Moral Match Request Example:
```json
POST /api/moral-match/
{
  "constituency_id": 13,
  "moral_input": "Anti-corruption, clean governance, pro-infrastructure development"
}
```

---

## Troubleshooting

### "No candidates found"
Run the ECI scraper first to populate candidate data.

### "XGBoost model not found"
Run `python ml/train_xgboost.py` to train the model.

### "Insufficient training data"
You need at least 10 candidates with computed features. Run the scrapers and then `python ml/feature_engineer.py`.

### "CORS error in browser"
Make sure `CORS_ALLOWED_ORIGINS` in `.env` matches your frontend URL (default: `http://localhost:5173`).

### "Rate limited by Gemini"
The Gemini filter has built-in rate limiting (1s between calls). If you hit quotas, wait and retry.
