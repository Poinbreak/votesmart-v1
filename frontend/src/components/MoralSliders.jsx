import { useState } from 'react'
import { runMoralMatch } from '../api/client'

const PRESET_CHIPS = [
  { id: 'anti-corruption', label: '🛡️ Anti-corruption', value: 'Anti-corruption, clean governance, no criminal record' },
  { id: 'infrastructure', label: '🏗️ Pro-infrastructure', value: 'Infrastructure development, roads, water supply, public transport' },
  { id: 'welfare', label: '🤝 Welfare-focused', value: 'Social welfare, education, healthcare, poverty reduction, subsidies' },
  { id: 'development', label: '🚀 Development-oriented', value: 'Economic development, job creation, industrial growth, technology' },
]

export default function MoralSliders({ constituencyId, onResult }) {
  const [moralText, setMoralText] = useState('')
  const [selectedChips, setSelectedChips] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const toggleChip = (chipId) => {
    setSelectedChips(prev =>
      prev.includes(chipId) ? prev.filter(c => c !== chipId) : [...prev, chipId]
    )
  }

  const handleSubmit = async () => {
    // Build combined moral input
    const chipValues = selectedChips
      .map(id => PRESET_CHIPS.find(c => c.id === id)?.value)
      .filter(Boolean)
      .join(', ')
    
    const combinedInput = [chipValues, moralText.trim()].filter(Boolean).join('. ')

    if (combinedInput.length < 5) {
      setError('Please describe your values or select at least one priority above.')
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      const result = await runMoralMatch(constituencyId, combinedInput)
      onResult(result)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to run moral matching. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="glass-card p-6 sm:p-8">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
          <span className="text-xl">🎯</span>
        </div>
        <div>
          <h2 className="text-xl font-display font-semibold text-white">Find Your Moral Match</h2>
          <p className="text-sm text-white/40">Tell us your values — we'll find the most aligned candidate</p>
        </div>
      </div>

      {/* Preset Value Chips */}
      <div className="flex flex-wrap gap-2 mb-4">
        {PRESET_CHIPS.map(chip => (
          <button
            key={chip.id}
            id={`chip-${chip.id}`}
            onClick={() => toggleChip(chip.id)}
            className={`chip ${selectedChips.includes(chip.id) ? 'chip-active' : ''}`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Free-text input */}
      <textarea
        id="moral-text-input"
        value={moralText}
        onChange={e => setMoralText(e.target.value)}
        placeholder="Describe your ideal candidate's values... (e.g., 'I want someone who fights for farmers' rights and has a clean criminal record')"
        rows={3}
        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/25 transition-all resize-none mb-4"
      />

      {/* Error message */}
      {error && (
        <div className="mb-4 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Submit button */}
      <button
        id="find-match-btn"
        onClick={handleSubmit}
        disabled={isLoading}
        className={`btn-primary w-full sm:w-auto ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Analyzing candidates...
          </span>
        ) : (
          '🎯 Find My Match'
        )}
      </button>

      {/* Loading skeleton */}
      {isLoading && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="skeleton h-12 w-12 rounded-full"></div>
                <div>
                  <div className="skeleton h-5 w-24 mb-1"></div>
                  <div className="skeleton h-3 w-16"></div>
                </div>
              </div>
              <div className="skeleton h-3 w-full mb-2"></div>
              <div className="skeleton h-3 w-3/4 mb-2"></div>
              <div className="skeleton h-3 w-1/2"></div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
