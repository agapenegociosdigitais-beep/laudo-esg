'use client'

/**
 * Componente de mapa interativo com Leaflet.
 * Renderiza o polígono da propriedade e centraliza automaticamente.
 * Só carrega no cliente (Leaflet não funciona no SSR).
 */
import { useEffect, useRef } from 'react'
import type { GeoJSONFeatureCollection } from '@/types'

interface MapProps {
  geojson?: GeoJSONFeatureCollection | null
  altura?: string
}

export default function MapComponent({ geojson, altura = '400px' }: MapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapaInstancia = useRef<unknown>(null)
  const camadaGeojson = useRef<unknown>(null)

  useEffect(() => {
    // Importa Leaflet dinamicamente para evitar erro de SSR
    async function inicializarMapa() {
      if (!mapRef.current) return

      const L = (await import('leaflet')).default

      // Corrige ícone padrão do Leaflet no Next.js
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      // Cria o mapa se ainda não existir
      if (!mapaInstancia.current) {
        const mapa = L.map(mapRef.current, {
          center: [-15.0, -53.0],  // Centro do Brasil
          zoom: 4,
          zoomControl: true,
        })

        // Camada base OpenStreetMap (gratuito, sem token)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }).addTo(mapa)

        // Camada de satélite (opcional — também gratuita via ESRI)
        // L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        //   attribution: 'Tiles © Esri',
        // }).addTo(mapa)

        mapaInstancia.current = mapa
      }

      const mapa = mapaInstancia.current as ReturnType<typeof L.map>

      // Remove camada GeoJSON anterior
      if (camadaGeojson.current) {
        (camadaGeojson.current as ReturnType<typeof L.geoJSON>).remove()
        camadaGeojson.current = null
      }

      // Adiciona o polígono da propriedade
      if (geojson) {
        const camada = L.geoJSON(geojson as never, {
          style: {
            color: '#1b5e20',
            weight: 2.5,
            opacity: 0.9,
            fillColor: '#4caf50',
            fillOpacity: 0.25,
          },
          onEachFeature: (feature, layer) => {
            const props = feature.properties as Record<string, string>
            if (props?.numero_car) {
              layer.bindPopup(
                `<div style="font-family:sans-serif;font-size:12px">
                  <strong>CAR:</strong> ${props.numero_car}
                </div>`,
                { maxWidth: 300 }
              )
            }
          },
        }).addTo(mapa)

        camadaGeojson.current = camada

        // Centraliza e ajusta zoom para o polígono
        const bounds = camada.getBounds()
        if (bounds.isValid()) {
          mapa.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
        }
      }
    }

    inicializarMapa()
  }, [geojson])

  // Limpa o mapa quando o componente é desmontado
  useEffect(() => {
    return () => {
      if (mapaInstancia.current) {
        (mapaInstancia.current as ReturnType<import('leaflet').Map['remove']>)
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

  return (
    <div
      ref={mapRef}
      style={{ height: altura, width: '100%' }}
      className="rounded-xl overflow-hidden border border-gray-200 z-0"
    />
  )
}
