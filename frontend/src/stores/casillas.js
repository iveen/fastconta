import { defineStore } from 'pinia'
import { ref } from 'vue'
import { casillasService } from '@/services/casillasService'

export const useCasillasStore = defineStore('casillas', () => {
  const loading = ref(false)

  async function crearCasilla(data) {
    loading.value = true
    try {
      const nueva = await casillasService.crear(data)
      return { success: true, data: nueva }
    } catch (err) {
      console.error('Error al crear casilla:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al crear casilla' 
      }
    } finally {
      loading.value = false
    }
  }

  async function actualizarCasilla(id, data) {
    loading.value = true
    try {
      const actualizada = await casillasService.actualizar(id, data)
      return { success: true, data: actualizada }
    } catch (err) {
      console.error('Error al actualizar casilla:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al actualizar casilla' 
      }
    } finally {
      loading.value = false
    }
  }

  async function eliminarCasilla(id) {
    loading.value = true
    try {
      await casillasService.eliminar(id)
      return { success: true }
    } catch (err) {
      console.error('Error al eliminar casilla:', err)
      return { 
        success: false, 
        error: err.response?.data?.detail || 'Error al eliminar casilla' 
      }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    crearCasilla,
    actualizarCasilla,
    eliminarCasilla,
  }
})