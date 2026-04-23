import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRealityPrediction, getCandidates } from '../api/client'
import MoralSliders from '../components/MoralSliders'
import CandidateCard from '../components/CandidateCard'
import WinnerBanner from '../components/WinnerBanner'
import RadarChart from '../components/RadarChart'

export default function Constituency() {
  const { id } = useParams()
  const navigate = useNavigate()
  const constituencyId = parseInt(id)

  const [predictions, setPredictions] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [moralResults, setMoralResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [predLoading, setPredLoading] = useState(false)
  const [error, setError] = useState(null)
  const [openAccordion, setOpenAccordion] = useState(null)

  useEffect(() => {
    loadData()
  }, [constituencyId])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [candData, predData] = await Promise.allSettled([
        getCandidates(constituencyId),
        getRealityPrediction(constituencyId),
      ])

      if (candData.status === 'fulfilled') {
        setCandidates(candData.value.candidates || [])
      }
      if (predData.status === 'fulfilled') {
        setPredictions(predData.value.predictions || [])
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const constituencyName = candidates[0]?.constituency_name || `Constituency #${constituencyId}`
  const district = candidates[0]?.district || ''

  const formatCurrency = (val) => {
    if (!val) return '—'
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)}Cr`
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
    return `₹${val.toLocaleString('en-IN')}`
  }

  const getAssetGrowth = (current, previous) => {
    if (!current || !previous || previous === 0) return null
    return ((current - previous) / previous * 100).toFixed(1)
  }

  const getHeatClass = (score) => {
    if (!score || score < 0.3) return 'heat-low'
    if (score < 0.6) return 'heat-medium'
    return 'heat-high'
  }

  const getHeatLabel = (score) => {
    if (!score || score < 0.3) return 'LOW'
    if (score < 0.6) return 'MEDIUM'
    return 'HIGH'
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="skeleton h-10 w-64 mb-2"></div>
        <div className="skeleton h-6 w-40 mb-8"></div>
        <div className="glass-card p-8 mb-6">
          <div className="skeleton h-8 w-48 mb-4"></div>
          <div className="skeleton h-32 w-full mb-4"></div>
          <div className="skeleton h-12 w-40"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1,2,3].map(i => (
            <div key={i} className="glass-card p-6">
              <div className="skeleton h-16 w-16 rounded-full mx-auto mb-4"></div>
              <div className="skeleton h-6 w-32 mx-auto mb-2"></div>
              <div className="skeleton h-4 w-24 mx-auto"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-fade-in">
      {/* ─── Back Navigation ─── */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-white/40 hover:text-white/70 transition-colors mb-6 group"
      >
        <svg className="w-4 h-4 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        <span className="text-sm">Back to all constituencies</span>
      </button>

      {/* ─── 1. Header ─── */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-2">
          <h1 className="text-3xl sm:text-4xl font-display font-bold gradient-text">
            {constituencyName}
          </h1>
          {district && (
            <span className="badge badge-blue text-sm self-start">{district}</span>
          )}
        </div>
        <div className="flex items-center gap-4 text-white/40 text-sm">
          <span>{candidates.length} candidates</span>
          {candidates[0]?.total_voters && (
            <span>{candidates[0].total_voters.toLocaleString('en-IN')} voters</span>
          )}
        </div>
      </div>

      {/* ─── 2. Moral Sliders Section ─── */}
      <section className="mb-10">
        <MoralSliders
          constituencyId={constituencyId}
          onResult={(data) => setMoralResults(data)}
        />
      </section>

      {/* ─── 3. Top 3 Moral Matches ─── */}
      {moralResults && moralResults.top3 && (
        <section className="mb-10 animate-slide-up">
          <h2 className="text-xl font-display font-semibold text-white mb-4 flex items-center gap-2">
            <span className="text-2xl">🎯</span> Your Top Moral Matches
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {moralResults.top3.map((match, idx) => (
              <CandidateCard
                key={match.candidate.id}
                candidate={match.candidate}
                score={match.score}
                explanation={match.explanation}
                rank={idx + 1}
                formatCurrency={formatCurrency}
                getAssetGrowth={getAssetGrowth}
              />
            ))}
          </div>
        </section>
      )}

      {/* ─── 4. Reality Check Divider ─── */}
      <div className="divider-with-text text-white/50 my-10 text-lg font-display font-semibold">
        <span className="flex items-center gap-2">
          <span className="text-2xl">⚡</span> The Reality Check
        </span>
      </div>

      {/* ─── 5. Predicted Winner Banner ─── */}
      {predictions && predictions.length > 0 ? (
        <section className="mb-10">
          <WinnerBanner
            predictions={predictions}
            formatCurrency={formatCurrency}
            getHeatClass={getHeatClass}
            getHeatLabel={getHeatLabel}
          />
        </section>
      ) : (
        <div className="glass-card p-8 text-center mb-10">
          <div className="text-4xl mb-3">🔮</div>
          <h3 className="text-lg font-semibold text-white/70 mb-2">
            Predictions Not Yet Available
          </h3>
          <p className="text-white/40 text-sm">
            The ML model needs more data to generate predictions for this constituency.
            Check back after the data pipeline runs.
          </p>
        </div>
      )}

      {/* ─── 6. Radar Chart ─── */}
      {predictions && predictions.length > 0 && (
        <section className="mb-10">
          <h2 className="text-xl font-display font-semibold text-white mb-4">
            Candidate Comparison
          </h2>
          <div className="glass-card p-6">
            <RadarChart predictions={predictions} />
          </div>
        </section>
      )}

      {/* ─── 7. Candidates Deep Dive Accordion ─── */}
      <section className="mb-10">
        <h2 className="text-xl font-display font-semibold text-white mb-4 flex items-center gap-2">
          <span className="text-2xl">📊</span> Candidate Deep Dive
        </h2>
        <div className="space-y-3">
          {candidates.map((candidate) => {
            const isOpen = openAccordion === candidate.id
            const growth = getAssetGrowth(candidate.asset_value_current, candidate.asset_value_previous)
            const features = candidate.ml_features || {}

            return (
              <div key={candidate.id} className="glass-card overflow-hidden">
                {/* Accordion header */}
                <button
                  id={`accordion-${candidate.id}`}
                  onClick={() => setOpenAccordion(isOpen ? null : candidate.id)}
                  className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {/* Initials avatar */}
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500/30 to-accent-500/30 border border-white/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-white/80">
                        {candidate.name?.split(' ').map(w => w[0]).join('').slice(0, 2)}
                      </span>
                    </div>
                    <div className="text-left">
                      <h4 className="font-semibold text-white">{candidate.name}</h4>
                      <div className="flex items-center gap-2 text-sm text-white/50">
                        <span>{candidate.party}</span>
                        {candidate.alliance && (
                          <span className="badge badge-blue text-[10px]">{candidate.alliance}</span>
                        )}
                        {candidate.is_incumbent && (
                          <span className="badge badge-yellow text-[10px]">Incumbent</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {candidate.criminal_cases > 0 && (
                      <span className="badge badge-red">{candidate.criminal_cases} case{candidate.criminal_cases > 1 ? 's' : ''}</span>
                    )}
                    <svg
                      className={`w-5 h-5 text-white/30 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {/* Accordion content */}
                <div className={`accordion-content ${isOpen ? 'open' : ''}`}>
                  <div className="px-5 pb-5 border-t border-white/5">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
                      {/* Asset current */}
                      <div>
                        <p className="text-xs text-white/40 mb-1">Current Assets</p>
                        <p className="text-lg font-bold text-white">{formatCurrency(candidate.asset_value_current)}</p>
                      </div>
                      {/* Asset previous */}
                      <div>
                        <p className="text-xs text-white/40 mb-1">Previous Assets</p>
                        <p className="text-lg font-bold text-white/70">{formatCurrency(candidate.asset_value_previous)}</p>
                      </div>
                      {/* Growth */}
                      <div>
                        <p className="text-xs text-white/40 mb-1">Asset Growth</p>
                        <p className={`text-lg font-bold ${growth && parseFloat(growth) > 100 ? 'text-red-400' : 'text-green-400'}`}>
                          {growth ? `${growth}%` : '—'}
                        </p>
                      </div>
                      {/* Education */}
                      <div>
                        <p className="text-xs text-white/40 mb-1">Education</p>
                        <p className="text-sm font-medium text-white/70">{candidate.education || '—'}</p>
                      </div>
                    </div>

                    {/* ML Features */}
                    {features && Object.keys(features).length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/5">
                        <p className="text-xs text-white/40 mb-3 uppercase tracking-wider">ML Features</p>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">Local Support</p>
                            <p className="text-sm font-semibold text-white">{(features.local_support_ratio * 100).toFixed(1)}%</p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">Alliance Win Share</p>
                            <p className="text-sm font-semibold text-white">{(features.alliance_historical_win_share * 100).toFixed(1)}%</p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">Anti-Incumbency</p>
                            <p className={`text-sm font-semibold ${getHeatClass(features.anti_incumbency_score)}`}>
                              {features.anti_incumbency_score?.toFixed(2)} ({getHeatLabel(features.anti_incumbency_score)})
                            </p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">Sentiment Avg</p>
                            <p className={`text-sm font-semibold ${features.positive_sentiment_avg > 0.5 ? 'text-green-400' : 'text-yellow-400'}`}>
                              {features.positive_sentiment_avg?.toFixed(3)}
                            </p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">News (7d)</p>
                            <p className="text-sm font-semibold text-white">{features.news_volume_7d || 0} articles</p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-xs text-white/40">Power Fatigue</p>
                            <p className={`text-sm font-semibold ${getHeatClass(features.power_fatigue_score)}`}>
                              {features.power_fatigue_score?.toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Recent News */}
                    {candidate.recent_news && candidate.recent_news.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/5">
                        <p className="text-xs text-white/40 mb-3 uppercase tracking-wider">Recent Verified News</p>
                        <div className="space-y-2">
                          {candidate.recent_news.map((news, i) => (
                            <a
                              key={i}
                              href={news.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group"
                            >
                              <div className="flex items-center justify-between">
                                <p className="text-sm text-white/70 group-hover:text-white transition-colors line-clamp-1">
                                  {news.headline}
                                </p>
                                <span className={`text-xs font-mono ml-2 flex-shrink-0 ${
                                  news.sentiment_score > 0 ? 'text-green-400' : news.sentiment_score < 0 ? 'text-red-400' : 'text-white/40'
                                }`}>
                                  {news.sentiment_score > 0 ? '+' : ''}{news.sentiment_score?.toFixed(2)}
                                </span>
                              </div>
                              <p className="text-xs text-white/30 mt-1">{news.source}</p>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
