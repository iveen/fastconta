<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <!-- Header -->
    <div class="mb-6 flex justify-between items-start">
      <div>
        <h1 class="text-3xl font-bold text-gray-800">Declaraciones SAT</h1>
        <p class="text-gray-600 mt-1">Formularios sombra para revisión previa al envío</p>
      </div>
      <div class="flex gap-3 flex-wrap">
        <!-- Selector de Empresa -->
        <select v-model="selectedEmpresa" class="px-4 py-2 border rounded-lg bg-white">
          <option value="">Seleccionar empresa...</option>
          <option v-for="emp in empresas" :key="emp.id" :value="emp.id">{{ emp.nombre }}</option>
        </select>
        
        <!-- ✅ Selector de Formulario (Preparado para Strategy Pattern) -->
        <select v-model="selectedFormulario" class="px-4 py-2 border rounded-lg bg-white">
          <option value="SAT-2237">SAT-2237 (IVA General)</option>
          <!-- Futuros: SAT-2027, SAT-1010, etc. -->
        </select>

        <!-- Selector de Mes -->
        <select v-model="selectedMes" class="px-4 py-2 border rounded-lg bg-white">
          <option v-for="m in 12" :key="m" :value="m">{{ nombresMeses[m-1] }}</option>
        </select>
        
        <!-- ✅ Input de Año con validación min/max -->
        <input 
          v-model.number="selectedAnio" 
          type="number" 
          min="2020" 
          max="2030" 
          class="px-4 py-2 border rounded-lg w-24 bg-white" 
        />
        
        <button
          @click="generarSombra"
          :disabled="!selectedEmpresa || cargando"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {{ cargando ? 'Generando...' : 'Generar Sombra' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-4 flex items-center gap-2">
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      {{ error }}
    </div>

    <!-- Formulario Sombra -->
    <FormularioSombra
      v-if="declaracionActual"
      @recargar="recargar"
    />

    <!-- Empty state -->
    <div v-else-if="!cargando" class="bg-white rounded-lg shadow p-12 text-center">
      <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900">Selecciona empresa, formulario y período</h3>
      <p class="mt-2 text-gray-500">Luego haz clic en "Generar Sombra" para calcular el formulario.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDeclaraciones } from '@/composables/useDeclaraciones'
import FormularioSombra from '@/components/declaraciones/FormularioSombra.vue'
import { empresasApi } from '@/services/empresas'

const { declaracionActual, cargando, error, generarSombra: generarSombraComposable, recargar } = useDeclaraciones()

const empresas = ref([])
const selectedEmpresa = ref('')
const selectedFormulario = ref('SAT-2237') // ✅ Nuevo: selector de formulario
const selectedMes = ref(new Date().getMonth() + 1)
const selectedAnio = ref(new Date().getFullYear())
const nombresMeses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const generarSombra = async () => {
  // ✅ Validación explícita de empresa
  if (!selectedEmpresa.value) {
    error.value = 'Por favor, selecciona una empresa antes de generar la declaración.'
    return
  }
  
  // ✅ Pasar el código del formulario seleccionado al composable
  await generarSombraComposable(
    selectedEmpresa.value, 
    selectedAnio.value, 
    selectedMes.value, 
    selectedFormulario.value
  )
}

onMounted(async () => {
  try {
    const data = await empresasApi.listar()
    empresas.value = data
  } catch (e) {
    console.error('Error cargando empresas:', e)
    error.value = 'Error al cargar el listado de empresas. Verifica tu conexión.'
  }
})
</script>