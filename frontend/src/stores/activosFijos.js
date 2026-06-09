// src/stores/activosFijos.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { activosFijosService } from '@/services/activosFijosService'

export const useActivosFijosStore = defineStore('activosFijos', () => {
  // ============================================================================
  // ESTADO (reactivo)
  // ============================================================================
  const activos = ref([])
  const categorias = ref([])
  const proyeccion = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // ✅ Persistencia de empresa seleccionada (UX: evitar re-selección al navegar)
  const empresaSeleccionadaId = ref(null)

  // ============================================================================
  // ACCIONES
  // ============================================================================

  /**
   * Carga el catálogo global de categorías de activos fijos (schema public)
   */
  const fetchCategorias = async () => {
    try {
      const response = await activosFijosService.getCategorias()
      categorias.value = response.data
      error.value = null
    } catch (err) {
      console.error('❌ Error al cargar categorías:', err)
      error.value = 'No se pudieron cargar las categorías de activos. Verifica tu conexión.'
      categorias.value = []
    }
  }

  /**
   * Carga los activos fijos de una empresa específica
   * @param {string} empresaId - UUID de la empresa
   */
  const fetchActivos = async (empresaId) => {
    if (!empresaId) {
      console.warn('⚠️ fetchActivos llamado sin empresa_id')
      return
    }
    
    loading.value = true
    error.value = null
    
    try {
      const response = await activosFijosService.getActivos(empresaId)
      activos.value = response.data
      // ✅ Guardar selección en estado y localStorage
      empresaSeleccionadaId.value = empresaId
      localStorage.setItem('fastconta_ultima_empresa', empresaId)
    } catch (err) {
      console.error('❌ Error al cargar activos:', err)
      error.value = err.response?.data?.detail || 'No se pudieron cargar los activos fijos'
      activos.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Obtiene la proyección de depreciación para un activo específico
   * @param {string} activoId - UUID del activo
   * @param {string} empresaId - UUID de la empresa (para validación de acceso)
   * @returns {Promise<Object>} - Datos de la proyección
   */
  const fetchProyeccion = async (activoId, empresaId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await activosFijosService.getProyeccion(activoId, empresaId)
      proyeccion.value = response.data
      return response.data
    } catch (err) {
      console.error('❌ Error al cargar proyección:', err)
      error.value = err.response?.data?.detail || 'No se pudo cargar la proyección de depreciación'
      proyeccion.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Procesa la depreciación mensual consolidada para todos los activos de una empresa
   * @param {string} empresaId - UUID de la empresa
   * @param {number} anio - Año del periodo (ej: 2024)
   * @param {number} mes - Mes del periodo (1-12)
   * @returns {Promise<Object>} - Resumen de la partida generada
   */
  const procesarDepreciacionMensual = async (empresaId, anio, mes) => {
    loading.value = true
    try {
      const response = await activosFijosService.procesarDepreciacion(empresaId, anio, mes)
      return response.data
    } catch (err) {
      console.error('❌ Error al procesar depreciación:', err)
      error.value = err.response?.data?.detail || 'No se pudo procesar la depreciación mensual'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Crea un nuevo activo fijo (wrapper del servicio para centralizar manejo de errores)
   * @param {string} empresaId - UUID de la empresa
   * @param {Object} data - Datos del activo (schema ActivoFijoCreate)
   * @returns {Promise<Object>} - El activo creado
   */
  const crearActivo = async (empresaId, data) => {
    loading.value = true
    error.value = null
    try {
      const response = await activosFijosService.crearActivo(empresaId, data)
      // ✅ Actualizar lista localmente para UX inmediata (opcional)
      activos.value.unshift(response.data)
      return response.data
    } catch (err) {
      console.error('❌ Error al crear activo:', err)
      error.value = err.response?.data?.detail || 'No se pudo crear el activo fijo'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Actualiza un activo fijo existente
   * @param {string} empresaId - UUID de la empresa
   * @param {string} activoId - UUID del activo a actualizar
   * @param {Object} data - Datos a actualizar (schema ActivoFijoUpdate)
   * @returns {Promise<Object>} - El activo actualizado
   */
  const actualizarActivo = async (empresaId, activoId, data) => {
    loading.value = true
    error.value = null
    try {
      const response = await activosFijosService.actualizarActivo(empresaId, activoId, data)
      // ✅ Actualizar el elemento en la lista localmente
      const index = activos.value.findIndex(a => a.id === activoId)
      if (index !== -1) {
        activos.value[index] = response.data
      }
      return response.data
    } catch (err) {
      console.error('❌ Error al actualizar activo:', err)
      error.value = err.response?.data?.detail || 'No se pudo actualizar el activo fijo'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================================
  // UTILIDADES DE PERSISTENCIA Y NAVEGACIÓN
  // ============================================================================

  /**
   * Restaura la empresa seleccionada desde localStorage (al cargar la app)
   * @returns {string|null} - El ID de la empresa restaurada o null
   */
  const initFromStorage = () => {
    const guardada = localStorage.getItem('fastconta_ultima_empresa')
    if (guardada) {
      empresaSeleccionadaId.value = guardada
      return guardada
    }
    return null
  }

  /**
   * Limpia la selección de empresa y los datos asociados
   */
  const clearEmpresaSeleccionada = () => {
    empresaSeleccionadaId.value = null
    localStorage.removeItem('fastconta_ultima_empresa')
    activos.value = []
    proyeccion.value = null
  }

  /**
   * Helper para formatear montos en Quetzales (reutilizable en componentes)
   * @param {number|Decimal} value - Monto a formatear
   * @returns {string} - Monto formateado como "Q 1,234.56"
   */
  const formatMoney = (value) => {
    return Number(value).toLocaleString('es-GT', {
      style: 'currency',
      currency: 'GTQ',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  }

  // ============================================================================
  // RETORNO (lo que se expone a los componentes vía store)
  // ============================================================================
  return {
    // Estado
    activos,
    categorias,
    proyeccion,
    loading,
    error,
    empresaSeleccionadaId,
    
    // Acciones principales
    fetchCategorias,
    fetchActivos,
    fetchProyeccion,
    procesarDepreciacionMensual,
    crearActivo,
    actualizarActivo,
    
    // Utilidades de persistencia
    initFromStorage,
    clearEmpresaSeleccionada,
    
    // Helpers de formato
    formatMoney
  }
})