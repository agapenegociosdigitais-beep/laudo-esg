'use client'

/**
 * Exibe os dados da propriedade encontrada no SICAR.
 * Alerta claramente quando o CAR esta cancelado, suspenso ou indisponivel.
 */
import type { CARResultado } from '@/types'

interface Props {
  propriedade: CARResultado
}

const STATUS_CORES: Record<string, string> = {
  ATIVO:               'bg-green-100 text-green-800',
  Ativo:               'bg-green-100 text-green-800',
  PENDENTE:            'bg-yellow-100 text-yellow-800',
  Pendente:            'bg-yellow-100 text-yellow-800',
  SUSPENSO:            'bg-orange-100 text-orange-800',
  Suspenso:            'bg-orange-100 text-orange-800',
  INATIVO:             'bg-red-100 text-red-800',
  Inativo:             'bg-red-100 text-red-800',
  CANCELADO:           'bg-red-100 text-red-800',
  Cancelado:           'bg-red-100 text-red-800',
  INSCRITO:            'bg-yellow-100 text-yellow-800',
  Inscrito:            'bg-yellow-100 text-yellow-800',
  RETIFICADO:          'bg-purple-100 text-purple-800',
  Retificado:          'bg-purple-100 text-purple-800',
  'Não informado':     'bg-gray-100 text-gray-500',
  'SICAR INDISPONIVEL':'bg-gray-100 text-gray-600',
}

const STATUS_ICONE: Record<string, string> = {
  ATIVO:               '✅',
  Ativo:               '✅',
  PENDENTE:            '⏳',
  Pendente:            '⏳',
  SUSPENSO:            '⚠️',
  Suspenso:            '⚠️',
  INATIVO:             '🚫',
  Inativo:             '🚫',
  CANCELADO:           '🚫',
  Cancelado:           '🚫',
  INSCRITO:            '⏳',
  Inscrito:            '⏳',
  RETIFICADO:          '🔄',
  Retificado:          '🔄',
  'Não informado':     '❓',
  'SICAR INDISPONIVEL':'❓',
}

const STATUS_DESCRICAO: Record<string, string> = {
  ATIVO:      'CAR ativo e valido. Analise ESG realizada com dados reais.',
  Ativo:      'CAR ativo e valido. Analise ESG realizada com dados reais.',
  PENDENTE:   'CAR cadastrado mas ainda nao analisado e validado pelo orgao ambiental. Para fins de financiamento, exportacao para UE (EUDR) e certificacao, o CAR pendente tem as mesmas restricoes que o cancelado ate ser regularizado.',
  Pendente:   'CAR cadastrado mas ainda nao analisado e validado pelo orgao ambiental. Para fins de financiamento, exportacao para UE (EUDR) e certificacao, o CAR pendente tem as mesmas restricoes que o cancelado ate ser regularizado.',
  SUSPENSO:   'CAR suspenso por decisao administrativa. Analise ESG prejudicada — consulte o orgao ambiental.',
  Suspenso:   'CAR suspenso por decisao administrativa. Analise ESG prejudicada — consulte o orgao ambiental.',
  INATIVO:    'CAR inativo no sistema SICAR. Este registro nao esta mais vigente e nao pode ser utilizado para fins comerciais, legais ou de financiamento.',
  Inativo:    'CAR inativo no sistema SICAR. Este registro nao esta mais vigente e nao pode ser utilizado para fins comerciais, legais ou de financiamento.',
  CANCELADO:  'ATENCAO: Este CAR foi CANCELADO e nao representa mais uma propriedade rural valida. A analise ESG abaixo e INVALIDA para fins comerciais ou legais.',
  Cancelado:  'ATENCAO: Este CAR foi CANCELADO e nao representa mais uma propriedade rural valida. A analise ESG abaixo e INVALIDA para fins comerciais ou legais.',
  INSCRITO:   'CAR inscrito no SICAR mas ainda em processo de analise. Situacao semelhante ao Pendente — consulte o orgao ambiental estadual.',
  Inscrito:   'CAR inscrito no SICAR mas ainda em processo de analise. Situacao semelhante ao Pendente — consulte o orgao ambiental estadual.',
  RETIFICADO: 'CAR foi retificado (corrigido) pelo proprietario. Verifique a data da ultima atualizacao e confirme se a retificacao foi aceita pelo orgao ambiental.',
  Retificado: 'CAR foi retificado (corrigido) pelo proprietario. Verifique a data da ultima atualizacao e confirme se a retificacao foi aceita pelo orgao ambiental.',
  'Não informado': 'Status nao retornado pelo SICAR. Consulte car.gov.br para verificar a situacao real.',
  'SICAR INDISPONIVEL':'O SICAR nao retornou dados para este CAR no momento da consulta. Pode estar cancelado, nao cadastrado ou o sistema estar indisponivel. Verifique em car.gov.br.',
}

export default function PropertyInfo({ propriedade }: Props) {
  const status     = propriedade.status_car || 'Não informado'
  const statusCor  = STATUS_CORES[status]  || 'bg-gray-100 text-gray-600'
  const icone      = STATUS_ICONE[status]  || '❓'
  const descricao  = STATUS_DESCRICAO[status] || ''
  const cancelado  = status === 'CANCELADO' || status === 'Cancelado'
  const suspenso   = status === 'SUSPENSO'  || status === 'Suspenso'
  const inativo    = status === 'INATIVO'   || status === 'Inativo'
  const pendente   = status === 'PENDENTE'  || status === 'Pendente' || status === 'INSCRITO' || status === 'Inscrito'
  const invalido   = cancelado || inativo || status === 'SICAR INDISPONIVEL'

  return (
    <div className="space-y-3">

      {/* ALERTA VERMELHO — CAR CANCELADO */}
      {cancelado && (
        <div className="bg-red-50 border-2 border-red-500 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🚫</span>
            <div>
              <h3 className="text-lg font-bold text-red-700">CAR CANCELADO</h3>
              <p className="text-sm text-red-600 font-semibold">Este registro nao e mais valido</p>
            </div>
          </div>
          <p className="text-sm text-red-700 leading-relaxed mb-3">
            Este CAR foi <strong>cancelado oficialmente</strong> e nao representa mais uma propriedade rural valida no sistema SICAR.
            O cancelamento pode ter ocorrido por:
          </p>
          <ul className="text-sm text-red-700 space-y-1 mb-3 ml-4">
            <li>• <strong>Unificacao</strong> com imovel vizinho (novo CAR foi gerado)</li>
            <li>• <strong>Sobreposicao</strong> com area publica ou outra propriedade</li>
            <li>• <strong>Decisao administrativa</strong> do orgao ambiental</li>
            <li>• <strong>Solicitacao do proprietario</strong></li>
          </ul>
          <div className="bg-red-100 rounded-lg p-3 border border-red-300">
            <p className="text-xs font-bold text-red-800 uppercase mb-1">⚠️ Importante para o comprador/financiador:</p>
            <p className="text-xs text-red-700">
              A analise ESG exibida abaixo e <strong>INVALIDA para fins comerciais, legais ou de financiamento</strong>.
              Solicite o numero do CAR substituto ao proprietario e realize nova consulta.
            </p>
          </div>
          <div className="mt-3 flex gap-2">
            <a
              href={`https://car.gov.br/publico/imoveis/index`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-red-600 text-white px-3 py-1.5 rounded-lg hover:bg-red-700 font-semibold"
            >
              🔍 Buscar CAR substituto — car.gov.br
            </a>
            <a
              href={`https://car.semas.pa.gov.br`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-red-100 text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-200 font-semibold border border-red-300"
            >
              📋 Portal SEMAS-PA
            </a>
          </div>
        </div>
      )}

      {/* ALERTA AMARELO — CAR PENDENTE / INSCRITO */}
      {pendente && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">⏳</span>
            <h3 className="text-base font-bold text-yellow-700">CAR {status.toUpperCase()} — Analise nao concluida</h3>
          </div>
          <p className="text-sm text-yellow-800 mb-2">
            Este CAR foi cadastrado no SICAR mas <strong>ainda nao foi analisado e validado</strong> pelo orgao ambiental estadual.
          </p>
          <div className="bg-yellow-100 rounded-lg p-3 border border-yellow-300">
            <p className="text-xs text-yellow-800">
              Regularize junto ao orgao ambiental estadual antes de usar para fins comerciais ou de financiamento.
            </p>
          </div>
          <p className="text-xs text-yellow-700 mt-2">
            Regularize junto ao orgao ambiental estadual ou acesse <strong>car.gov.br</strong>.
          </p>
        </div>
      )}

      {/* ALERTA LARANJA — CAR SUSPENSO */}
      {suspenso && (
        <div className="bg-orange-50 border-2 border-orange-400 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">⚠️</span>
            <h3 className="text-base font-bold text-orange-700">CAR SUSPENSO</h3>
          </div>
          <p className="text-sm text-orange-700">
            Este CAR esta temporariamente suspenso por decisao administrativa.
            A analise ESG pode estar <strong>incompleta ou desatualizada</strong>.
            Consulte o orgao ambiental estadual para mais informacoes.
          </p>
        </div>
      )}

      {/* ALERTA VERMELHO — CAR INATIVO */}
      {inativo && (
        <div className="bg-red-50 border-2 border-red-400 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🚫</span>
            <h3 className="text-base font-bold text-red-700">CAR INATIVO</h3>
          </div>
          <p className="text-sm text-red-700 mb-2">
            Este CAR está <strong>inativo no sistema SICAR</strong> e não está mais em vigor.
          </p>
          <div className="bg-red-100 rounded-lg p-3 border border-red-300">
            <p className="text-xs font-bold text-red-800 uppercase mb-1">Implicações:</p>
            <ul className="text-xs text-red-700 space-y-1">
              <li>• <strong>Financiamento rural:</strong> bloqueado — CAR inativo não é aceito</li>
              <li>• <strong>Exportação para UE (EUDR):</strong> não atende ao requisito de due diligence</li>
              <li>• <strong>Moratória da Soja:</strong> tradings podem recusar a compra</li>
              <li>• <strong>Uso comercial/legal:</strong> análise ESG abaixo é inválida</li>
            </ul>
          </div>
          <p className="text-xs text-red-600 mt-2">
            Regularize junto ao órgão ambiental estadual ou acesse <strong>car.gov.br</strong>.
          </p>
        </div>
      )}

      {/* ALERTA CINZA — SICAR INDISPONIVEL */}
      {status === 'SICAR INDISPONIVEL' && (
        <div className="bg-gray-50 border-2 border-gray-300 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">❓</span>
            <h3 className="text-base font-bold text-gray-600">SICAR INDISPONIVEL</h3>
          </div>
          <p className="text-sm text-gray-600">
            O sistema SICAR nao retornou dados para este CAR.
            Verifique se o numero esta correto em <strong>car.gov.br</strong> antes de usar esta analise.
          </p>
        </div>
      )}

      {/* CARD PRINCIPAL DA PROPRIEDADE */}
      <div className={`bg-white rounded-2xl shadow-sm border p-6 ${invalido ? 'border-red-200 opacity-75' : 'border-gray-100'}`}>

        {invalido && (
          <div className="bg-yellow-50 border border-yellow-300 rounded-lg px-3 py-2 mb-4">
            <p className="text-xs font-bold text-yellow-700">
              ⚠️ DADOS ABAIXO COM VALIDADE COMPROMETIDA — CAR {status.toUpperCase()}
            </p>
          </div>
        )}

        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              {propriedade.nome_propriedade && propriedade.nome_propriedade !== 'NAO OBTIDO - SICAR indisponivel'
                ? propriedade.nome_propriedade
                : 'Nome nao disponivel no SICAR'}
            </h2>
            <p className="text-xs text-gray-400 font-mono mt-0.5">{propriedade.numero_car}</p>
          </div>
          <span className={`text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1 ${statusCor}`}>
            {icone} {status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            {
              label: 'Municipio / UF',
              valor: propriedade.municipio && propriedade.municipio !== 'NAO OBTIDO - SICAR indisponivel'
                ? `${propriedade.municipio} / ${propriedade.estado}`
                : 'Nao obtido'
            },
            {
              label: 'Bioma',
              valor: propriedade.bioma && propriedade.bioma !== 'NAO OBTIDO'
                ? propriedade.bioma
                : 'Nao obtido'
            },
            {
              label: 'Area Declarada',
              valor: propriedade.area_ha && propriedade.area_ha > 0
                ? `${propriedade.area_ha.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} ha`
                : 'Nao obtido'
            },
            {
              label: 'Fonte dos Dados',
              valor: propriedade.fonte || 'Nao informado'
            },
          ].map(({ label, valor }) => (
            <div key={label} className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-0.5">{label}</p>
              <p className="text-sm font-medium text-gray-800">{valor}</p>
            </div>
          ))}
        </div>

        {descricao && !cancelado && !suspenso && status !== 'SICAR INDISPONIVEL' && (
          <p className="text-xs text-gray-500 mt-3 border-t pt-3">{descricao}</p>
        )}
      </div>
    </div>
  )
}