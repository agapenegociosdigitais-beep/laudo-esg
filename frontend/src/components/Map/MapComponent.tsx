'use client'

import { useEffect, useRef, useState } from 'react'
import type { GeoJSONFeatureCollection } from '@/types'

interface OverlayFeatureCollection extends GeoJSONFeatureCollection {
  features: Array<{
    type: 'Feature'
    geometry: Record<string, unknown>
    properties: Record<string, string | number | null>
  }>
}

interface MapProps {
  geojson?: GeoJSONFeatureCollection | null
  overlays?: OverlayFeatureCollection | null
  altura?: string
}

export default function MapComponent({ geojson, overlays, altura = '400px' }: MapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapaInstancia = useRef<unknown>(null)
  const camadaGeojson = useRef<unknown>(null)
  const camadasOverlay = useRef<unknown[]>([])
  const [satelite, setSatelite] = useState(false)

  useEffect(() => {
    async function inicializarMapa() {
      if (!mapRef.current) return

      const L = (await import('leaflet')).default
      await import('leaflet/dist/leaflet.css')

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      if (!mapaInstancia.current) {
        const mapa = L.map(mapRef.current, {
          center: [-15.0, -53.0],
          zoom: 4,
          zoomControl: true,
        })

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 19,
        }).addTo(mapa)

        mapaInstancia.current = mapa
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const mapa = mapaInstancia.current as any

      // Remove camada GeoJSON anterior
      if (camadaGeojson.current) {
        (camadaGeojson.current as ReturnType<typeof L.geoJSON>).remove()
        camadaGeojson.current = null
      }

      // Remove overlays anteriores
      for (const camada of camadasOverlay.current) {
        camada.remove()
      }
      camadasOverlay.current = []

      // Adiciona poligono da propriedade
      if (geojson) {
        const camada = L.geoJSON(geojson as never, {
          style: {
            color: '#1b5e20',
            weight: 3,
            opacity: 1,
            fillColor: '#4caf50',
            fillOpacity: 0.15,
          },
          onEachFeature: (feature, layer) => {
            const props = feature.properties as Record<string, string>
            if (props?.numero_car) {
              layer.bindPopup(
                `<div style="font-family:sans-serif;font-size:12px;max-width:280px">
                  <strong>CAR:</strong> ${props.numero_car}
                </div>`,
                { maxWidth: 300 }
              )
            }
          },
        }).addTo(mapa)

        camadaGeojson.current = camada

        const bounds = camada.getBounds()
        if (bounds.isValid()) {
          mapa.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
        }
      }

      // Adiciona overlays (embargos, PRODES, UC, TI, etc.)
      if (overlays?.features?.length) {
        for (const feature of overlays.features) {
          const props = feature.properties
          const tipo = (props.tipo as string) || 'outro'
          const cor = (props.cor as string) || '#888888'
          const areaHa = parseFloat((props.area_intersecao_ha as string) || '0')
          const year = (props.year as string) || ''

          // Cores por ano para PRODES
          const YEAR_COLORS: Record<string, string> = {
            '2008': '#fee08b', '2009': '#fdae61', '2010': '#f46d43',
            '2011': '#d73027', '2012': '#a50026', '2013': '#d53e4f',
            '2014': '#f46d43', '2015': '#fdae61', '2016': '#fee08b',
            '2017': '#e6f598', '2018': '#abdda4', '2019': '#66c2a5',
            '2020': '#3288bd', '2021': '#d73027', '2022': '#a50026',
            '2023': '#d53e4f', '2024': '#f46d43', '2025': '#a50026',
          }

          const prodesCor = tipo === 'prodes' && year ? (YEAR_COLORS[year] || cor) : cor

          const style = {
            embargos: { color: prodesCor, weight: 2, opacity: 0.9, fillColor: prodesCor, fillOpacity: 0.3 },
            prodes: { color: prodesCor, weight: 2, opacity: 0.85, fillColor: prodesCor, fillOpacity: 0.35 },
            uc: { color: prodesCor, weight: 2, opacity: 0.8, fillColor: prodesCor, fillOpacity: 0.15 },
            ti: { color: prodesCor, weight: 2, opacity: 0.8, fillColor: prodesCor, fillOpacity: 0.2 },
            assentamentos: { color: prodesCor, weight: 2, opacity: 0.8, fillColor: prodesCor, fillOpacity: 0.2 },
            quilombolas: { color: prodesCor, weight: 2, opacity: 0.8, fillColor: prodesCor, fillOpacity: 0.25 },
          }[tipo] || { color: prodesCor, weight: 2, opacity: 0.7, fillColor: prodesCor, fillOpacity: 0.2 }

          const popupLines: string[] = [`<strong>${tipo.toUpperCase()}</strong>`]
          if (props.num_tad) popupLines.push(`TAD: ${props.num_tad}`)
          if (props.orgao) popupLines.push(`Orgao: ${props.orgao}`)
          if (props.year) popupLines.push(`Ano: ${props.year}`)
          if (props.nome_uc) popupLines.push(`UC: ${props.nome_uc}`)
          if (props.nome_ti) popupLines.push(`TI: ${props.nome_ti}`)
          if (props.nome) popupLines.push(`Nome: ${props.nome}`)
          if (areaHa > 0) popupLines.push(`Area: ${areaHa.toFixed(1)} ha`)

          try {
            const camada = L.geoJSON(feature.geometry as never, {
              style,
              onEachFeature: (_f, layer) => {
                layer.bindPopup(
                  `<div style="font-family:sans-serif;font-size:11px;max-width:280px;line-height:1.4">
                    ${popupLines.join('<br>')}
                  </div>`,
                  { maxWidth: 300 }
                )
                // Label permanente com o ano para PRODES
                if (tipo === 'prodes' && year) {
                  layer.bindTooltip(`<b>${year}</b>`, {
                    permanent: true,
                    direction: 'center',
                    className: 'prodes-year-label',
                    opacity: 0.9,
                  })
                }
              },
            }).addTo(mapa)

            camadasOverlay.current.push(camada)
          } catch {
            // Geometria invalida — ignora
          }
        }
      }
    }

    inicializarMapa()
  }, [geojson, overlays])

  useEffect(() => {
    return () => {
      if (mapaInstancia.current) {
        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ;(mapaInstancia.current as any).remove()
        } catch {
          // Ignora erros de cleanup
        }
        mapaInstancia.current = null
      }
    }
  }, [])

  // Efeito para alternar camada satelite
  useEffect(() => {
    if (!mapaInstancia.current) return
    const L = (window as unknown as Record<string, Record<string, unknown>>)?.L
    if (!L) return
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const mapa = mapaInstancia.current as any

    if (satelite) {
      const sat = (L as unknown as Record<string, Record<string, unknown>>).tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles © Esri', maxZoom: 19 }
      )
      sat.addTo(mapa)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(mapa as any)._satLayer = sat
    } else {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const sat = (mapa as any)._satLayer
      if (sat) {
        sat.remove()
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(mapa as any)._satLayer = null
      }
    }
  }, [satelite])

  const labels = [
    { cor: '#ef4444', nome: 'Embargos' },
    { cor: '#a50026', nome: 'PRODES 21+' },
    { cor: '#fee08b', nome: 'PRODES 08-16' },
    { cor: '#3288bd', nome: 'PRODES 17-20' },
    { cor: '#22c55e', nome: 'UC' },
    { cor: '#a855f7', nome: 'T.I.' },
    { cor: '#eab308', nome: 'Assent.' },
    { cor: '#ec4899', nome: 'Quilom.' },
  ]

  return (
    <div className="relative">
      <div
        ref={mapRef}
        style={{ height: altura, width: '100%' }}
        className="rounded-xl overflow-hidden border border-gray-200 z-0"
      />
      {/* Controles */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1">
        <button
          onClick={() => setSatelite(!satelite)}
          className={`text-xs font-medium px-2.5 py-1.5 rounded-lg shadow-md transition-colors ${
            satelite ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
          }`}
        >
          🛰 Satélite
        </button>
      </div>
      {/* Legenda */}
      {overlays?.features?.length ? (
        <div className="absolute bottom-3 left-3 z-[1000] bg-white/90 backdrop-blur rounded-lg shadow-md px-3 py-2 border border-gray-200">
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {labels.map(({ cor, nome }) => (
              <div key={nome} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: cor, opacity: 0.6 }} />
                <span className="text-xs text-gray-600">{nome}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
