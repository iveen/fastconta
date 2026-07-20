import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useInventarioStore } from '../inventarioStore'
import { inventarioService } from '@/services/inventarioService'

// Mock del servicio para no hacer llamadas HTTP reales
vi.mock('@/services/inventarioService', () => ({
  inventarioService: {
    consultarEstadoJob: vi.fn(),
    obtenerToma: vi.fn(),
    listarItems: vi.fn(),
  }
}))

describe('inventarioStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers() // Controlamos el tiempo para testear el polling
    vi.clearAllMocks()
  })

  it('debe detener el polling y recargar la toma cuando el job se COMPLETA', async () => {
    const store = useInventarioStore()
    const tomaId = 'test-toma-123'
    const jobId = 'test-job-456'

    // Simular que el job cambia a COMPLETADO en la primera consulta
    inventarioService.consultarEstadoJob.mockResolvedValueOnce({
      public_id: jobId,
      estado: 'COMPLETADO',
      filas_validas: 50,
      filas_con_error: 0
    })

    // Iniciar polling (usamos vi.advanceTimersByTime para simular el paso del tiempo)
    store.jobActivo = { public_id: jobId, estado: 'PROCESANDO' }
    
    // Simulamos el intervalo de 2500ms
    vi.advanceTimersByTime(2500)
    
    // Esperar a que se resuelvan las promesas del polling
    await vi.runAllTimersAsync()

    // Verificaciones
    expect(inventarioService.consultarEstadoJob).toHaveBeenCalledWith(jobId)
    expect(inventarioService.obtenerToma).toHaveBeenCalledWith(tomaId) // Se recargó la toma
    expect(store.jobActivo).toBeNull() // El job activo se limpió
  })
})