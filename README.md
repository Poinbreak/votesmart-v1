# VoteSmart TN — Tamil Nadu Election Intelligence Platform

> Data-driven insights for all 234 Tamil Nadu constituencies.
> Find candidates that match your values — and see who's likely to win.

## 🎯 Features

- **Moral Match Engine** — CrossEncoder-based semantic matching between voter priorities and candidate records
- **Reality Predictor** — XGBoost win probability with 11-feature model
- **Automated Data Pipeline** — Daily ECI affidavit scraping + Tamil news crawling
- **Gemini AI Filter** — Fact-checking and spam detection for news articles
- **Beautiful React UI** — Glassmorphism design with interactive charts

## 📁 Architecture

```
votesmart-tn/
├── backend/          # Django REST API + ML engines + Scrapers
│   ├── api/          # DRF views, serializers, urls
│   ├── ml/           # MoralMatcher, RealityPredictor, FeatureEngineer
│   └── scrapers/     # Playwright (ECI) + Scrapy (News) + Gemini filter
├── frontend/         # React + Vite + Tailwind
│   └── src/
│       ├── pages/    # Home, Constituency
│       └── components/ # MoralSliders, CandidateCard, WinnerBanner, RadarChart
├── supabase/         # Database migrations
└── .github/          # CI/CD workflows
```

## 🚀 Quick Start

See [SETUP.md](./SETUP.md) for detailed instructions.

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## 📊 Data Sources

| Source | Data Type | Update Frequency |
|--------|-----------|------------------|
| ECI Affidavit Portal | Asset declarations, criminal cases | Daily (23:30 IST) |
| The Hindu | State-level political news | Daily (00:00 IST) |
| Puthiya Thalaimurai | Regional Tamil news | Daily |
| Dinamalar | Regional Tamil news | Daily |
| News18 Tamil | Regional Tamil news | Daily |

## 🤖 ML Models

- **Moral Matcher**: `cross-encoder/ms-marco-MiniLM-L-6-v2` (CrossEncoder)
- **Reality Predictor**: XGBRegressor (300 trees, 11 features, 5-fold CV)
- **Gemini Filter**: `gemini-2.5-flash` (fact-checking + sentiment)

## License

MIT
