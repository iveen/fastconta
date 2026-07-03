import { ref } from 'vue'
import api  from '@/services/api'

export function useRegimenDTEApi() {
  const loading = ref(false)
  const error = ref(null)

  const listarPorRegimen = async (regimenId) => {
    loading.value = true
    try {
      const { data } = await api.get(`/regimen-dte-config/regimen/${regimenId}`)
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar configuración'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarDTEPermitidos = async (regimenId) => {
    const { data } = await api.get(`/regimen-dte-config/regimen/${regimenId}/dte-permitidos`)
    return data
  }

  const asociar = async (regimenId, payload) => {
    const { data } = await api.post(`/regimen-dte-config/regimen/${regimenId}/dte`, payload)
    return data
  }

  const actualizar = async (regimenId, dteId, payload) => {
    const { data } = await api.patch(
      `/regimen-dte-config/regimen/${regimenId}/dte/${dteId}`,
      payload
    )
    return data
  }

  const desasociar = async (regimenId, dteId) => {
    await api.delete(`/regimen-dte-config/regimen/${regimenId}/dte/${dteId}`)
  }

  const asociarBulk = async (regimenId, dteIds, esExclusivo = false) => {
    const { data } = await api.post(
      `/regimen-dte-config/regimen/${regimenId}/dte/bulk`,
      { dte_ids: dteIds, es_exclusivo: esExclusivo }
    )
    return data
  }

  return {
    loading, error,
    listarPorRegimen, listarDTEPermitidos,
    asociar, actualizar, desasociar, asociarBulk
  }
}