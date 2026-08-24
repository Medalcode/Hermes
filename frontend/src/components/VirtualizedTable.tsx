import { useState } from 'react'

type VirtualizedTableProps = {
  columns: string[];
  data: Record<string, any>[];
  totalRows: number;
  pageSizeOptions?: number[];
}

export default function VirtualizedTable({
  columns,
  data,
  totalRows,
  pageSizeOptions = [10, 25, 50, 100]
}: VirtualizedTableProps) {
  const [pageSize, setPageSize] = useState(pageSizeOptions[0])
  const [currentPage, setCurrentPage] = useState(0)

  const totalPages = Math.ceil(data.length / pageSize) || 1
  const paginatedData = data.slice(currentPage * pageSize, (currentPage + 1) * pageSize)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div className="table-wrapper" style={{ maxHeight: '420px', overflowY: 'auto' }}>
        <table>
          <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-card, #ffffff)', zIndex: 2 }}>
            <tr>
              <th style={{ width: '50px', textAlign: 'center', background: '#f8fafc' }}>#</th>
              {columns.map((col, idx) => (
                <th key={idx}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIdx) => {
              const globalIndex = currentPage * pageSize + rowIdx + 1
              return (
                <tr key={rowIdx}>
                  <td style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', background: '#f8fafc' }}>
                    {globalIndex}
                  </td>
                  {columns.map((col, colIdx) => (
                    <td key={colIdx}>{row[col] !== undefined && row[col] !== null ? String(row[col]) : ''}</td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center" style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-2">
          <span>Mostrar:</span>
          <select
            value={pageSize}
            onChange={e => {
              setPageSize(Number(e.target.value))
              setCurrentPage(0)
            }}
            style={{ width: '80px', padding: '4px 8px' }}
          >
            {pageSizeOptions.map(size => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span>por página (Mostrando {paginatedData.length} de {data.length} filas en vista previa | {totalRows} totales)</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn"
            style={{ padding: '4px 12px', fontSize: '0.875rem' }}
            disabled={currentPage === 0}
            onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
          >
            Anterior
          </button>
          <span>
            Página {currentPage + 1} de {totalPages}
          </span>
          <button
            className="btn"
            style={{ padding: '4px 12px', fontSize: '0.875rem' }}
            disabled={currentPage >= totalPages - 1}
            onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  )
}
