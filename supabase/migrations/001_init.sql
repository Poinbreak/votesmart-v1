-- ============================================================
-- VoteSmart TN — Database Schema
-- Supabase / PostgreSQL Migration 001
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: constituencies
-- ============================================================
CREATE TABLE constituencies (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  district TEXT NOT NULL,
  state TEXT DEFAULT 'Tamil Nadu',
  total_voters INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_constituencies_district ON constituencies(district);

-- ============================================================
-- TABLE: candidates
-- ============================================================
CREATE TABLE candidates (
  id SERIAL PRIMARY KEY,
  constituency_id INTEGER REFERENCES constituencies(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  party TEXT NOT NULL,
  alliance TEXT,
  is_incumbent BOOLEAN DEFAULT FALSE,
  terms_served INTEGER DEFAULT 0,
  asset_value_current BIGINT,
  asset_value_previous BIGINT,
  criminal_cases INTEGER DEFAULT 0,
  education TEXT,
  age INTEGER,
  affidavit_text TEXT,
  processed_text_payload JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidates_constituency ON candidates(constituency_id);
CREATE INDEX idx_candidates_party ON candidates(party);
CREATE INDEX idx_candidates_alliance ON candidates(alliance);

-- ============================================================
-- TABLE: news_articles
-- ============================================================
CREATE TABLE news_articles (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  url TEXT UNIQUE,
  headline TEXT,
  body TEXT,
  published_at TIMESTAMPTZ,
  sentiment_score FLOAT,
  is_factual BOOLEAN DEFAULT FALSE,
  local_mention BOOLEAN DEFAULT FALSE,
  scraped_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_candidate ON news_articles(candidate_id);
CREATE INDEX idx_news_factual ON news_articles(is_factual);
CREATE INDEX idx_news_published ON news_articles(published_at);

-- ============================================================
-- TABLE: ml_features (updated nightly by cron)
-- ============================================================
CREATE TABLE ml_features (
  id SERIAL PRIMARY KEY,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE UNIQUE,
  local_support_ratio FLOAT,
  alliance_historical_win_share FLOAT,
  power_fatigue_score FLOAT,
  wealth_divergence_score FLOAT,
  anti_incumbency_score FLOAT,
  positive_sentiment_avg FLOAT,
  news_volume_7d INTEGER,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ml_features_candidate ON ml_features(candidate_id);

-- ============================================================
-- TABLE: predictions (written by XGBoost inference)
-- ============================================================
CREATE TABLE predictions (
  id SERIAL PRIMARY KEY,
  constituency_id INTEGER REFERENCES constituencies(id) ON DELETE CASCADE,
  candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
  predicted_vote_share FLOAT,
  predicted_rank INTEGER,
  confidence_score FLOAT,
  model_version TEXT,
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_constituency ON predictions(constituency_id);
CREATE INDEX idx_predictions_candidate ON predictions(candidate_id);
CREATE INDEX idx_predictions_rank ON predictions(predicted_rank);

-- ============================================================
-- SEED DATA: All 234 Tamil Nadu Assembly Constituencies
-- ============================================================
INSERT INTO constituencies (name, district) VALUES
-- Thiruvallur District (1-8)
('Gummidipoondi', 'Thiruvallur'),
('Ponneri', 'Thiruvallur'),
('Tiruttani', 'Thiruvallur'),
('Thiruvallur', 'Thiruvallur'),
('Poonamallee', 'Thiruvallur'),
('Avadi', 'Thiruvallur'),
('Maduravoyal', 'Thiruvallur'),
('Ambattur', 'Thiruvallur'),

-- Chennai District (9-24)
('Madavaram', 'Chennai'),
('Thiruvottiyur', 'Chennai'),
('Dr. Radhakrishnan Nagar', 'Chennai'),
('Perambur', 'Chennai'),
('Kolathur', 'Chennai'),
('Villivakkam', 'Chennai'),
('Thiru. Vi. Ka. Nagar', 'Chennai'),
('Egmore', 'Chennai'),
('Royapuram', 'Chennai'),
('Harbour', 'Chennai'),
('Chepauk-Thiruvallikeni', 'Chennai'),
('Thousand Lights', 'Chennai'),
('Anna Nagar', 'Chennai'),
('Virugambakkam', 'Chennai'),
('Saidapet', 'Chennai'),
('T. Nagar', 'Chennai'),

-- Kancheepuram District (25-32)
('Mylapore', 'Kancheepuram'),
('Velachery', 'Kancheepuram'),
('Sholinganallur', 'Kancheepuram'),
('Alandur', 'Kancheepuram'),
('Sriperumbudur', 'Kancheepuram'),
('Pallavaram', 'Kancheepuram'),
('Tambaram', 'Kancheepuram'),
('Kancheepuram', 'Kancheepuram'),

-- Chengalpattu District (33-36)
('Chengalpattu', 'Chengalpattu'),
('Thiruporur', 'Chengalpattu'),
('Cheyyur', 'Chengalpattu'),
('Madurantakam', 'Chengalpattu'),

-- Ranipet District (37-40)
('Uthiramerur', 'Ranipet'),
('Arakkonam', 'Ranipet'),
('Sholingur', 'Ranipet'),
('Ranipet', 'Ranipet'),

-- Vellore District (41-46)
('Arcot', 'Vellore'),
('Vellore', 'Vellore'),
('Anaikattu', 'Vellore'),
('Kilvaithinankuppam', 'Vellore'),
('Gudiyattham', 'Vellore'),
('Vaniyambadi', 'Vellore'),

-- Tirupattur District (47-49)
('Ambur', 'Tirupattur'),
('Jolarpet', 'Tirupattur'),
('Tirupattur', 'Tirupattur'),

-- Krishnagiri District (50-55)
('Uthangarai', 'Krishnagiri'),
('Bargur', 'Krishnagiri'),
('Krishnagiri', 'Krishnagiri'),
('Veppanahalli', 'Krishnagiri'),
('Hosur', 'Krishnagiri'),
('Thalli', 'Krishnagiri'),

-- Dharmapuri District (56-59)
('Palacode', 'Dharmapuri'),
('Pennagaram', 'Dharmapuri'),
('Dharmapuri', 'Dharmapuri'),
('Harur', 'Dharmapuri'),

-- Tiruvannamalai District (60-67)
('Chengam', 'Tiruvannamalai'),
('Tiruvannamalai', 'Tiruvannamalai'),
('Kilpennathur', 'Tiruvannamalai'),
('Kalasapakkam', 'Tiruvannamalai'),
('Polur', 'Tiruvannamalai'),
('Arani', 'Tiruvannamalai'),
('Cheyyar', 'Tiruvannamalai'),
('Vandavasi', 'Tiruvannamalai'),

-- Viluppuram District (68-73)
('Gingee', 'Viluppuram'),
('Mailam', 'Viluppuram'),
('Tindivanam', 'Viluppuram'),
('Vanur', 'Viluppuram'),
('Viluppuram', 'Viluppuram'),
('Vikravandi', 'Viluppuram'),

-- Kallakurichi District (74-77)
('Kallakurichi', 'Kallakurichi'),
('Sankarapuram', 'Kallakurichi'),
('Ulundurpet', 'Kallakurichi'),
('Rishivandiyam', 'Kallakurichi'),

-- Cuddalore District (78-83)
('Cuddalore', 'Cuddalore'),
('Kurinjipadi', 'Cuddalore'),
('Bhuvanagiri', 'Cuddalore'),
('Chidambaram', 'Cuddalore'),
('Kattumannarkoil', 'Cuddalore'),
('Sirkazhi', 'Cuddalore'),

-- Mayiladuthurai District (84-86)
('Mayiladuthurai', 'Mayiladuthurai'),
('Poompuhar', 'Mayiladuthurai'),
('Nagapattinam', 'Mayiladuthurai'),

-- Thanjavur District (87-93)
('Kilvelur', 'Thanjavur'),
('Nannilam', 'Thanjavur'),
('Thiruvaiyaru', 'Thanjavur'),
('Thanjavur', 'Thanjavur'),
('Orathanadu', 'Thanjavur'),
('Pattukkottai', 'Thanjavur'),
('Peravurani', 'Thanjavur'),

-- Thiruvarur District (94-97)
('Thiruvarur', 'Thiruvarur'),
('Mannargudi', 'Thiruvarur'),
('Thiruthuraipoondi', 'Thiruvarur'),
('Vedaranyam', 'Thiruvarur'),

-- Pudukkottai District (98-103)
('Gandharvakottai', 'Pudukkottai'),
('Viralimalai', 'Pudukkottai'),
('Pudukkottai', 'Pudukkottai'),
('Thirumayam', 'Pudukkottai'),
('Alangudi', 'Pudukkottai'),
('Aranthangi', 'Pudukkottai'),

-- Salem District (104-114)
('Gangavalli', 'Salem'),
('Attur', 'Salem'),
('Yercaud', 'Salem'),
('Omalur', 'Salem'),
('Mettur', 'Salem'),
('Edappadi', 'Salem'),
('Sankari', 'Salem'),
('Salem West', 'Salem'),
('Salem North', 'Salem'),
('Salem South', 'Salem'),
('Veerapandi', 'Salem'),

-- Namakkal District (115-120)
('Rasipuram', 'Namakkal'),
('Senthamangalam', 'Namakkal'),
('Namakkal', 'Namakkal'),
('Paramathi-Velur', 'Namakkal'),
('Tiruchengode', 'Namakkal'),
('Kumarapalayam', 'Namakkal'),

-- Erode District (121-129)
('Erode East', 'Erode'),
('Erode West', 'Erode'),
('Modakkurichi', 'Erode'),
('Perundurai', 'Erode'),
('Bhavani', 'Erode'),
('Anthiyur', 'Erode'),
('Gobichettipalayam', 'Erode'),
('Bhavanisagar', 'Erode'),
('Nambiyur', 'Erode'),

-- Nilgiris District (130-132)
('Udhagamandalam', 'Nilgiris'),
('Gudalur', 'Nilgiris'),
('Coonoor', 'Nilgiris'),

-- Coimbatore District (133-142)
('Mettupalayam', 'Coimbatore'),
('Sulur', 'Coimbatore'),
('Kavundampalayam', 'Coimbatore'),
('Coimbatore North', 'Coimbatore'),
('Thondamuthur', 'Coimbatore'),
('Coimbatore South', 'Coimbatore'),
('Singanallur', 'Coimbatore'),
('Kinathukadavu', 'Coimbatore'),
('Pollachi', 'Coimbatore'),
('Valparai', 'Coimbatore'),

-- Tiruppur District (143-148)
('Dharapuram', 'Tiruppur'),
('Kangeyam', 'Tiruppur'),
('Udumalpet', 'Tiruppur'),
('Madathukulam', 'Tiruppur'),
('Palladam', 'Tiruppur'),
('Tiruppur North', 'Tiruppur'),

-- Tiruppur contd. (149-150)
('Tiruppur South', 'Tiruppur'),
('Avinashi', 'Tiruppur'),

-- Karur District (151-154)
('Aravakurichi', 'Karur'),
('Karur', 'Karur'),
('Krishnarayapuram', 'Karur'),
('Kulithalai', 'Karur'),

-- Dindigul District (155-162)
('Palani', 'Dindigul'),
('Oddanchatram', 'Dindigul'),
('Athoor', 'Dindigul'),
('Nilakkottai', 'Dindigul'),
('Natham', 'Dindigul'),
('Dindigul', 'Dindigul'),
('Vedasandur', 'Dindigul'),
('Kodaikanal', 'Dindigul'),

-- Tiruchirappalli District (163-172)
('Manapparai', 'Tiruchirappalli'),
('Srirangam', 'Tiruchirappalli'),
('Tiruchirappalli West', 'Tiruchirappalli'),
('Tiruchirappalli East', 'Tiruchirappalli'),
('Thiruverumbur', 'Tiruchirappalli'),
('Lalgudi', 'Tiruchirappalli'),
('Manachanallur', 'Tiruchirappalli'),
('Musiri', 'Tiruchirappalli'),
('Thuraiyur', 'Tiruchirappalli'),
('Perambalur', 'Tiruchirappalli'),

-- Perambalur District (173-174)
('Kunnam', 'Perambalur'),
('Ariyalur', 'Perambalur'),

-- Sivaganga District (175-179)
('Karaikudi', 'Sivaganga'),
('Sivaganga', 'Sivaganga'),
('Manamadurai', 'Sivaganga'),
('Devakottai', 'Sivaganga'),
('Ilayankudi', 'Sivaganga'),

-- Madurai District (180-189)
('Melur', 'Madurai'),
('Madurai East', 'Madurai'),
('Sholavandan', 'Madurai'),
('Madurai North', 'Madurai'),
('Madurai South', 'Madurai'),
('Madurai Central', 'Madurai'),
('Madurai West', 'Madurai'),
('Thiruparankundram', 'Madurai'),
('Tirumangalam', 'Madurai'),
('Usilampatti', 'Madurai'),

-- Theni District (190-194)
('Andipatti', 'Theni'),
('Periyakulam', 'Theni'),
('Bodinayakanur', 'Theni'),
('Cumbum', 'Theni'),
('Theni', 'Theni'),

-- Virudhunagar District (195-201)
('Rajapalayam', 'Virudhunagar'),
('Srivilliputhur', 'Virudhunagar'),
('Sattur', 'Virudhunagar'),
('Sivakasi', 'Virudhunagar'),
('Virudhunagar', 'Virudhunagar'),
('Aruppukkottai', 'Virudhunagar'),
('Tiruchuli', 'Virudhunagar'),

-- Ramanathapuram District (202-205)
('Paramakudi', 'Ramanathapuram'),
('Tiruvadanai', 'Ramanathapuram'),
('Ramanathapuram', 'Ramanathapuram'),
('Mudhukulathur', 'Ramanathapuram'),

-- Thoothukudi District (206-211)
('Vilathikulam', 'Thoothukudi'),
('Thoothukudi', 'Thoothukudi'),
('Tiruchendur', 'Thoothukudi'),
('Srivaikuntam', 'Thoothukudi'),
('Ottapidaram', 'Thoothukudi'),
('Kovilpatti', 'Thoothukudi'),

-- Tenkasi District (212-216)
('Sankarankovil', 'Tenkasi'),
('Vasudevanallur', 'Tenkasi'),
('Kadayanallur', 'Tenkasi'),
('Tenkasi', 'Tenkasi'),
('Alangulam', 'Tenkasi'),

-- Tirunelveli District (217-222)
('Tirunelveli', 'Tirunelveli'),
('Ambasamudram', 'Tirunelveli'),
('Palayamkottai', 'Tirunelveli'),
('Nanguneri', 'Tirunelveli'),
('Radhapuram', 'Tirunelveli'),
('Cheranmahadevi', 'Tirunelveli'),

-- Kanniyakumari District (223-228)
('Kanniyakumari', 'Kanniyakumari'),
('Nagercoil', 'Kanniyakumari'),
('Colachel', 'Kanniyakumari'),
('Padmanabhapuram', 'Kanniyakumari'),
('Vilavancode', 'Kanniyakumari'),
('Killiyoor', 'Kanniyakumari'),

-- Ariyalur District contd. (229-230)
('Jayankondam', 'Ariyalur'),
('Sendurai', 'Ariyalur'),

-- Papanasam & Kumbakonam (231-234)
('Papanasam', 'Thanjavur'),
('Kumbakonam', 'Thanjavur'),
('Thiruvidaimarudur', 'Thanjavur'),
('Pattukottai', 'Thanjavur');

-- ============================================================
-- Row-Level Security (RLS) Policies
-- ============================================================
ALTER TABLE constituencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

-- Public read access for all tables
CREATE POLICY "Public read access" ON constituencies FOR SELECT USING (true);
CREATE POLICY "Public read access" ON candidates FOR SELECT USING (true);
CREATE POLICY "Public read access" ON news_articles FOR SELECT USING (true);
CREATE POLICY "Public read access" ON ml_features FOR SELECT USING (true);
CREATE POLICY "Public read access" ON predictions FOR SELECT USING (true);

-- Service role full access
CREATE POLICY "Service role full access" ON constituencies FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON candidates FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON news_articles FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON ml_features FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON predictions FOR ALL USING (auth.role() = 'service_role');
