// ─── Tipos centrais da plataforma Eureka Terra ─────────────────────────────

export interface Usuario {
  id: string
  email: string
  nome: string
  empresa?: string
  perfil: 'produtor' | 'trader' | 'consultor' | 'admin'
  ativo: boolean
  criado_em: string
}

export interface TokenResposta {
  access_token: string
  token_type: string
  usuario: Usuario
}

// ─── Propriedade Rural ───────────────────────────────────────────────────────

export interface GeoJSONFeature {
  type: 'Feature'
  properties: Record<string, unknown>
  geometry: {
    type: string
    coordinates: unknown
  }
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
}

export interface Propriedade {
  id: string
  numero_car: string
  estado: string
  municipio: string
  nome_propriedade?: string
  area_ha?: number
  bioma?: string
  status_car?: string
  geojson?: GeoJSONFeatureCollection
  criado_em: string
}

/** Resultado do endpoint buscar-car — inclui o id interno para uso na análise */
export interface CARResultado {
  id: string | null
  numero_car: string
  estado: string
  municipio: string
  nome_propriedade?: string
  area_ha?: number
  status_car?: string
  bioma?: string
  geojson?: GeoJSONFeatureCollection
  fonte: string
  encontrado: boolean
}

// ─── Embargos e Áreas Protegidas ─────────────────────────────────────────────

/** Resultado da verificação de embargo (IBAMA ou SEMAS-PA). */
export interface ResultadoEmbargo {
  /** null = não verificado (API indisponível) | false = regular | true = embargado */
  embargado: boolean | null
  orgao: string
  numero_embargo?: string
  data_embargo?: string
  area_embargada_ha?: number
  motivo?: string
  fonte: string
  verificado: boolean
  /** Texto de status pronto para exibição: "Regular" | "Embargado" | "Não verificado" */
  status_display: string
}

/** Resultado da verificação de sobreposição com área protegida (UC ou TI). */
export interface ResultadoAreaProtegida {
  /** null = não verificado (API indisponível) | false = sem sobreposição | true = sobrepõe */
  sobreposicao_detectada: boolean | null
  tipo_verificacao: 'UC' | 'TI'
  nome_area?: string
  categoria?: string
  percentual_sobreposicao?: number
  area_sobreposicao_ha?: number
  esfera?: string
  fonte: string
  verificado: boolean
  motivo_nao_verificado?: string
  /** Texto de status pronto para exibição */
  status_display: string
}

// ─── Conformidade Socioambiental ─────────────────────────────────────────────

export interface ResultadoSobreposicaoSimples {
  sobreposicao: boolean
  total: number
  nomes: string[]
  verificado: boolean
  fonte: string
}

export interface ResultadoTrabalhoEscravo {
  trabalho_escravo: boolean
  nome_encontrado?: string
  verificado: boolean
  fonte: string
}

export interface ResultadoBalancoAmbiental {
  rl_exigida_ha: number
  rl_existente_ha: number
  excedente_rl_ha: number
  deficit_rl_ha: number
  app_necessaria_ha: number
  app_declarada_ha: number
  deficit_app_ha: number
  em_conformidade: boolean
  percentual_rl_exigida: number
}

export interface RegistroDesmatamentoAnual {
  ano: number | string
  area_ha: number
}

export interface DadosDesmatamento {
  total_registros: number
  bioma?: string
  metodo?: string
  registros_por_ano: RegistroDesmatamentoAnual[]
  anos_detectados?: string[]
}

export interface ResultadoMarcoUE {
  em_conformidade: boolean
  desmatamento_detectado: boolean
  registros_pos_2020: Array<{ ano: number; area_ha: number; uf: string; fonte: string }>
  total_registros: number
  area_total_ha: number
  marco_referencia: string
  regulacao: string
  verificado: boolean
  fonte: string
}

export interface ResultadoConformidade {
  quilombola?: ResultadoSobreposicaoSimples
  assentamento?: ResultadoSobreposicaoSimples
  trabalho_escravo?: ResultadoTrabalhoEscravo
  balanco_ambiental?: ResultadoBalancoAmbiental
  marco_ue?: ResultadoMarcoUE
}

// ─── Análise ESG ─────────────────────────────────────────────────────────────

export type NivelRisco = 'BAIXO' | 'MÉDIO' | 'ALTO' | 'CRÍTICO'
export type StatusAnalise = 'pendente' | 'processando' | 'concluido' | 'erro'

export interface Analise {
  id: string
  propriedade_id: string
  data_inicio: string
  data_fim: string

  // Embargos ambientais
  embargo_ibama?: ResultadoEmbargo
  embargo_semas?: ResultadoEmbargo

  // Áreas protegidas
  sobreposicao_uc?: ResultadoAreaProtegida
  sobreposicao_ti?: ResultadoAreaProtegida

  // Cobertura do solo
  cobertura_solo?: Record<string, number>

  // Desmatamento
  area_desmatada_ha?: number
  desmatamento_detectado: boolean
  dados_desmatamento?: DadosDesmatamento

  // Conformidade socioambiental (quilombola, assentamento, trabalho, RL/APP, Marco UE)
  resultado_conformidade?: ResultadoConformidade

  // Conformidade regulatória
  moratorio_soja_conforme?: boolean
  moratorio_soja_detalhe?: string
  eudr_conforme?: boolean
  eudr_detalhe?: string

  // ESG
  score_esg?: number
  nivel_risco?: NivelRisco

  // Status
  status: StatusAnalise
  erro_mensagem?: string
  criado_em: string
}

// ─── Relatório ───────────────────────────────────────────────────────────────

export interface Relatorio {
  id: string
  nome_arquivo: string
  status: string
  tamanho_bytes?: number
  criado_em: string
  url_download?: string
}

// ─── Estados da UI ───────────────────────────────────────────────────────────

export type EstadoCarregamento = 'idle' | 'carregando' | 'sucesso' | 'erro'

export interface ErroAPI {
  detail: string | { msg: string; type: string }[]
}

// ─── Painel Administrativo ───────────────────────────────────────────────

export interface UsuarioAdmin extends Usuario {
  limite_consultas: number | null
  consultas_mes_atual: number
  mes_referencia: string | null
}

export interface TopUsuario {
  nome: string
  email: string
  consultas_mes: number
}

export interface EstatisticasAdmin {
  total_usuarios: number
  usuarios_ativos: number
  total_analises: number
  analises_mes_atual: number
  cars_consultados: number
  top_usuarios: TopUsuario[]
}

export interface AnaliseAdmin {
  id: string
  numero_car: string
  nome_propriedade?: string
  usuario_email?: string
  status: string
  score_esg?: number
  nivel_risco?: string
  criado_em: string
}

export interface StatusAPI {
  online: boolean
  latencia_ms?: number
  ultima_verificacao: string
}

export interface StatusAPIsExternas {
  ibama: StatusAPI
  semas: StatusAPI
  prodes: StatusAPI
}

export interface AlertaAnalise {
  id: string
  numero_car: string
  nome_propriedade?: string
  status: string
  score_esg?: number
  nivel_risco?: string
  criado_em: string
  tem_embargo_ibama: boolean
  tem_embargo_semas: boolean
  tem_desmatamento: boolean
  area_desmatada_ha?: number
}
