/**
 * CandidateCard — Displays a moral match result with compatibility score,
 * circular progress arc, and Gemini explanation.
 */
export default function CandidateCard({ candidate, score, explanation, rank, formatCurrency, getAssetGrowth }) {
  const percentage = Math.round(score * 100)
  const circumference = 2 * Math.PI * 36 // radius = 36
  const offset = circumference - (percentage / 100) * circumference

  const rankColors = {
    1: 'from-yellow-500 to-amber-400',
    2: 'from-gray-300 to-gray-400',
    3: 'from-orange-600 to-orange-500',
  }

  const growth = getAssetGrowth(candidate.asset_value_current, candidate.asset_value_previous)

  return (
    <div className="glass-card-hover p-5 flex flex-col relative overflow-hidden">
      {/* Rank badge */}
      <div className={`absolute top-3 right-3 w-7 h-7 rounded-full bg-gradient-to-br ${rankColors[rank] || 'from-gray-500 to-gray-600'} flex items-center justify-center`}>
        <span className="text-xs font-bold text-white">#{rank}</span>
      </div>

      {/* Top section: Avatar + Name + Score */}
      <div className="flex items-start gap-4 mb-4">
        {/* Circular progress score */}
        <div className="relative flex-shrink-0">
          <svg className="circular-progress w-20 h-20" viewBox="0 0 80 80">
            {/* Background circle */}
            <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
            {/* Progress arc */}
            <circle
              cx="40" cy="40" r="36"
              fill="none"
              stroke="url(#scoreGradient)"
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
            <defs>
              <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#4c6ef5" />
                <stop offset="100%" stopColor="#ff9800" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold text-white">{percentage}%</span>
          </div>
        </div>

        {/* Name and party */}
        <div className="min-w-0 pt-1">
          <h3 className="text-base font-semibold text-white truncate">{candidate.name}</h3>
          <p className="text-sm text-white/50">{candidate.party}</p>
          {candidate.alliance && (
            <span className="badge badge-blue text-[10px] mt-1 inline-block">{candidate.alliance}</span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 mb-3 text-xs">
        {candidate.criminal_cases > 0 ? (
          <span className="badge badge-red">
            ⚖️ {candidate.criminal_cases} case{candidate.criminal_cases > 1 ? 's' : ''}
          </span>
        ) : (
          <span className="badge badge-green">✓ Clean record</span>
        )}
        {growth && (
          <span className={`badge ${parseFloat(growth) > 100 ? 'badge-red' : 'badge-green'}`}>
            {growth > 0 ? '↑' : '↓'}{Math.abs(growth)}% assets
          </span>
        )}
      </div>

      {/* Gemini explanation */}
      <p className="text-sm text-white/60 leading-relaxed flex-1">
        {explanation}
      </p>

      {/* Asset info */}
      {candidate.asset_value_current && (
        <div className="mt-3 pt-3 border-t border-white/5 text-xs text-white/30">
          Assets: {formatCurrency(candidate.asset_value_current)}
          {candidate.age && <span className="ml-3">Age: {candidate.age}</span>}
        </div>
      )}
    </div>
  )
}
