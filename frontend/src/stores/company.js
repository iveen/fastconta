// src/stores/company.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useCompanyStore = defineStore('company', () => {
  // Estado reactivo
  const selectedCompanyId = ref(localStorage.getItem('selectedCompanyId') || null)
  const availableCompanies = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const currentCompany = computed(() => {
    return availableCompanies.value.find(c => c.id === selectedCompanyId.value) || null
  })

  const hasCompanies = computed(() => availableCompanies.value.length > 0)

  // Cargar empresas desde el backend
  const loadCompanies = async () => {
    loading.value = true
    error.value = null
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 segundos de timeout
      const response = await api.get('/empresas/mis-empresas', {
        signal: controller.signal
      })

      clearTimeout(timeoutId)
      
      availableCompanies.value = response.data
      
      // Si la empresa guardada ya no está en la lista, limpiar
      if (selectedCompanyId.value && !availableCompanies.value.find(c => c.id === selectedCompanyId.value)) {
        setCompany(null)
      }
      
      // Si no hay empresa seleccionada pero hay disponibles, seleccionar la primera
      if (!selectedCompanyId.value && availableCompanies.value.length > 0) {
        setCompany(availableCompanies.value[0].id)
      }
      
      return response.data
    } catch (err) {
      console.error('Error al cargar empresas:', err)
      if (err.name === 'AbortError') {
        error.value = 'La solicitud de empresas ha sido cancelada por timeout. Intenta nuevamente.'
      } else {
        error.value = err.response?.data?.detail || 'Error al cargar empresas'
      }
      
      availableCompanies.value = []
      throw err
    } finally {
      loading.value = false
    }
  }

  // Cambiar empresa actual
  const setCompany = (companyId) => {
    if (companyId) {
      selectedCompanyId.value = companyId
      localStorage.setItem('selectedCompanyId', companyId)
    } else {
      selectedCompanyId.value = null
      localStorage.removeItem('selectedCompanyId')
    }
  }

  // Limpiar estado (logout)
  const clearCompany = () => {
    selectedCompanyId.value = null
    availableCompanies.value = []
    error.value = null
    localStorage.removeItem('selectedCompanyId')
  }

  return {
    selectedCompanyId,
    availableCompanies,
    currentCompany,
    hasCompanies,
    loading,
    error,
    loadCompanies,
    setCompany,
    clearCompany
  }
})