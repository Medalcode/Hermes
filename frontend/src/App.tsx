import { useState } from 'react'
import { Upload, Sparkles, Activity, BarChart2 } from 'lucide-react'
import localforage from 'localforage'
import UploadView from './components/UploadView'
import AutoAnalyzeDashboard from './components/AutoAnalyzeDashboard'
import PlottingView from './components/PlottingView'

export type AppState = {
  df_json: string | null;
  columns: string[];
  numeric_columns: string[];
  shape: number[];
}

function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [session, setSession] = useState<AppState>({
    df_json: null,
    columns: [],
    numeric_columns: [],
    shape: [0, 0]
  })
  
  // Persist session to IndexedDB
  const updateSession = async (newSession: Partial<AppState>) => {
    const updated = { ...session, ...newSession }
    setSession(updated)
    if (updated.df_json) {
      await localforage.setItem('myna_session', updated)
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <nav className="sidebar">
        <div className="logo">
          <h1>✨ Myna</h1>
        </div>
        <ul className="nav-links">
          <li className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>
            <Upload size={18} /> Carga
          </li>
          <li className={`nav-item ${activeTab === 'auto' ? 'active' : ''}`} onClick={() => setActiveTab('auto')}>
            <Sparkles size={18} /> Auto-Analyze
          </li>
          <li className={`nav-item ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>
            <Activity size={18} /> Estadísticas
          </li>
          <li className={`nav-item ${activeTab === 'plot' ? 'active' : ''}`} onClick={() => setActiveTab('plot')}>
            <BarChart2 size={18} /> Visualización
          </li>
        </ul>
      </nav>

      {/* Main Content Area */}
      <main className="content">
        {activeTab === 'upload' && <UploadView session={session} updateSession={updateSession} />}
        {activeTab === 'auto' && <AutoAnalyzeDashboard session={session} updateSession={updateSession} />}
        {activeTab === 'plot' && <PlottingView session={session} />}
        {activeTab === 'stats' && (
          <div className="card">
            <h2>Próximamente...</h2>
            <p>La vista de estadísticas está siendo migrada a React.</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
