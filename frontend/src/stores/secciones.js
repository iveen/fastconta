import { defineStore } from 'pinia'
import { ref } from 'vue'
import { seccionesService } from '@/services/seccionesService'

export const useSeccionesStore = defineStore('secciones', () => {
  const loading = ref(false)

  async function crearSeccion(data) {
    loading.value = true
    try {
      const nueva = await seccionesService.crear(data)
      return { success: true, data: nueva }
    } catch (err) {
      console.error('Error al crear sección:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al crear sección' 
      }
    } finally {
      loading.value = false
    }
  }

  async function actualizarSeccion(id, data) {
    loading.value = true
    try {
      const actualizada = await seccionesService.actualizar(id, data)
      return { success: true, data: actualizada }
    } catch (err) {
      console.error('Error al actualizar sección:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al actualizar sección' 
      }
    } finally {
      loading.value = false
    }
  }

  async function eliminarSeccion(id) {
    loading.value = true
    try {
      await seccionesService.eliminar(id)
      return { success: true }
    } catch (err) {
      console.error('Error al eliminar sección:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al eliminar sección' 
      }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    crearSeccion,
    actualizarSeccion,
    eliminarSeccion,
  }
})