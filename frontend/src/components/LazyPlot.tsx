import { useEffect, useState } from 'react'

type LazyPlotProps = {
  data: any[];
  layout: any;
  config?: any;
  style?: React.CSSProperties;
  useResizeHandler?: boolean;
}

export default function LazyPlot(props: LazyPlotProps) {
  const [PlotComponent, setPlotComponent] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true
    Promise.all([
      import('react-plotly.js/factory'),
      import('plotly.js-dist-min')
    ]).then(([createPlotlyComponent, Plotly]) => {
      if (isMounted) {
        const Plot = createPlotlyComponent.default(Plotly.default || Plotly)
        setPlotComponent(() => Plot)
        setLoading(false)
      }
    }).catch(err => {
      console.error('Failed to load Plotly module:', err)
      if (isMounted) setLoading(false)
    })

    return () => {
      isMounted = false
    }
  }, [])

  if (loading || !PlotComponent) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: '400px', color: 'var(--text-muted)' }}>
        <p>Cargando motor de visualización (Plotly.js)...</p>
      </div>
    )
  }

  return <PlotComponent {...props} />
}
