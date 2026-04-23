import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

/**
 * WinnerBanner — Large hero card for predicted winner + ranked vote share bar chart
 */
export default function WinnerBanner({ predictions, formatCurrency, getHeatClass, getHeatLabel }) {
  if (!predictions || predictions.length === 0) return null

  const winner = predictions[0]
  const barData = predictions.map(p => ({
    name: p.candidate.name.length > 15 ? p.candidate.name.slice(0, 14) + '…' : p.candidate.name,
    fullName: p.candidate.name,
    voteShare: Math.round(p.predicted_vote_share * 1000) / 10,
    party: p.candidate.party,
    rank: p.predicted_rank,
  }))

  const BAR_COLORS = ['#4c6ef5', '#748ffc', '#91a7ff', '#bac8ff', '#dbe4ff', '#f0f4ff']

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div className="bg-tn-dark/95 backdrop-blur border border-white/10 rounded-lg p-3 shadow-xl">
        <p className="font-semibold text-white text-sm">{d.fullName}</p>
        <p className="text-white/50 text-xs">{d.party}</p>
        <p className="text-primary-300 font-bold mt-1">{d.voteShare}% predicted</p>
      </div>
    )
  }

  return (
    <div>
      {/* ─── Winner Hero Card ─── */}
      <div className="glass-card p-6 sm:p-8 mb-6 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute -top-20 -right-20 w-60 h-60 bg-primary-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-accent-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-white/40 uppercase tracking-wider font-medium">Predicted Winner</span>
            <span className="badge badge-green">#{winner.predicted_rank}</span>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            {/* Winner avatar */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/25 flex-shrink-0">
              <span className="text-2xl font-bold text-white">
                {winner.candidate.name?.split(' ').map(w => w[0]).join('').slice(0, 2)}
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <h3 className="text-2xl sm:text-3xl font-display font-bold gradient-text mb-1">
                {winner.candidate.name}
              </h3>
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <span className="text-lg text-white/60">{winner.candidate.party}</span>
                {winner.candidate.alliance && (
                  <span className="badge badge-blue">{winner.candidate.alliance}</span>
                )}
                {winner.candidate.is_incumbent && (
                  <span className="badge badge-yellow">Incumbent</span>
                )}
              </div>

              {/* Vote share display */}
              <div className="flex items-end gap-4">
                <div>
                  <p className="text-4xl font-display font-bold text-white">
                    {(winner.predicted_vote_share * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-white/30">Predicted Vote Share</p>
                </div>

                <div>
                  <p className="text-lg font-semibold text-white/70">
                    {(winner.confidence_score * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-white/30">Confidence</p>
                </div>

                {winner.anti_incumbency_score !== null && winner.anti_incumbency_score !== undefined && (
                  <div>
                    <p className={`text-lg font-semibold ${getHeatClass(winner.anti_incumbency_score)}`}>
                      {getHeatLabel(winner.anti_incumbency_score)}
                    </p>
                    <p className="text-xs text-white/30">Anti-Incumbency</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Vote Share Bar Chart ─── */}
      <div className="glass-card p-5">
        <h3 className="text-sm text-white/40 uppercase tracking-wider mb-4 font-medium">
          All Candidates — Predicted Vote Share
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis
                type="number"
                domain={[0, 'auto']}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 12 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.05)' }}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="voteShare" radius={[0, 6, 6, 0]} barSize={28}>
                {barData.map((entry, idx) => (
                  <Cell key={idx} fill={BAR_COLORS[idx] || BAR_COLORS[5]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
