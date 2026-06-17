<template>
  <div class="space-y-6">
    <!-- Resumen Superior -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex justify-between items-center mb-4">
        <div>
          <h2 class="text-xl font-bold text-gray-800">{{ declaracionActual.formulario_codigo }}</h2>
          <p class="text-sm text-gray-600">
            Período: {{ nombresMeses[declaracionActual.mes - 1] }} {{ declaracionActual.anio }}
            <span :class="badgeClass" class="ml-2 px-3 py-1 rounded-full text-xs font-semibold">
              {{ declaracionActual.estado }}
            </span>
          </p>
        </div>
        <div class="flex gap-2">
          <button
            v-if="declaracionActual.estado !== 'FINALIZADO'"
            @click="$emit('recargar')"
            class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            🔄 Recalcular
          </button>
          <button
            v-if="declaracionActual.estado !== 'FINALIZADO'"
            @click="finalizarDeclaracion"
            class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            ✓ Finalizar
          </button>
        </div>
      </div>
      
      <!-- KPIs -->
      <div class="grid grid-cols-4 gap-4 mt-6">
        <KpiCard label="Débito Fiscal" :valor="declaracionActual.total_debito_fiscal" color="red" />
        <KpiCard label="Crédito Fiscal" :valor="declaracionActual.total_credito_fiscal" color="blue" />
        <KpiCard label="Remanente Sig. Período" :valor="declaracionActual.remanente_siguiente_periodo" color="yellow" />
        <KpiCard label="Impuesto a Pagar" :valor="declaracionActual.impuesto_a_pagar" color="green" highlight />
      </div>
    </div>

    <!-- Secciones del Formulario -->
    <SeccionFormulario
      v-for="seccion in seccionesVisibles"
      :key="seccion.codigo"
      :titulo="seccion.titulo"
      :descripcion="seccion.descripcion"
      :casillas="casillasPorSeccion(seccion.codigo)"
      :estado="declaracionActual.estado"
      :tipo-seccion="seccion.tipo"
      @ver-facturas="abrirDrillDown"
      @ajustar="abrirAjuste"
    />

    <!-- Modales -->
    <ModalDrillDown
      v-if="drillDownCasilla"
      :declaracion-id="declaracionActual.id"
      :casilla-codigo="drillDownCasilla"
      @close="drillDownCasilla = null"
    />
    <AjusteManual
      v-if="ajusteCasilla"
      :declaracion-id="declaracionActual.id"
      :casilla="ajusteCasilla"
      @close="ajusteCasilla = null"
      @guardado="$emit('recargar')"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useDeclaraciones } from '@/composables/useDeclaraciones'
import SeccionFormulario from './SeccionFormulario.vue'
import ModalDrillDown from './ModalDrillDown.vue'
import AjusteManual from './AjusteManual.vue'
import KpiCard from './KpiCard.vue'

const { declaracionActual, finalizar, casillasPorSeccion } = useDeclaraciones()
const emit = defineEmits(['recargar'])

const nombresMeses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

// 🔹 CORREGIDO: Incluye TODAS las secciones del SAT-2237
const secciones = [
  { 
    codigo: '3', 
    titulo: '3. DÉBITO FISCAL POR OPERACIONES LOCALES', 
    descripcion: 'Ventas y servicios gravados del período',
    tipo: 'CALCULO'
  },
  { 
    codigo: '4', 
    titulo: '4. OPERACIONES DE EXPORTACIÓN Y TRANSFERENCIA', 
    descripcion: 'Exportaciones y transferencias (no generan IVA)',
    tipo: 'REFERENCIA'
  },
  { 
    codigo: '5', 
    titulo: '5. CRÉDITO FISCAL POR OPERACIONES LOCALES', 
    descripcion: 'Compras y servicios que generan crédito fiscal',
    tipo: 'CALCULO'
  },
  { 
    codigo: '6', 
    titulo: '6. DETERMINACIÓN DEL IMPUESTO', 
    descripcion: 'Cálculo final del impuesto a pagar o remanente',
    tipo: 'CALCULADO'
  },
  { 
    codigo: '7', 
    titulo: '7. RETENCIONES DE IVA', 
    descripcion: 'Retenciones de IVA practicadas en el período',
    tipo: 'RETENCION'
  },
  { 
    codigo: '8', 
    titulo: '8. INDICADORES COMERCIALES', 
    descripcion: 'Indicadores Comerciales',
    tipo: 'INDICADOR'
  },
  { codigo: '9.1', titulo: '9.1 CANTIDAD DE OPERACIONES REALIZADAS', descripcion: 'Conteo de documentos emitidos y recibidos', tipo: 'INDICADOR' },
  { codigo: '9.2', titulo: '9.2 MONTO DE OPERACIONES REALIZADAS', descripcion: 'Valor de notas de crédito y débito', tipo: 'INDICADOR' },
]

// Filtrar secciones que tienen datos
const seccionesVisibles = computed(() => {
  return secciones.filter(seccion => {
    const casillas = casillasPorSeccion(seccion.codigo)
    if (['CALCULADO', 'INDICADOR'].includes(seccion.tipo)) return true
    if (seccion.codigo === '6') return true  // Siempre mostrar sección 6
    
    return casillas.some(c => 
      Number(c.base_imponible || 0) > 0 || 
      Number(c.monto_impuesto || 0) > 0
    )
  })
})

const badgeClass = computed(() => ({
  'bg-yellow-100 text-yellow-800': declaracionActual.value?.estado === 'BORRADOR',
  'bg-blue-100 text-blue-800': declaracionActual.value?.estado === 'REVISION',
  'bg-green-100 text-green-800': declaracionActual.value?.estado === 'FINALIZADO',
}))

const drillDownCasilla = ref(null)
const ajusteCasilla = ref(null)

const abrirDrillDown = (codigo) => drillDownCasilla.value = codigo
const abrirAjuste = (casilla) => ajusteCasilla.value = casilla

const finalizarDeclaracion = async () => {
  if (!confirm('¿Finalizar la declaración? No podrás modificar los valores.')) return
  await finalizar()
  emit('recargar')
}
</script>