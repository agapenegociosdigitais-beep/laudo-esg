/**
 * Serviço de autenticação — gerencia token JWT via cookies e estado global.
 */
import Cookies from 'js-cookie'

import type { Usuario } from '@/types'

const COOKIE_TOKEN = 'token'
const COOKIE_USUARIO = 'usuario'
const COOKIE_EXPIRACAO_DIAS = 1  // 24h

export const authStorage = {
  salvarSessao(token: string, usuario: Usuario): void {
    Cookies.set(COOKIE_TOKEN, token, { expires: COOKIE_EXPIRACAO_DIAS, sameSite: 'strict' })
    Cookies.set(COOKIE_USUARIO, JSON.stringify(usuario), {
      expires: COOKIE_EXPIRACAO_DIAS,
      sameSite: 'strict',
    })
  },

  limparSessao(): void {
    Cookies.remove(COOKIE_TOKEN)
    Cookies.remove(COOKIE_USUARIO)
  },

  obterToken(): string | undefined {
    return Cookies.get(COOKIE_TOKEN)
  },

  obterUsuario(): Usuario | null {
    const raw = Cookies.get(COOKIE_USUARIO)
    if (!raw) return null
    try {
      return JSON.parse(raw) as Usuario
    } catch {
      return null
    }
  },

  estaAutenticado(): boolean {
    return !!Cookies.get(COOKIE_TOKEN)
  },
}
