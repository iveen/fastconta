import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { inventarioService } from '@/services/inventarioService'
import { useToast } from '@/composables/useToast' // Ajusta a tu sistema de notificaciones

export const useInventarioStore = defineStore('inventario', () => {
  const tomaActual = ref(null)
  const items = ref([])
  const isLoading = ref(false)
  const jobActivo = ref(null)
  let pollingInterval = null

  const totalValor = computed(() => tomaActual.value?.valor_total || 0)
  const totalItemsCount = computed(() => tomaActual.value?.total_items || 0)

  async function cargarToma(publicId) {
    isLoading.value = true
    try {
      const [toma, listaItems] = await Promise.all([
        inventarioService.obtenerToma(publicId),
        inventarioService.listarItems(publicId)
      ])
      tomaActual.value = toma
      items.value = listaItems
    } catch (error) {
      useToast().error('Error al cargar la toma de inventario')
    } finally {
      isLoading.value = false
    }
  }

  async function iniciarImportacion(tomaPublicId, file, modo) {
    try {
      const job = await inventarioService.importarArchivo(tomaPublicId, file, modo)
      jobActivo.value = job
      useToast().success('Importación iniciada en segundo plano')
      iniciarPolling(job.public_id, tomaPublicId)
      return job
    } catch (error) {
      useToast().error(error.response?.data?.detail || 'Error al iniciar la importación')
      throw error
    }
  }

  function iniciarPolling(jobPublicId, tomaPublicId) {
    if (pollingInterval) clearInterval(pollingInterval)
    
    pollingInterval = setInterval(async () => {
      try {
        const estado = await inventarioService.consultarEstadoJob(jobPublicId)
        jobActivo.value = estado

        if (estado.estado === 'COMPLETADO') {
          clearInterval(pollingInterval)
          useToast().success(`Importación completada: ${estado.filas_validas} items válidos`)
          await cargarToma(tomaPublicId) // Recargar datos
          jobActivo.value = null
        } else if (['FALLIDO', 'CANCELADO', 'TOMA_ELIMINADA'].includes(estado.estado)) {
          clearInterval(pollingInterval)
          useToast().error(`Importación fallida: ${estado.mensaje_error || 'Error desconocido'}`)
          jobActivo.value = null
        }
      } catch (error) {
        console.error('Error en polling de job:', error)
      }
    }, 2000) // Consultar cada 2 segundos
  }

  function detenerPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
    jobActivo.value = null
  }

  async function confirmarTomaAction(publicId) {
    try {
      await inventarioService.confirmarToma(publicId)
      useToast().success('Toma confirmada exitosamente')
      await cargarToma(publicId)
    } catch (error) {
      useToast().error(error.response?.data?.detail || 'Error al confirmar la toma')
    }
  }

  return {
    tomaActual,
    items,
    isLoading,
    jobActivo,
    totalValor,
    totalItemsCount,
    cargarToma,
    iniciarImportacion,
    detenerPolling,
    confirmarTomaAction
  }
})