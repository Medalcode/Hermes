import { useState } from 'react'
import type { AppState } from '../App'
import { UploadCloud } from 'lucide-react'

type Props = {
  session: AppState;
  updateSession: (s: Partial<AppState>) => void;
}

export default function UploadView({ session, updateSession }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [delimiter, setDelimiter] = useState(',')
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('delimiter', delimiter)

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (res.ok) {
        updateSession({
          df_json: data.df_json,
          columns: data.columns,
          numeric_columns: data.numeric_columns,
          shape: data.shape
        })
        setPreview(data.preview || [])
      } else {
        setError(data.error || 'Error al cargar el archivo')
      }
    } catch (err) {
      setError('Error de red al intentar cargar el archivo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Cargar Datos</h2>
      <div className="card">
        <form onSubmit={handleUpload} className="flex items-center gap-4">
          <label style={{ 
            display: 'flex', alignItems: 'center', gap: '8px',
            border: '2px dashed var(--border-color)', padding: '16px 24px', 
            borderRadius: '8px', cursor: 'pointer', background: 'white'
          }}>
            <UploadCloud size={24} color="var(--primary-color)" />
            <input 
              type="file" 
              accept=".csv,.xlsx" 
              style={{ display: 'none' }} 
              onChange={e => setFile(e.target.files?.[0] || null)}
            />
            <span style={{ color: 'var(--text-muted)' }}>
              {file ? file.name : 'Seleccionar Archivo'}
            </span>
          </label>
          
          <select value={delimiter} onChange={e => setDelimiter(e.target.value)} style={{ width: '200px' }}>
            <option value=",">Separador: Coma (,)</option>
            <option value=";">Separador: Punto y Coma (;)</option>
          </select>
          
          <button type="submit" className="btn btn-primary" disabled={loading || !file}>
            {loading ? 'Cargando...' : 'Cargar'}
          </button>
        </form>
        {error && <p style={{ color: '#ef4444', marginTop: '16px' }}>{error}</p>}
      </div>

      {session.shape[0] > 0 && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3>Vista Previa del Dataset</h3>
            <span style={{ background: '#eef2ff', color: 'var(--primary-color)', padding: '4px 12px', borderRadius: '16px', fontSize: '0.875rem', fontWeight: 600 }}>
              {session.shape[0]} filas × {session.shape[1]} columnas
            </span>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {session.columns.map((c, i) => <th key={i}>{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    {session.columns.map((c, j) => <td key={j}>{row[c]}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
