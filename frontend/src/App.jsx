import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Constituency from './pages/Constituency'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        {/* ─── Navigation Bar ─── */}
        <nav className="sticky top-0 z-50 glass-card border-b border-white/5 rounded-none">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <a href="/" className="flex items-center gap-3 group">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-primary-500/40 transition-shadow">
                  <span className="text-white font-bold text-lg">V</span>
                </div>
                <div>
                  <h1 className="text-lg font-display font-bold gradient-text">VoteSmart TN</h1>
                  <p className="text-[10px] text-white/40 -mt-1 tracking-wider uppercase">Election Intelligence</p>
                </div>
              </a>
              <div className="flex items-center gap-4">
                <span className="text-xs text-white/30 hidden sm:block">234 Constituencies • Data-Driven</span>
                <div className="w-2 h-2 rounded-full bg-success animate-pulse-slow" title="Live data"></div>
              </div>
            </div>
          </div>
        </nav>

        {/* ─── Routes ─── */}
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/constituency/:id" element={<Constituency />} />
          </Routes>
        </main>

        {/* ─── Footer ─── */}
        <footer className="border-t border-white/5 mt-20">
          <div className="max-w-7xl mx-auto px-4 py-8 text-center">
            <p className="text-white/30 text-sm">
              VoteSmart TN — Built for Tamil Nadu voters. Data from ECI affidavits & verified news sources.
            </p>
            <p className="text-white/20 text-xs mt-2">
              Predictions are statistical estimates, not guarantees. Always exercise your democratic right responsibly.
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
