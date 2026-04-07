'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { authService } from '@/services/api'
import { authStorage } from '@/services/auth'

const PERFIS = [
  { value: 'produtor', label: 'Produtor Rural' },
  { value: 'trader', label: 'Trader / Exportador' },
  { value: 'consultor', label: 'Consultor Ambiental' },
]

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    nome: '',
    email: '',
    senha: '',
    empresa: '',
    perfil: 'consultor',
  })
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [carregando, setCarregando] = useState(false)

  function atualizar(campo: string, valor: string) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro('')
    setSucesso('')

    if (form.senha.length < 8) {
      setErro('A senha deve ter no mínimo 8 caracteres.')
      return
    }

    setCarregando(true)
    try {
      const resposta = await authService.registrar(form)
      setSucesso(resposta.mensagem)

      // Redireciona para login após 2 segundos
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } catch (err: unknown) {
      setErro(err instanceof Error ? err.message : 'Erro ao criar conta.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-verde-900 to-verde-700 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-2">
            <span className="text-3xl">🌱</span>
            <span className="text-verde-800 text-xl font-bold">Eureka Terra</span>
          </Link>
          <p className="text-gray-500 text-sm">Crie sua conta gratuita</p>
        </div>

        {erro && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
            {erro}
          </div>
        )}

        {sucesso && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg">
            ✅ {sucesso}
            <p className="text-xs mt-2">Redirecionando para login em breve...</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome completo</label>
            <input
              type="text"
              value={form.nome}
              onChange={(e) => atualizar('nome', e.target.value)}
              placeholder="João da Silva"
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-verde-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">E-mail</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => atualizar('email', e.target.value)}
              placeholder="seu@email.com.br"
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-verde-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Senha</label>
            <input
              type="password"
              value={form.senha}
              onChange={(e) => atualizar('senha', e.target.value)}
              placeholder="Mínimo 8 caracteres"
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-verde-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Empresa (opcional)</label>
            <input
              type="text"
              value={form.empresa}
              onChange={(e) => atualizar('empresa', e.target.value)}
              placeholder="Nome da empresa"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-verde-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Perfil</label>
            <select
              value={form.perfil}
              onChange={(e) => atualizar('perfil', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-verde-500 bg-white"
            >
              {PERFIS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={carregando}
            className="w-full py-3 bg-verde-700 hover:bg-verde-800 text-white font-semibold rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {carregando ? 'Criando conta...' : 'Criar conta'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Já tem conta?{' '}
          <Link href="/login" className="text-verde-700 font-semibold hover:underline">
            Entrar
          </Link>
        </p>
      </div>
    </main>
  )
}
