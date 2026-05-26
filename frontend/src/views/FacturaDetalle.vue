<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <!-- Navegación -->
    <button @click="volverAlListado" class="text-gray-600 hover:text-gray-900 flex items-center gap-2 transition">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      Volver a Facturas
    </button>

    <!-- 🟡 Estado de Carga -->
    <div v-if="cargando" class="flex flex-col items-center justify-center py-16">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      <p class="mt-3 text-gray-500 font-medium">Cargando detalle de factura...</p>
    </div>

    <!-- 🔴 Estado de Error -->
    <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 rounded">
      <div class="flex">
        <div class="ml-3">
          <p class="text-sm text-red-700 font-medium">{{ error }}</p>
          <button @click="cargarFactura" class="mt-1 text-sm text-red-600 hover:text-red-800 underline">Reintentar</button>
        </div>
      </div>
    </div>

    <!-- ✅ Contenido Principal (Solo si factura existe) -->
    <div v-else-if="factura" class="space-y-6">
      
      <!-- Encabezado -->
      <div class="bg-white shadow-sm rounded-lg border p-6">
        <div class="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">
              Factura {{ factura.serie || 'S/N' }}-{{ factura.numero || '000' }}
            </h1>
            <p class="text-sm text-gray-500 mt-1 font-mono">
              Auth: {{ factura.numero_autorizacion }}
            </p>
          </div>
          
          <!-- Badges: Estado, Operación y ÁMBITO -->
          <div class="flex gap-2 flex-wrap">
            <span :class="estadoBadgeClass">{{ factura.estado || 'N/A' }}</span>
            <span :class="tipoOpBadgeClass">{{ factura.tipo_operacion || 'N/A' }}</span>
            
            <!-- 🔹 NUEVO: Badge de Ámbito -->
            <span 
              :class="factura.es_exportacion ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-700 border-gray-200'"
              class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border"
            >
              {{ factura.es_exportacion ? 'Exportación' : 'Local' }}
            </span>
          </div>
        </div>

        <!-- 🔹 Info Grid (Sin duplicados) -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div class="bg-gray-50 p-3 rounded border">
            <p class="text-xs text-gray-500 uppercase tracking-wide">Fecha Emisión</p>
            <p class="font-semibold text-gray-900">{{ formatearFecha(factura.fecha_emision) }}</p>
          </div>
          <div class="bg-gray-50 p-3 rounded border">
            <p class="text-xs text-gray-500 uppercase tracking-wide">Moneda</p>
            <p class="font-semibold text-gray-900">{{ factura.moneda || 'GTQ' }}</p>
          </div>
          <div class="bg-gray-50 p-3 rounded border">
            <p class="text-xs text-gray-500 uppercase tracking-wide">Tasa de Cambio</p>
            <p class="font-semibold text-gray-900 font-mono">
              {{ formatoTipoCambio(factura.tipo_cambio, factura.moneda) }}
            </p>
          </div>
          <div class="bg-gray-50 p-3 rounded border">
            <p class="text-xs text-gray-500 uppercase tracking-wide">Tipo Documento</p>
            <p class="font-semibold text-gray-900">{{ factura.tipo_documento || 'FACT' }}</p>
          </div>
        </div>

        <!-- 🔹 Emisor / Receptor con lógica dinámica -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pt-6 border-t">
          <div>
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              {{ factura.tipo_operacion === 'Venta' ? 'Cliente (Receptor)' : 'Proveedor (Emisor)' }}
            </h3>
            <p class="font-medium text-gray-900">
              {{ factura.tipo_operacion === 'Venta' ? factura.receptor_nombre : factura.emisor_nombre }}
            </p>
            <p class="text-sm text-gray-600 font-mono">
              NIT: {{ formatearNit(factura.tipo_operacion === 'Venta' ? factura.receptor_nit : factura.emisor_nit) }}
            </p>
          </div>
          <div>
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              {{ factura.tipo_operacion === 'Venta' ? 'Nosotros (Emisor)' : 'Nosotros (Receptor)' }}
            </h3>
            <p class="font-medium text-gray-900">
              {{ factura.tipo_operacion === 'Venta' ? factura.emisor_nombre : factura.receptor_nombre }}
            </p>
            <p class="text-sm text-gray-600 font-mono">
              NIT: {{ formatearNit(factura.tipo_operacion === 'Venta' ? factura.emisor_nit : factura.receptor_nit) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Totales -->
      <div class="bg-white shadow-sm rounded-lg border p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Desglose de Totales</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-right p-3 bg-gray-50 rounded">
            <p class="text-xs text-gray-500">Total Gravado</p>
            <p class="font-bold text-gray-900">{{ formatCurrency(factura.total_gravado) }}</p>
          </div>
          <div class="text-right p-3 bg-gray-50 rounded">
            <p class="text-xs text-gray-500">Total IVA</p>
            <p class="font-bold text-gray-900">{{ formatCurrency(factura.total_iva) }}</p>
          </div>
          <div class="text-right p-3 bg-gray-50 rounded">
            <p class="text-xs text-gray-500">Total Exento</p>
            <p class="font-bold text-gray-900">{{ formatCurrency(factura.total_exento) }}</p>
          </div>
          <div class="text-right p-3 bg-blue-50 rounded border border-blue-100">
            <p class="text-xs text-blue-600 font-semibold">Gran Total</p>
            <p class="text-xl font-bold text-blue-700">{{ formatCurrency(factura.total) }}</p>
          </div>
        </div>
      </div>

      <!-- Detalle de Líneas -->
      <div class="bg-white shadow-sm rounded-lg border overflow-hidden">
        <div class="px-6 py-4 border-b bg-gray-50">
          <h3 class="text-lg font-semibold text-gray-900">Detalle de Líneas</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Precio Unit.</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total Línea</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">IVA Línea</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="det in factura.detalles || []" :key="det.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm text-gray-900">{{ det.descripcion }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono">{{ det.cantidad }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono">{{ formatCurrency(det.precio_unitario) }}</td>
                <td class="px-4 py-3 text-sm text-right font-medium text-gray-900">{{ formatCurrency(det.total_linea) }}</td>
                <td class="px-4 py-3 text-sm text-right text-gray-500 font-mono">{{ formatCurrency(det.iva_linea) }}</td>
              </tr>
              <tr v-if="!factura.detalles?.length">
                <td colspan="5" class="px-4 py-12 text-center text-gray-500 bg-gray-50">
                  No se registraron líneas de detalle
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Acciones -->
      <div class="flex flex-wrap gap-3 justify-end pt-2">
        <button
          v-if="factura.estado === 'Activa'"
          @click="anularFactura"
          :disabled="accionCargando"
          class="px-4 py-2 bg-white border border-red-300 text-red-700 rounded-md hover:bg-red-50 disabled:opacity-50 transition font-medium"
        >
          {{ accionCargando && accionActual === 'anular' ? 'Anulando...' : 'Anular Factura' }}
        </button>
        
        <button
          v-if="factura.estado === 'Activa'"
          @click="generarPartida"
          :disabled="accionCargando"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition font-medium shadow-sm"
        >
          {{ accionCargando && accionActual === 'partida' ? 'Generando...' : 'Generar Partida Contable' }}
        </button>
        
        <router-link 
          :to="{ path: '/dashboard/facturas', query: { empresa: factura.empresa_id } }" 
          class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition font-medium"
        >
          Volver al Listado
        </router-link>
      </div>

    </div>
    <!-- ✅ Cierre del contenedor principal v-else-if="factura" -->
  </div>
  <!-- ✅ Cierre del contenedor raíz -->
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

const factura = ref(null)
const cargando = ref(true)
const error = ref('')
const accionCargando = ref(false)
const accionActual = ref('')

// 🎨 Clases dinámicas para badges
const estadoBadgeClass = computed(() => {
  const base = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide'
  if (!factura.value?.estado) return `${base} bg-gray-100 text-gray-600`
  return factura.value.estado === 'Activa'
    ? `${base} bg-green-100 text-green-700 border border-green-200`
    : `${base} bg-red-100 text-red-700 border border-red-200`
})

const tipoOpBadgeClass = computed(() => {
  const base = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide'
  if (!factura.value?.tipo_operacion) return `${base} bg-gray-100 text-gray-600`
  return factura.value.tipo_operacion === 'Venta'
    ? `${base} bg-emerald-100 text-emerald-700 border border-emerald-200`
    : `${base} bg-indigo-100 text-indigo-700 border border-indigo-200`
})

// ️ Utilidades de formato
const formatearFecha = (fecha) => {
  if (!fecha) return 'N/A'
  return fecha.includes('T') ? fecha.split('T')[0] : fecha.substring(0, 10)
}

const formatearNit = (nit) => {
  if (!nit) return 'N/A'
  const limpio = nit.replace(/[-\s]/g, '')
  return limpio.length > 1 ? `${limpio.slice(0, -1)}-${limpio.slice(-1)}` : limpio
}

const formatCurrency = (valor) => {
  if (valor === null || valor === undefined) return 'Q 0.00'
  const num = typeof valor === 'string' ? parseFloat(valor) : valor
  
  // Determinar símbolo según la moneda de la factura
  const simbolo = factura.value?.moneda === 'USD' ? '$' : 
                  factura.value?.moneda === 'GTQ' ? 'Q' : 
                  factura.value?.moneda || 'Q'
  
  return `${simbolo} ${num.toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// 🔹 Formateador de tipo de cambio (5 decimales, estándar Banco de Guatemala)
const formatoTipoCambio = (valor, moneda) => {
  if (!valor && moneda === 'GTQ') return '1.00000'
  if (!valor) return 'N/A'

  const num = typeof valor === 'string' ? parseFloat(valor) : valor
  return num.toLocaleString('es-GT', { 
    minimumFractionDigits: 5, 
    maximumFractionDigits: 5,
    useGrouping: false 
  })
}

// 📥 Carga de datos
const cargarFactura = async () => {
  cargando.value = true
  error.value = ''

  const facturaId = route.params.factura_id
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

  if (!facturaId || facturaId === 'undefined' || !uuidRegex.test(facturaId)) {
    error.value = `ID inválido: "${facturaId}"`
    cargando.value = false
    return
  }

  try {
    const resp = await api.get(`/facturas/${facturaId}`)
    factura.value = resp.data

    if (!factura.value?.id) {
      error.value = 'La factura no tiene datos válidos'
      factura.value = null
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'No se pudo cargar la factura'
  } finally {
    cargando.value = false
  }
}

// ⚡ Acciones
const anularFactura = async () => {
  if (!confirm('¿Confirmas la anulación de esta factura?')) return
  accionCargando.value = true
  accionActual.value = 'anular'
  try {
    await api.patch(`/facturas/${route.params.factura_id}/anular`)
    await cargarFactura()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al anular'
  } finally {
    accionCargando.value = false
    accionActual.value = '' 
  }
}

const volverAlListado = () => {
  router.push({ 
    path: '/dashboard/facturas', 
    query: { empresa: factura.value?.empresa_id } 
  })
}

const generarPartida = async () => {
  if (!confirm('¿Generar la partida contable automática?')) return
  accionCargando.value = true
  accionActual.value = 'partida'
  try {
    const empresaId = route.query.empresa || factura.value?.empresa_id
    await api.post(`/facturas/${route.params.factura_id}/generar-partida`, null, {
      params: { empresa_id: empresaId }
    })
    alert('✅ Partida generada exitosamente.')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al generar partida'
  } finally {
    accionCargando.value = false
    accionActual.value = ''
  }
}

onMounted(() => {
  cargarFactura()
})
</script>