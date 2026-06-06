<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-4xl mx-auto bg-white rounded-lg shadow p-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">
        {{ isEdit ? 'Editar Activo Fijo' : 'Nuevo Activo Fijo' }}
      </h1>

      <form @submit.prevent="guardarActivo" class="space-y-6">
        
        <!-- Categoría -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Categoría del Activo *</label>
          <select 
            v-model="form.categoria_id" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">-- Seleccione una categoría --</option>
            <option v-for="cat in activosStore.categorias" :key="cat.id" :value="cat.id">
              {{ cat.nombre }} (Máx. {{ cat.tasa_maxima_anual }}%)
            </option>
          </select>
          <p v-if="categoriaSeleccionada" class="mt-1 text-xs text-gray-500 italic">
            {{ categoriaSeleccionada.descripcion }}
          </p>
        </div>

        <!-- Código Interno (Automático) -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Código Interno *</label>
          <input 
            v-model="form.codigo_interno" 
            type="text" 
            readonly
            class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-600 cursor-not-allowed"
            title="Generado automáticamente según la categoría"
          />
          <p class="mt-1 text-xs text-gray-500">Se genera automáticamente al seleccionar la categoría.</p>
        </div>

        <!-- Descripción -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
          <input v-model="form.descripcion" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500" />
        </div>

        <!-- Fechas y Valores -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de Adquisición *</label>
            <input v-model="form.fecha_adquisicion" type="date" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Valor de Costo (Q) *</label>
            <input v-model.number="form.valor_costo" type="number" step="0.01" min="0" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Valor Residual (Q) *</label>
            <input v-model.number="form.valor_residual" type="number" step="0.01" min="0" required class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500" />
          </div>
        </div>

        <!-- Parámetros de Depreciación -->
        <div class="bg-indigo-50 p-4 rounded-lg border border-indigo-100">
          <h3 class="text-sm font-semibold text-indigo-800 mb-3">Parámetros de Depreciación (Art. 28 Dec. 10-2012)</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tasa de Depreciación Anual (%) *</label>
              <input 
                v-model.number="form.tasa_depreciacion_anual_aplicada" 
                type="number" 
                step="0.01" 
                min="0.01" 
                max="100"
                required 
                :class="['w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500', errorTasa ? 'border-red-500 bg-red-50' : 'border-gray-300']" 
              />
              <p v-if="errorTasa" class="mt-1 text-xs text-red-600 font-medium">⚠️ {{ errorTasa }}</p>
              <p v-else-if="categoriaSeleccionada" class="mt-1 text-xs text-green-700">
                ✅ Tasa válida. Máximo permitido: {{ categoriaSeleccionada.tasa_maxima_anual }}%
              </p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Vida Útil Estimada (Meses) *</label>
              <input 
                v-model.number="form.vida_util_meses_aplicada" 
                type="number" 
                readonly 
                class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed" 
                title="Calculado automáticamente como (100 / Tasa) * 12"
              />
              <p class="mt-1 text-xs text-gray-500">Calculado automáticamente en base a la tasa.</p>
            </div>
          </div>
        </div>

        <!-- Cuentas Contables -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Cuenta de Gasto (Débito) *</label>
            <select 
              v-model="form.cuenta_gasto_id" 
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Seleccione una cuenta --</option>
              <option v-for="cuenta in cuentasPlan" :key="cuenta.id" :value="cuenta.id">
                {{ cuenta.codigo }} - {{ cuenta.nombre }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Cuenta de Depreciación Acumulada (Crédito) *</label>
            <select 
              v-model="form.cuenta_depreciacion_acumulada_id" 
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">-- Seleccione una cuenta --</option>
              <option v-for="cuenta in cuentasPlan" :key="cuenta.id" :value="cuenta.id">
                {{ cuenta.codigo }} - {{ cuenta.nombre }}
              </option>
            </select>
          </div>
        </div>

        <!-- Botones -->
        <div class="flex justify-end gap-3 pt-4 border-t">
          <button type="button" @click="cancelar" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200">
            Cancelar
          </button>
          <button 
            type="submit" 
            :disabled="!!errorTasa || cargando" 
            class="px-6 py-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span v-if="cargando" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
            {{ isEdit ? 'Actualizar Activo' : 'Guardar Activo' }}
          </button>
        </div>

      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivosFijosStore } from '@/stores/activosFijos'
import { planCuentasService } from '@/services/planCuentasService' // ✅ Sin espacio
import { activosFijosService } from '@/services/activosFijosService'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const activosStore = useActivosFijosStore()

const isEdit = computed(() => !!route.params.id)
const cargando = ref(false)
const errorTasa = ref('')
const cuentasPlan = ref([])

const form = ref({
  categoria_id: '',
  codigo_interno: '',
  descripcion: '',
  fecha_adquisicion: '',
  valor_costo: 0,
  valor_residual: 0,
  tasa_depreciacion_anual_aplicada: null,
  vida_util_meses_aplicada: null,
  cuenta_gasto_id: '',
  cuenta_depreciacion_acumulada_id: ''
})

const categoriaSeleccionada = computed(() => 
  activosStore.categorias.find(c => c.id === form.value.categoria_id)
)

// Generar código automático
watch(() => form.value.categoria_id, async (nuevaCategoriaId) => {
  if (!nuevaCategoriaId || isEdit.value) return
  
  const empresaId = route.query.empresa_id
  try {
    const res = await api.get(`/activos-fijos/siguiente-codigo?empresa_id=${empresaId}&categoria_id=${nuevaCategoriaId}`)
    const { siguiente_numero, prefijo } = res.data
    form.value.codigo_interno = `${prefijo}-${String(siguiente_numero).padStart(4, '0')}`
  } catch (err) {
    console.warn('No se pudo generar código automático:', err.response?.data?.detail || err.message)
    form.value.codigo_interno = 'AUTO-GENERAR'
  }
})

// Validar tasa
watch(() => form.value.tasa_depreciacion_anual_aplicada, (nuevaTasa) => {
  if (!nuevaTasa || !categoriaSeleccionada.value) {
    errorTasa.value = ''
    return
  }
  const tasaMaxima = categoriaSeleccionada.value.tasa_maxima_anual
  if (nuevaTasa > tasaMaxima) {
    errorTasa.value = `La tasa no puede exceder el ${tasaMaxima}% permitido por la SAT para esta categoría.`
  } else {
    errorTasa.value = ''
    form.value.vida_util_meses_aplicada = Math.round((100 / nuevaTasa) * 12)
  }
})

onMounted(async () => {
  console.log('🔄 Cargando categorías...')
  await activosStore.fetchCategorias()
  console.log('✅ Categorías cargadas:', activosStore.categorias.length)
  
  const empresaId = route.query.empresa_id
  if (empresaId) {
    try {
      const res = await planCuentasService.getCuentas(empresaId)
      cuentasPlan.value = res.data
      console.log('✅ Plan de cuentas cargado:', cuentasPlan.value.length, 'cuentas')
    } catch (err) {
      console.error('❌ Error cargando plan de cuentas:', err)
      cuentasPlan.value = []
    }
  }

  if (isEdit.value) {
    try {
      const res = await api.get(`/activos-fijos/${route.params.id}?empresa_id=${empresaId}`)
      const activo = res.data
      form.value = {
        categoria_id: activo.categoria_id,
        codigo_interno: activo.codigo_interno,
        descripcion: activo.descripcion,
        fecha_adquisicion: activo.fecha_adquisicion,
        valor_costo: Number(activo.valor_costo),
        valor_residual: Number(activo.valor_residual),
        tasa_depreciacion_anual_aplicada: Number(activo.tasa_depreciacion_anual_aplicada),
        vida_util_meses_aplicada: activo.vida_util_meses_aplicada,
        cuenta_gasto_id: activo.cuenta_gasto_id,
        cuenta_depreciacion_acumulada_id: activo.cuenta_depreciacion_acumulada_id
      }
    } catch (err) {
      console.error('Error cargando activo:', err)
      alert('No se pudo cargar el activo')
      router.back()
    }
  }
})

// ✅ FUNCIÓN CANCELAR CORREGIDA
const cancelar = () => {
  const empresaId = route.query.empresa_id
  router.push({ 
    path: '/dashboard/activos-fijos', // ✅ Usar path absoluto
    query: { empresa_id: empresaId } 
  })
}

// ✅ FUNCIÓN GUARDAR CORREGIDA
const guardarActivo = async () => {
  console.log('🚀 [DEBUG] guardarActivo iniciado')
  console.log('📦 [DEBUG] Form data:', JSON.parse(JSON.stringify(form.value)))
  
  // Validaciones básicas
  if (!form.value.categoria_id) {
    alert('Debe seleccionar una categoría')
    return
  }
  if (!form.value.codigo_interno) {
    alert('El código interno es requerido')
    return
  }
  
  const empresaId = route.query.empresa_id
  if (!empresaId) {
    alert('Error: No se identificó la empresa.')
    return
  }

  cargando.value = true
  try {
    console.log('📡 [DEBUG] Enviando petición a backend...')
    
    let response
    // ✅ DETECTAR SI ES EDICIÓN O CREACIÓN
    if (isEdit.value && route.params.id) {
      // 🔹 MODO EDICIÓN: Llamar a actualizarActivo
      console.log('✏️ [DEBUG] Modo edición - Actualizando activo ID:', route.params.id)
      response = await activosFijosService.actualizarActivo(
        empresaId, 
        route.params.id, 
        form.value
      )
      alert('Activo actualizado exitosamente')
    } else {
      // 🔹 MODO CREACIÓN: Llamar a crearActivo
      console.log('➕ [DEBUG] Modo creación - Creando nuevo activo')
      response = await activosFijosService.crearActivo(empresaId, form.value)
      alert('Activo creado exitosamente')
    }
    
    console.log('✅ [DEBUG] Respuesta del backend:', response.data)
    
    // ✅ Navegar de vuelta al listado con path absoluto
    router.push({ 
      path: '/dashboard/activos-fijos', 
      query: { empresa_id: empresaId } 
    })
    
  } catch (err) {
    console.error('❌ [DEBUG] Error:', err)
    console.error('❌ [DEBUG] Response data:', err.response?.data)
    alert('Error: ' + (err.response?.data?.detail || 'No se pudo guardar el activo'))
  } finally {
    cargando.value = false
  }
}
</script>