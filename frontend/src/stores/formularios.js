// src/stores/formularios.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { formulariosService } from '@/services/formulariosService'

export const useFormulariosStore = defineStore('formularios', () => {
  const formularios = ref([])
  const formularioActual = ref(null)
  const historial = ref(null)
  const loading = ref(false)
  const total = ref(0)

  const formulariosActivos = computed(() => 
    formularios.value.filter(f => f.es_version_activa)
  )

  async function fetchFormularios(params = {}) {
    loading.value = true
    try {
      const data = await formulariosService.listar(params)
      formularios.value = data.data
      total.value = data.total
      return { success: true }
    } catch (err) {
      console.error('Error al cargar formularios:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al cargar formularios' 
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchFormularioDetail(id) {
    loading.value = true
    try {
      formularioActual.value = await formulariosService.obtenerPorId(id)
      return { success: true }
    } catch (err) {
      console.error('Error al cargar detalle:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al cargar detalle' 
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchHistorial(codigo) {
    loading.value = true
    try {
      historial.value = await formulariosService.obtenerHistorial(codigo)
      return { success: true }
    } catch (err) {
      console.error('Error al cargar historial:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al cargar historial' 
      }
    } finally {
      loading.value = false
    }
  }

  async function crearFormulario(data) {
    loading.value = true
    try {
      const nuevo = await formulariosService.crear(data)
      await fetchFormularios()
      return { success: true, data: nuevo }
    } catch (err) {
      console.error('Error al crear:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al crear formulario' 
      }
    } finally {
      loading.value = false
    }
  }

  async function actualizarFormulario(id, data) {
    loading.value = true
    try {
      const actualizado = await formulariosService.actualizar(id, data)
      await fetchFormularios()
      if (formularioActual.value?.id === id) {
        formularioActual.value = { ...formularioActual.value, ...actualizado }
      }
      return { success: true, data: actualizado }
    } catch (err) {
      console.error('Error al actualizar:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al actualizar formulario' 
      }
    } finally {
      loading.value = false
    }
  }

  async function duplicarFormulario(id, data) {
    loading.value = true
    try {
      const duplicado = await formulariosService.duplicar(id, data)
      await fetchFormularios()
      return { success: true, data: duplicado }
    } catch (err) {
      console.error('Error al duplicar:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al duplicar formulario' 
      }
    } finally {
      loading.value = false
    }
  }

  async function eliminarFormulario(id) {
    loading.value = true
    try {
      await formulariosService.eliminar(id)
      await fetchFormularios()
      if (formularioActual.value?.id === id) {
        formularioActual.value = null
      }
      return { success: true }
    } catch (err) {
      console.error('Error al eliminar:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al eliminar formulario' 
      }
    } finally {
      loading.value = false
    }
  }

  function clearFormularioActual() {
    formularioActual.value = null
  }

  function clearHistorial() {
    historial.value = null
  }

  async function fetchFormularioDetail(id) {
    loading.value = true
    try {
        const data = await formulariosService.obtenerPorId(id)

        formularioActual.value = data

        return { success: true, data }
    } catch (err) {
        console.error('Error al cargar detalle:', err)
        return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al cargar detalle del formulario' 
        }
    } finally {
        loading.value = false
    }
  }

  return {
    formularios,
    formularioActual,
    historial,
    loading,
    total,
    formulariosActivos,
    fetchFormularios,
    fetchFormularioDetail,
    fetchHistorial,
    crearFormulario,
    actualizarFormulario,
    duplicarFormulario,
    eliminarFormulario,
    clearFormularioActual,
    clearHistorial,
    fetchFormularioDetail,
  }
})