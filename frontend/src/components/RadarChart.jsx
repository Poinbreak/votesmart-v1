import {
  Radar as RechartsRadar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts'

/**
 * RadarChart — Multi-candidate comparison across key metrics.
 * Shows up to 4 candidates on a single radar plot.
 */

const METRICS = [
  { key: 'vote_share', label: 'Vote Share', format: 'pct' },
  { key: 'confidence', label: 'Confidence', format: 'pct' },
  { key: 'clean_record', label: 'Clean Record', format: 'bool' },
  { key: 'alliance_strength', label: 'Alliance', format: 'pct' },
  { key: 'sentiment', label: 'Sentiment', format: 'score' },
  { key: 'incumbency_advantage', label: 'Incumbency', format: 'bool' },
]

const COLORS = ['#4c6ef5', '#ff9800', '#00c853', '#e53935']

export default function RadarChart({ predictions }) {
  if (!predictions || predictions.length === 0) return null

  // Take top 4 candidates for readability
  const top = predictions.slice(0, 4)

  // Build radar data
  const radarData = METRICS.map(metric => {
    const point = { metric: metric.label }
    top.forEach((pred, idx) => {
      const candidate = pred.candidate
      let value = 0

      switch (metric.key) {
        case 'vote_share':
          value = pred.predicted_vote_share * 100
          break
        case 'confidence':
          value = (pred.confidence_score || 0.5) * 100
          break
        case 'clean_record':
          value = (candidate.criminal_cases || 0) === 0 ? 100 : Math.max(0, 100 - candidate.criminal_cases * 25)
          break
        case 'alliance_strength':
          // Approximate from vote share rank
          value = Math.max(20, 100 - (pred.predicted_rank - 1) * 20)
          break
        case 'sentiment':
          value = 50 // Neutral default — would be enriched with actual sentiment data
          break
        case 'incumbency_advantage':
          value = candidate.is_incumbent ? 80 : 30
          break
        default:
          value = 50
      }

      point[`c${idx}`] = Math.min(100, Math.max(0, value))
    })
    return point
  })

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null
    return (
      <div className="bg-tn-dark/95 backdrop-blur border border-white/10 rounded-lg p-3 shadow-xl">
        <p className="text-white/50 text-xs mb-1">{label}</p>
        {payload.map((entry, idx) => (
          <p key={idx} style={{ color: entry.color }} className="text-sm font-medium">
            {top[idx]?.candidate.name.split(' ')[0]}: {Math.round(entry.value)}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="h-80 sm:h-96">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsRadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
            <PolarGrid stroke="rgba(255,255,255,0.08)" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
            />
            <PolarRadiusAxis
              domain={[0, 100]}
              tick={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            {top.map((pred, idx) => (
              <RechartsRadar
                key={pred.candidate.id}
                name={pred.candidate.name.length > 12 ? pred.candidate.name.slice(0, 11) + '…' : pred.candidate.name}
                dataKey={`c${idx}`}
                stroke={COLORS[idx]}
                fill={COLORS[idx]}
                fillOpacity={0.1}
                strokeWidth={2}
              />
            ))}
            <Legend
              wrapperStyle={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}
            />
          </RechartsRadarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend cards */}
      <div className="flex flex-wrap gap-2 mt-4 justify-center">
        {top.map((pred, idx) => (
          <div key={pred.candidate.id} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx] }}></div>
            <span className="text-xs text-white/60">{pred.candidate.name}</span>
            <span className="text-xs font-mono text-white/30">{pred.candidate.party}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
