/**
 * Utilitário para exportar dados em CSV
 * Inclui BOM (UTF-8 Signature) para compatibilidade com Excel
 */

export function exportarCSV(dados: object[], nomeArquivo: string) {
  if (dados.length === 0) {
    alert('Nenhum dado para exportar')
    return
  }

  const colunas = Object.keys(dados[0])

  // Cabeçalho com colunas
  const cabecalho = colunas.map(c => `"${c}"`).join(',')

  // Linhas de dados
  const linhas = dados.map(row =>
    colunas
      .map(col => {
        const valor = (row as any)[col] ?? ''
        // Escapa aspas duplas e envolve em aspas
        const valorStr = String(valor).replace(/"/g, '""')
        return `"${valorStr}"`
      })
      .join(',')
  )

  // Monta o CSV com BOM (UTF-8 Signature)
  const csv = [cabecalho, ...linhas].join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })

  // Cria URL para download
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${nomeArquivo}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
