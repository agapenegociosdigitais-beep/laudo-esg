'use client'

/**
 * Painel de conformidade ESG com 4 cards de verificação:
 * Embargo IBAMA, Embargo SEMAS-PA, Unidade de Conservação, Terra Indígena.
 * Exibe detalhes expandidos quando há irregularidade.
 */
import type {
  Analise,
  ResultadoEmbargo,
  ResultadoAreaProtegida,
  ResultadoSobreposicaoSimples,
  ResultadoTrabalhoEscravo,
  ResultadoBalancoAmbiental,
} from '@/types'

interface Props {
  analise: Analise
  onGerarRelatorio: () => void
  gerandoRelatorio: boolean
}

// ─── Link de consulta externa ────────────────────────────────────────────────

function LinkConsulta({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
    >
      🔍 {label} ↗
    </a>
  )
}

// Configuração visual por nível de risco ESG
const RISCO_CONFIG: Record<string, { cor: string; bg: string; label: string }> = {
  BAIXO:   { cor: 'text-green-700',  bg: 'bg-green-50  border-green-200',  label: 'Risco Baixo'   },
  MÉDIO:   { cor: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-200', label: 'Risco Médio'   },
  ALTO:    { cor: 'text-orange-700', bg: 'bg-orange-50 border-orange-200', label: 'Risco Alto'    },
  CRÍTICO: { cor: 'text-red-700',    bg: 'bg-red-50    border-red-200',    label: 'Risco Crítico' },
}

// ─── Card de Embargo (IBAMA ou SEMAS) ─────────────────────────────────────────

interface CardEmbargoProps {
  titulo: string
  subtitulo: string
  dados?: ResultadoEmbargo
  linkConsulta?: string
  labelConsulta?: string
}

function CardEmbargo({ titulo, subtitulo, dados, linkConsulta, labelConsulta }: CardEmbargoProps) {
  // API indisponível ou campo ainda não preenchido
  if (!dados || dados.embargado === null) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-gray-400">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full">
          — Não verificado
        </span>
        {dados?.motivo && (
          <p className="mt-1 text-xs text-gray-400 italic">{dados.motivo}</p>
        )}
      </div>
    )
  }

  // Propriedade regular — sem embargo
  if (!dados.embargado) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-xs text-green-600 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-green-500">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
          ✓ Regular
        </span>
        <p className="mt-1 text-xs text-green-600">Nenhum embargo ativo encontrado.</p>
      </div>
    )
  }

  // Propriedade embargada
  return (
    <div className="rounded-xl border border-red-300 bg-red-50 p-4">
      <p className="text-xs text-red-600 uppercase tracking-wide mb-1">{titulo}</p>
      <p className="text-xs text-red-400">{subtitulo}</p>
      <span className="mt-2 inline-block text-xs bg-red-100 text-red-800 border border-red-300 px-2.5 py-0.5 rounded-full font-semibold">
        ⛔ Embargado
      </span>

      {/* Detalhes do embargo */}
      <div className="mt-3 space-y-1 text-xs text-red-800">
        {dados.numero_embargo && (
          <p><span className="font-medium">Nº Termo de Embargo:</span> {dados.numero_embargo}</p>
        )}
        {dados.area_embargada_ha != null && (
          <p><span className="font-medium">Área embargada:</span> {(dados.area_embargada_ha ?? 0).toFixed(2)} ha</p>
        )}
        {dados.motivo && (
          <p><span className="font-medium">Motivo:</span> {dados.motivo}</p>
        )}
      </div>
      <p className="mt-2 text-xs text-red-400 italic">Fonte: {dados.fonte}</p>
      {linkConsulta && (
        <LinkConsulta href={linkConsulta} label={labelConsulta ?? 'Consultar no sistema oficial'} />
      )}
    </div>
  )
}

// ─── Card de Área Protegida (UC ou TI) ────────────────────────────────────────

interface CardAreaProtegidaProps {
  titulo: string
  subtitulo: string
  dados?: ResultadoAreaProtegida
  /** TI usa vermelho em caso de sobreposição; UC usa amarelo (menos restritivo) */
  corSobreposicao: 'red' | 'yellow'
  linkConsulta?: string
  labelConsulta?: string
}

function CardAreaProtegida({ titulo, subtitulo, dados, corSobreposicao, linkConsulta, labelConsulta }: CardAreaProtegidaProps) {
  if (!dados || dados.sobreposicao_detectada === null) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-gray-400">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full">
          — Não verificado
        </span>
        {dados?.motivo_nao_verificado && (
          <p className="mt-1 text-xs text-gray-400 italic">{dados.motivo_nao_verificado}</p>
        )}
      </div>
    )
  }

  // Sem sobreposição — situação regular
  if (!dados.sobreposicao_detectada) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-xs text-green-600 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-green-500">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
          ✓ Sem sobreposição
        </span>
        <p className="mt-1 text-xs text-green-600">
          Geometria da propriedade não intersecta nenhuma área cadastrada.
        </p>
      </div>
    )
  }

  // Sobreposição detectada — cor varia por tipo
  const isRed = corSobreposicao === 'red'
  const borderClass  = isRed ? 'border-red-300'    : 'border-yellow-300'
  const bgClass      = isRed ? 'bg-red-50'          : 'bg-yellow-50'
  const titleClass   = isRed ? 'text-red-600'       : 'text-yellow-700'
  const subClass     = isRed ? 'text-red-400'       : 'text-yellow-500'
  const badgeBg      = isRed ? 'bg-red-100'         : 'bg-yellow-100'
  const badgeText    = isRed ? 'text-red-800'        : 'text-yellow-800'
  const badgeBorder  = isRed ? 'border-red-300'     : 'border-yellow-300'
  const detailClass  = isRed ? 'text-red-800'       : 'text-yellow-800'
  const sourceClass  = isRed ? 'text-red-400'       : 'text-yellow-500'

  return (
    <div className={`rounded-xl border ${borderClass} ${bgClass} p-4`}>
      <p className={`text-xs ${titleClass} uppercase tracking-wide mb-1`}>{titulo}</p>
      <p className={`text-xs ${subClass}`}>{subtitulo}</p>
      <span className={`mt-2 inline-block text-xs ${badgeBg} ${badgeText} border ${badgeBorder} px-2.5 py-0.5 rounded-full font-semibold`}>
        ⚠ Sobreposição detectada
      </span>

      {/* Detalhes da sobreposição */}
      <div className={`mt-3 space-y-1 text-xs ${detailClass}`}>
        {dados.nome_area && (
          <p><span className="font-medium">Área:</span> {dados.nome_area}</p>
        )}
        {dados.categoria && (
          <p><span className="font-medium">Categoria:</span> {dados.categoria}</p>
        )}
        {dados.esfera && (
          <p><span className="font-medium">Esfera:</span> {dados.esfera}</p>
        )}
        {dados.percentual_sobreposicao != null && (
          <p>
            <span className="font-medium">Sobreposição:</span>{' '}
            {(dados.percentual_sobreposicao ?? 0).toFixed(1)}%
            {dados.area_sobreposicao_ha != null && (
              <span> ({(dados.area_sobreposicao_ha ?? 0).toFixed(2)} ha)</span>
            )}
          </p>
        )}
      </div>
      <p className={`mt-2 text-xs ${sourceClass} italic`}>Fonte: {dados.fonte}</p>
      {linkConsulta && (
        <LinkConsulta href={linkConsulta} label={labelConsulta ?? 'Consultar no sistema oficial'} />
      )}
    </div>
  )
}

// ─── Card Sobreposição simples (quilombola / assentamento) ────────────────────

interface CardSobreposicaoProps {
  titulo: string
  subtitulo: string
  dados?: ResultadoSobreposicaoSimples
  corSobreposicao?: 'red' | 'orange'
  linkConsulta?: string
  labelConsulta?: string
}

function CardSobreposicao({ titulo, subtitulo, dados, corSobreposicao = 'orange', linkConsulta, labelConsulta }: CardSobreposicaoProps) {
  if (!dados) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-gray-400">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full">
          — Não verificado
        </span>
      </div>
    )
  }

  if (!dados.verificado) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-gray-400">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full">
          — Simulado
        </span>
        <p className="mt-1 text-xs text-gray-400 italic">Fonte: {dados.fonte}</p>
      </div>
    )
  }

  if (!dados.sobreposicao) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-xs text-green-600 uppercase tracking-wide mb-1">{titulo}</p>
        <p className="text-xs text-green-500">{subtitulo}</p>
        <span className="mt-2 inline-block text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
          ✓ Sem sobreposição
        </span>
        <p className="mt-1 text-xs text-green-600 italic">Fonte: {dados.fonte}</p>
      </div>
    )
  }

  const isRed = corSobreposicao === 'red'
  return (
    <div className={`rounded-xl border p-4 ${isRed ? 'border-red-300 bg-red-50' : 'border-orange-300 bg-orange-50'}`}>
      <p className={`text-xs uppercase tracking-wide mb-1 ${isRed ? 'text-red-600' : 'text-orange-700'}`}>{titulo}</p>
      <p className={`text-xs ${isRed ? 'text-red-400' : 'text-orange-500'}`}>{subtitulo}</p>
      <span className={`mt-2 inline-block text-xs px-2.5 py-0.5 rounded-full font-semibold border ${isRed ? 'bg-red-100 text-red-800 border-red-300' : 'bg-orange-100 text-orange-800 border-orange-300'}`}>
        ⚠ Sobreposição detectada{dados.total > 1 ? ` (${dados.total})` : ''}
      </span>

      {/* Detalhes dos assentamentos/quilombolas detectados */}
      <div className={`mt-2 space-y-1 text-xs ${isRed ? 'text-red-800' : 'text-orange-800'}`}>
        {dados.nomes.length > 0 ? (
          dados.nomes.map((n, i) => (
            <p key={i} className="flex items-start gap-1">
              <span className="mt-0.5 shrink-0">•</span>
              <span>{n}</span>
            </p>
          ))
        ) : (
          <p className={`italic ${isRed ? 'text-red-500' : 'text-orange-500'}`}>
            {dados.total > 0
              ? `${dados.total} registro(s) detectado(s) — nome não informado pela fonte`
              : 'Sobreposição detectada — consulte a fonte para detalhes'}
          </p>
        )}
      </div>

      <p className={`mt-2 text-xs italic ${isRed ? 'text-red-400' : 'text-orange-500'}`}>Fonte: {dados.fonte}</p>
      {linkConsulta && (
        <LinkConsulta href={linkConsulta} label={labelConsulta ?? 'Consultar no sistema oficial'} />
      )}
    </div>
  )
}

// ─── Card Trabalho Escravo ─────────────────────────────────────────────────────

function CardTrabalhoEscravo({ dados }: { dados?: ResultadoTrabalhoEscravo }) {
  if (!dados) {
    return (
      <div className="flex items-start justify-between p-3 bg-gray-50 rounded-xl">
        <div>
          <p className="text-sm font-medium text-gray-700">Lista Suja do Trabalho Escravo</p>
          <p className="text-xs text-gray-400 mt-0.5">MTE / Portal da Transparência</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">N/A</span>
      </div>
    )
  }

  return (
    <div className="flex items-start justify-between p-3 bg-gray-50 rounded-xl">
      <div>
        <p className="text-sm font-medium text-gray-700">Lista Suja do Trabalho Escravo</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {dados.trabalho_escravo && dados.nome_encontrado
            ? `Encontrado: ${dados.nome_encontrado}`
            : 'MTE / Portal da Transparência'}
        </p>
        {!dados.verificado && (
          <p className="text-xs text-gray-400 italic mt-0.5">Fonte: {dados.fonte}</p>
        )}
      </div>
      {!dados.verificado ? (
        <span className="text-xs bg-gray-100 text-gray-500 px-2.5 py-0.5 rounded-full">Simulado</span>
      ) : dados.trabalho_escravo ? (
        <span className="text-xs bg-red-100 text-red-800 border border-red-300 px-2.5 py-0.5 rounded-full font-semibold">
          ⛔ Constante
        </span>
      ) : (
        <span className="text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
          ✓ Regular
        </span>
      )}
      {dados.verificado && dados.trabalho_escravo && (
        <LinkConsulta
          href="https://www.transparencia.gov.br/trabalho-escravo/lista-suja"
          label="Consultar Lista Suja — Portal da Transparência"
        />
      )}
    </div>
  )
}

// ─── Card Balanço RL/APP ──────────────────────────────────────────────────────

function CardBalancoAmbiental({ dados }: { dados?: ResultadoBalancoAmbiental }) {
  if (!dados) {
    return (
      <div className="flex items-start justify-between p-3 bg-gray-50 rounded-xl">
        <div>
          <p className="text-sm font-medium text-gray-700">Balanço RL/APP</p>
          <p className="text-xs text-gray-400 mt-0.5">Código Florestal — Lei 12.651/2012</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">N/A</span>
      </div>
    )
  }

  const temDeficit = dados.deficit_rl_ha > 0 || dados.deficit_app_ha > 0

  return (
    <div className={`p-3 rounded-xl ${temDeficit ? 'bg-orange-50' : 'bg-green-50'}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-700">Balanço RL/APP</p>
          <p className="text-xs text-gray-400 mt-0.5">Código Florestal — Lei 12.651/2012</p>
        </div>
        {temDeficit ? (
          <span className="text-xs bg-orange-100 text-orange-800 border border-orange-300 px-2.5 py-0.5 rounded-full font-semibold">
            ⚠ Déficit
          </span>
        ) : (
          <span className="text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
            ✓ Conforme
          </span>
        )}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-600">
        <span>RL exigida: <strong>{(dados.rl_exigida_ha ?? 0).toFixed(1)} ha</strong> ({dados.percentual_rl_exigida}%)</span>
        <span>RL existente: <strong>{(dados.rl_existente_ha ?? 0).toFixed(1)} ha</strong></span>
        {dados.deficit_rl_ha > 0 && (
          <span className="text-orange-700 col-span-2">
            Déficit RL: <strong>{(dados.deficit_rl_ha ?? 0).toFixed(1)} ha</strong>
          </span>
        )}
        {dados.deficit_app_ha > 0 && (
          <span className="text-orange-700 col-span-2">
            Déficit APP: <strong>{(dados.deficit_app_ha ?? 0).toFixed(1)} ha</strong>
          </span>
        )}
      </div>
    </div>
  )
}

// ─── Badge de conformidade para Moratória/EUDR ────────────────────────────────

function BadgeConformidade({ conforme }: { conforme: boolean | undefined }) {
  if (conforme === undefined || conforme === null) {
    return <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">N/A</span>
  }
  return conforme ? (
    <span className="text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold">
      ✓ Conforme
    </span>
  ) : (
    <span className="text-xs bg-red-100 text-red-800 border border-red-300 px-2.5 py-0.5 rounded-full font-semibold">
      ✗ Não conforme
    </span>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function ComplianceStatus({ analise, onGerarRelatorio, gerandoRelatorio }: Props) {
  const risco = analise.nivel_risco || 'ALTO'
  const config = RISCO_CONFIG[risco] || RISCO_CONFIG.ALTO
  const score = analise.score_esg ?? 0

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-800">Conformidade ESG</h2>

      {/* ── Score ESG ──────────────────────────────────────────────────────── */}
      <div className={`rounded-xl border p-4 ${config.bg}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 mb-1">Score ESG</p>
            <p className={`text-4xl font-bold ${config.cor}`}>
              {score.toFixed(0)}<span className="text-lg">/100</span>
            </p>
          </div>
          <div className="text-right">
            <span className={`text-sm font-bold uppercase ${config.cor}`}>{config.label}</span>
            <div className="mt-2 w-24 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  risco === 'BAIXO'   ? 'bg-green-500'  :
                  risco === 'MÉDIO'   ? 'bg-yellow-500' :
                  risco === 'ALTO'    ? 'bg-orange-500' : 'bg-red-600'
                }`}
                style={{ width: `${score}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Embargos Ambientais ────────────────────────────────────────────── */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
          Embargos Ambientais
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <CardEmbargo
            titulo="Embargo IBAMA"
            subtitulo="Federal — CTF/IBAMA"
            dados={analise.embargo_ibama}
            linkConsulta="https://siscom.ibama.gov.br/monitora_emb/"
            labelConsulta="Consultar embargos — SISCOM/IBAMA"
          />
          <CardEmbargo
            titulo="Embargo SEMAS"
            subtitulo="Estadual — SEMAS-PA / SIMLAM"
            dados={analise.embargo_semas}
            linkConsulta="https://monitoramento.semas.pa.gov.br/simlam/index.php"
            labelConsulta="Consultar embargos — SIMLAM/SEMAS-PA"
          />
        </div>
      </div>

      {/* ── Áreas Protegidas ───────────────────────────────────────────────── */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
          Áreas Protegidas
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <CardAreaProtegida
            titulo="Unidade de Conservação"
            subtitulo="CNUC / Ministério do Meio Ambiente"
            dados={analise.sobreposicao_uc}
            corSobreposicao="yellow"
            linkConsulta="https://dados.mma.gov.br/dataset/unidadesdeconservacao"
            labelConsulta="Consultar UCs — MMA/CNUC"
          />
          <CardAreaProtegida
            titulo="Terra Indígena"
            subtitulo="FUNAI — Terras Homologadas"
            dados={analise.sobreposicao_ti}
            corSobreposicao="red"
            linkConsulta="https://terrasindigenas.org.br/"
            labelConsulta="Consultar Terras Indígenas — ISA"
          />
        </div>
      </div>

      {/* ── Conformidade Regulatória ───────────────────────────────────────── */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
          Conformidade Regulatória
        </h3>
        <div className="space-y-2">

          {/* Desmatamento PRODES */}
          <div className={`p-3 rounded-xl ${analise.desmatamento_detectado ? 'bg-red-50' : 'bg-gray-50'}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Desmatamento (PRODES/INPE)</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {analise.desmatamento_detectado
                    ? `${(analise.area_desmatada_ha ?? 0).toFixed(2)} ha detectados — PRODES/INPE (intersecção real)`
                    : 'Nenhum detectado no período'}
                </p>
              </div>
              {analise.desmatamento_detectado ? (
                <span className="text-xs bg-red-100 text-red-800 border border-red-300 px-2.5 py-0.5 rounded-full font-semibold shrink-0 ml-2">
                  ⚠ Detectado
                </span>
              ) : (
                <span className="text-xs bg-green-100 text-green-800 border border-green-300 px-2.5 py-0.5 rounded-full font-semibold shrink-0 ml-2">
                  ✓ OK
                </span>
              )}
            </div>

            {/* Detalhamento por ano quando há desmatamento */}
            {analise.desmatamento_detectado && analise.dados_desmatamento?.registros_por_ano && analise.dados_desmatamento.registros_por_ano.length > 0 && (
              <div className="mt-3 border-t border-red-200 pt-2">
                <p className="text-xs font-semibold text-red-700 mb-1.5">
                  Detalhamento PRODES por ano de detecção:
                </p>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-red-600">
                      <th className="text-left font-semibold pb-1 pr-4">Ano</th>
                      <th className="text-right font-semibold pb-1">Área desmatada</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analise.dados_desmatamento.registros_por_ano.map((r, i) => (
                      <tr key={i} className="border-t border-red-100 text-red-800">
                        <td className="py-1 pr-4 font-medium">{r.ano}</td>
                        <td className="py-1 text-right">{r.area_ha.toFixed(2)} ha</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-red-300 text-red-900 font-bold">
                      <td className="pt-1 pr-4">Total</td>
                      <td className="pt-1 text-right">{(analise.area_desmatada_ha ?? 0).toFixed(2)} ha</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}

            {analise.desmatamento_detectado && (
              <LinkConsulta
                href="https://prodes.inpe.br/dashboard/"
                label="Consultar desmatamento — PRODES/INPE"
              />
            )}
          </div>

          {/* Moratória da Soja */}
          <div className="p-3 bg-gray-50 rounded-xl">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Moratória da Soja</p>
                <p className="text-xs text-gray-400 mt-0.5">Corte: jul/2008 — Bioma Amazônia</p>
              </div>
              <BadgeConformidade conforme={analise.moratorio_soja_conforme} />
            </div>
            {analise.moratorio_soja_conforme === false && (
              <LinkConsulta
                href="https://abiove.org.br/sustentabilidade/monitoramento-da-soja/"
                label="Consultar Moratória da Soja — ABIOVE"
              />
            )}
          </div>

          {/* EUDR */}
          <div className="p-3 bg-gray-50 rounded-xl">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">EUDR (UE 2023/1115)</p>
                <p className="text-xs text-gray-400 mt-0.5">Corte: 31/12/2020 — Exportação UE</p>
              </div>
              <BadgeConformidade conforme={analise.eudr_conforme} />
            </div>
            {analise.eudr_conforme === false && (
              <LinkConsulta
                href="https://environment.ec.europa.eu/topics/forests/deforestation/regulation-deforestation-free-products_en"
                label="Consultar regulamento EUDR — Comissão Europeia"
              />
            )}
          </div>
        </div>

        {/* Detalhe EUDR quando não conforme */}
        {analise.eudr_detalhe && !analise.eudr_conforme && (
          <div className="mt-2 text-xs p-3 rounded-lg bg-red-50 text-red-800">
            {analise.eudr_detalhe}
          </div>
        )}
      </div>

      {/* ── Conformidade Socioambiental ────────────────────────────────────── */}
      <div>
        <h3 className="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">
          Conformidade Socioambiental
        </h3>

        {/* Quilombola e Assentamento lado a lado */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <CardSobreposicao
            titulo="Território Quilombola"
            subtitulo="INCRA SIGEF — Portaria"
            dados={analise.resultado_conformidade?.quilombola}
            corSobreposicao="red"
            linkConsulta="https://certificacao.incra.gov.br/"
            labelConsulta="Consultar Quilombolas — INCRA"
          />
          <CardSobreposicao
            titulo="Assentamento Rural"
            subtitulo="INCRA SIGEF — Projetos"
            dados={analise.resultado_conformidade?.assentamento}
            corSobreposicao="orange"
            linkConsulta="https://sigef.incra.gov.br/"
            labelConsulta="Consultar Assentamentos — SIGEF/INCRA"
          />
        </div>

        {/* Trabalho Escravo e Balanço RL/APP */}
        <div className="space-y-2">
          <CardTrabalhoEscravo dados={analise.resultado_conformidade?.trabalho_escravo} />
          <CardBalancoAmbiental dados={analise.resultado_conformidade?.balanco_ambiental} />
        </div>
      </div>

      {/* ── Botão de relatório ─────────────────────────────────────────────── */}
      <button
        onClick={onGerarRelatorio}
        disabled={gerandoRelatorio}
        className="w-full py-3 bg-verde-700 hover:bg-verde-800 text-white font-semibold rounded-xl transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {gerandoRelatorio ? (
          <>
            <span className="animate-spin">⏳</span>
            Gerando relatório PDF...
          </>
        ) : (
          <>📄 Gerar Relatório PDF</>
        )}
      </button>
    </div>
  )
}

