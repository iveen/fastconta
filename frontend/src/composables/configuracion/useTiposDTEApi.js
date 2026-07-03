import { ref } from 'vue'
import api from '@/services/api'

export function useTiposDTEApi() {
  const loading = ref(false)
  const error = ref(null)

  const listar = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/tipos-dte/', { params })
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Error al cargar tipos DTE'
      throw e
    } finally {
      loading.value = false
    }
  }

  const listarActivos = async () => {
    const { data } = await api.get('/tipos-dte/activos')
    return data
  }

  const obtenerPorId = async (id) => {
    const { data } = await api.get(`/tipos-dte/${id}`)
    return data
  }

  const crear = async (payload) => {
    const { data } = await api.post('/tipos-dte/', payload)
    return data
  }

  const actualizar = async (id, payload) => {
    const { data } = await api.patch(`/tipos-dte/${id}`, payload)
    return data
  }

  const eliminar = async (id) => {
    await api.delete(`/tipos-dte/${id}`)
  }

  const exportarExcel = async () => {
    const { data } = await api.get('/tipos-dte/exportar/excel', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'tipos_dte.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  const importarExcel = async (file, sobrescribir = false) => {
    const formData = new FormData()
    formData.append('archivo', file)
    const { data } = await api.post(
      `/tipos-dte/importar/excel?sobrescribir=${sobrescribir}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data
  }

  return {
    loading, error,
    listar, listarActivos, obtenerPorId, crear, actualizar, eliminar,
    exportarExcel, importarExcel
  }
}