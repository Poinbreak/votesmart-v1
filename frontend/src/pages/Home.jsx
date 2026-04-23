import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getConstituencies } from '../api/client'

const DISTRICTS_PER_PAGE = 8

export default function Home() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedDistrict, setSelectedDistrict] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    fetchConstituencies()
  }, [])

  const fetchConstituencies = async () => {
    try {
      setLoading(true)
      const result = await getConstituencies()
      setData(result)
    } catch (err) {
      setError(err.message || 'Failed to load constituencies')
    } finally {
      setLoading(false)
    }
  }

  const filteredDistricts = useMemo(() => {
    if (!data?.districts) return {}
    let districts = { ...data.districts }

    if (selectedDistrict) {
      districts = { [selectedDistrict]: districts[selectedDistrict] || [] }
    }

    if (search.trim()) {
      const q = search.toLowerCase()
      const filtered = {}
      Object.entries(districts).forEach(([district, constituencies]) => {
        const matches = constituencies.filter(
          c => c.name.toLowerCase().includes(q) || district.toLowerCase().includes(q)
        )
        if (matches.length > 0) filtered[district] = matches
      })
      return filtered
    }

    return districts
  }, [data, search, selectedDistrict])

  const districtNames = useMemo(() => 
    data?.districts ? Object.keys(data.districts).sort() : [],
    [data]
  )

  const visibleDistricts = useMemo(() => {
    const entries = Object.entries(filteredDistricts)
    return showAll ? entries : entries.slice(0, DISTRICTS_PER_PAGE)
  }, [filteredDistricts, showAll])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <div className="skeleton h-12 w-96 mx-auto mb-4"></div>
          <div className="skeleton h-6 w-64 mx-auto"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="glass-card p-6">
              <div className="skeleton h-6 w-32 mb-4"></div>
              <div className="space-y-2">
                <div className="skeleton h-4 w-full"></div>
                <div className="skeleton h-4 w-3/4"></div>
                <div className="skeleton h-4 w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center">
        <div className="glass-card p-12 max-w-lg mx-auto">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-white mb-2">Connection Error</h2>
          <p className="text-white/50 mb-6">{error}</p>
          <button onClick={fetchConstituencies} className="btn-primary">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:py-12">
      {/* ─── Hero Section ─── */}
      <div className="text-center mb-12 animate-fade-in">
        <div className="inline-flex items-center gap-2 mb-4 px-4 py-1.5 rounded-full bg-primary-600/10 border border-primary-500/20">
          <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse"></span>
          <span className="text-sm text-primary-300 font-medium">Live Election Intelligence</span>
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold mb-4">
          <span className="gradient-text">VoteSmart TN</span>
        </h1>
        <p className="text-lg text-white/50 max-w-2xl mx-auto leading-relaxed">
          Data-driven insights for all <span className="text-white font-semibold">{data?.total || 234}</span> Tamil Nadu constituencies.
          Find candidates that match your values — and see who's likely to win.
        </p>
      </div>

      {/* ─── Search & Filter ─── */}
      <div className="glass-card p-4 sm:p-6 mb-8 animate-slide-up">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="constituency-search"
              type="text"
              placeholder="Search constituency or district..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/25 transition-all"
            />
          </div>

          {/* District filter */}
          <select
            id="district-filter"
            value={selectedDistrict}
            onChange={e => setSelectedDistrict(e.target.value)}
            className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-primary-500/50 transition-all cursor-pointer appearance-none min-w-[200px]"
          >
            <option value="" className="bg-tn-dark">All Districts</option>
            {districtNames.map(d => (
              <option key={d} value={d} className="bg-tn-dark">{d}</option>
            ))}
          </select>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-6 mt-4 pt-3 border-t border-white/5">
          <span className="text-sm text-white/40">
            Showing <strong className="text-white/70">{Object.values(filteredDistricts).flat().length}</strong> constituencies
          </span>
          <span className="text-sm text-white/40">
            in <strong className="text-white/70">{Object.keys(filteredDistricts).length}</strong> districts
          </span>
        </div>
      </div>

      {/* ─── District Cards Grid ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {visibleDistricts.map(([district, constituencies], idx) => (
          <div
            key={district}
            className="glass-card-hover p-5 animate-slide-up"
            style={{ animationDelay: `${idx * 0.05}s` }}
          >
            {/* District header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-display font-semibold text-white">
                {district}
              </h3>
              <span className="badge badge-blue">{constituencies.length}</span>
            </div>

            {/* Constituency list */}
            <div className="space-y-1.5">
              {constituencies.map(constituency => (
                <button
                  key={constituency.id}
                  id={`constituency-${constituency.id}`}
                  onClick={() => navigate(`/constituency/${constituency.id}`)}
                  className="w-full text-left px-3 py-2 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/5 transition-all duration-200 flex items-center justify-between group"
                >
                  <span className="group-hover:translate-x-1 transition-transform duration-200">
                    {constituency.name}
                  </span>
                  <svg className="w-4 h-4 text-white/20 group-hover:text-primary-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Show More button */}
      {!showAll && Object.keys(filteredDistricts).length > DISTRICTS_PER_PAGE && (
        <div className="text-center mt-8">
          <button
            onClick={() => setShowAll(true)}
            className="btn-secondary"
          >
            Show All {Object.keys(filteredDistricts).length} Districts
          </button>
        </div>
      )}

      {/* Empty state */}
      {Object.keys(filteredDistricts).length === 0 && (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-white/70 mb-2">No Results Found</h3>
          <p className="text-white/40">Try a different search term or clear the district filter.</p>
        </div>
      )}
    </div>
  )
}
