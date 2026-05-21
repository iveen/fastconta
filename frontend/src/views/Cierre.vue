<template>
  <div>
    <h2 class="text-2xl font-bold mb-4">Cierre Contable</h2>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>
    <div v-if="exito" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
      {{ exito }}
    </div>

    <div class="bg-white shadow-md rounded-lg p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Empresa</label>
          <select
            v-model="empresaId"
            @change="cargarPeriodos"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Seleccionar empresa --</option>
            <option v-for="emp in empresas" :key="emp.id" :value="emp.id">
              {{ emp.nombre }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-gray-700 text-sm font-bold mb-2">Período Fiscal</label>
          <select
            v-model="periodoId"
            :disabled="!empresaId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">-- Seleccionar período --</option>
            <option v-for="per in periodosAbiertos" :key="per.id" :value="per.id">
              {{ per.nombre }} ({{ per.fecha_inicio }} - {{ per.fecha_fin }})
            </option>
          </select>
        </div>
      </div>

      <button
        @click="ejecutarCierre"
        :disabled="!empresaId || !periodoId || cargando"
        class="bg-orange-500 text-white px-6 py-2 rounded-md hover:bg-orange-600 transition disabled:opacity-50"
      >
        {{ cargando ? 'Cerrando...' : 'Ejecutar Cierre Anual' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const empresas = ref([])
const empresaId = ref('')
const periodosAbiertos = ref([])
const periodoId = ref('')
const cargando = ref(false)
const error = ref('')
const exito = ref('')

async function cargarEmpresas() {
  try {
    const resp = await api.get('/empresas/')
    empresas.value = resp.data
  } catch {
    error.value = 'Error al cargar empresas'
  }
}

async function cargarPeriodos() {
  periodosAbiertos.value = []
  periodoId.value = ''
  if (!empresaId.value) return
  try {
    const resp = await api.get('/periodos-fiscales/', { params: { empresa_id: empresaId.value } })
    periodosAbiertos.value = resp.data.filter(p => !p.cerrado)
  } catch {
    error.value = 'Error al cargar períodos'
  }
}

async function ejecutarCierre() {
  cargando.value = true
  error.value = ''
  exito.value = ''
  try {
    const resp = await api.post('/cierre/cierre-anual', null, {
      params: {
        empresa_id: empresaId.value,
        periodo_id: periodoId.value
      }
    })
    exito.value = resp.data.mensaje + '. Utilidad neta: ' + resp.data.utilidad_neta
    // Recargar períodos para deshabilitar el que se cerró
    await cargarPeriodos()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al ejecutar el cierre'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarEmpresas)
</script>