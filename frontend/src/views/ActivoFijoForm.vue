<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow mt-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">Registrar Nuevo Activo Fijo</h2>
    
    <form @submit.prevent="guardarActivo" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Identificacion -->
      <div>
        <label class="block text-sm font-medium text-gray-700">Codigo Interno</label>
        <input v-model="form.codigo_interno" type="text" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" placeholder="Ej: VEH-001">
      </div>
      
      <div class="md:col-span-2">
        <label class="block text-sm font-medium text-gray-700">Descripcion</label>
        <input v-model="form.descripcion" type="text" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" placeholder="Ej: Toyota Hilux 2023">
      </div>

      <!-- Fechas y Valores -->
      <div>
        <label class="block text-sm font-medium text-gray-700">Fecha de Adquisicion</label>
        <input v-model="form.fecha_adquisicion" type="date" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Valor de Costo (Q)</label>
        <input v-model.number="form.valor_costo" type="number" step="0.01" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Valor Residual (Q)</label>
        <input v-model.number="form.valor_residual" type="number" step="0.01" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border" placeholder="0.00">
        <p class="text-xs text-gray-500 mt-1">Valor de desecho estimado (puede ser 0)</p>
      </div>

      <!-- Configuracion Depreciacion (La parte inteligente) -->
      <div>
        <label class="block text-sm font-medium text-gray-700">Categoria (Limites SAT)</label>
        <select v-model="form.categoria_id" @change="aplicarDefaultsCategoria" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
          <option value="">Seleccione una categoria...</option>
          <option v-for="cat in store.categorias" :key="cat.id" :value="cat.id">
            {{ cat.nombre }} (Max: {{ cat.tasa_maxima_anual }}%)
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">
          Tasa Depreciacion Anual (%)
          <span v-if="tasaExcedeLimite" class="text-red-600 text-xs ml-2">⚠️ Excede el limite de la SAT</span>
        </label>
        <input 
          v-model.number="form.tasa_depreciacion_anual_aplicada" 
          type="number" 
          step="0.01" 
          required 
          :class="{'border-red-500 focus:ring-red-500 focus:border-red-500': tasaExcedeLimite}"
          class="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2 border"
        >
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Vida Util (Meses)</label>
        <input v-model.number="form.vida_util_meses_aplicada" type="number" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border">
      </div>

      <!-- Cuentas Contables (Simplificado para el ejemplo) -->
      <div class="md:col-span-2 border-t pt-4 mt-2">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Asignacion Contable</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700">Cuenta de Gasto</label>
            <input v-model="form.cuenta_gasto_id" type="text" placeholder="ID o buscar cuenta..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">Cuenta Depreciacion Acumulada</label>
            <input v-model="form.cuenta_depreciacion_acumulada_id" type="text" placeholder="ID o buscar cuenta..." class="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
          </div>
        </div>
      </div>

      <!-- Botones -->
      <div class="md:col-span-2 flex justify-end gap-3 mt-6">
        <button type="button" @click="$router.back()" class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">Cancelar</button>
        <button 
        type="submit" 
        :disabled="store.loading || tasaExcedeLimite || !formValido" 
        class="px-4 py-2 bg-indigo-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
        {{ store.loading ? 'Guardando...' : 'Guardar Activo' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActivosFijosStore } from '@/stores/activosFijos'
import { activosFijosService } from '@/services/activosFijosService'

const route = useRoute()
const router = useRouter()
const store = useActivosFijosStore()

// Obtener el empresa_id de la URL (query)
const empresaId = route.query.empresa_id

const form = reactive({
  codigo_interno: '',
  descripcion: '',
  fecha_adquisicion: '',
  valor_costo: null,
  valor_residual: 0,
  categoria_id: '',
  tasa_depreciacion_anual_aplicada: null,
  vida_util_meses_aplicada: null,
  cuenta_gasto_id: '',
  cuenta_depreciacion_acumulada_id: ''
})

onMounted(() => {
  store.fetchCategorias()
  if (!empresaId) {
    alert("No se especifico una empresa. Redirigiendo...")
    router.push('/dashboard/activos-fijos')
  }
})

const aplicarDefaultsCategoria = () => {
  const categoriaSeleccionada = store.categorias.find(c => c.id === form.categoria_id)
  if (categoriaSeleccionada) {
    // Sugerir el maximo permitido por la SAT, el usuario puede bajarlo si quiere
    form.tasa_depreciacion_anual_aplicada = categoriaSeleccionada.tasa_maxima_anual
    form.vida_util_meses_aplicada = categoriaSeleccionada.vida_util_meses_default
  }
}

// ✅ CORRECCION CLAVE: Solo evalua si ya hay categoria y tasa seleccionadas
const tasaExcedeLimite = computed(() => {
  if (!form.categoria_id || form.tasa_depreciacion_anual_aplicada === null || form.tasa_depreciacion_anual_aplicada === '') {
    return false // No bloquear si aun no se ha configurado
  }
  const categoria = store.categorias.find(c => c.id === form.categoria_id)
  if (!categoria) return false
  
  return form.tasa_depreciacion_anual_aplicada > categoria.tasa_maxima_anual
})

// ✅ Validacion basica para habilitar el boton solo si los campos obligatorios tienen datos
const formValido = computed(() => {
  return form.codigo_interno && 
         form.descripcion && 
         form.fecha_adquisicion && 
         form.valor_costo > 0 && 
         form.categoria_id &&
         form.cuenta_gasto_id &&
         form.cuenta_depreciacion_acumulada_id
})

const guardarActivo = async () => {
  if (tasaExcedeLimite.value) {
    alert("La tasa de depreciacion no puede exceder el limite maximo permitido por la SAT para esta categoria.")
    return
  }

  try {
    await activosFijosService.crearActivo(empresaId, form)
    router.push('/dashboard/activos-fijos') 
  } catch (error) {
    console.error(error)
    alert(error.response?.data?.detail || 'Error al guardar el activo')
  }
}
</script>