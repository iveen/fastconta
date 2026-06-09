// src/utils/errorHandler.js
export const formatFastApiError = (err) => {
  // Si es un error de validación 422 de FastAPI
  if (err.response?.status === 422 && Array.isArray(err.response.data?.detail)) {
    const errores = err.response.data.detail
    
    // Buscamos el error más relevante (a veces hay varios, tomamos el primero o el que tenga 'value_error')
    const errorPrincipal = errores.find(e => e.type === 'value_error') || errores[0]
    
    let mensaje = errorPrincipal.msg || 'Error de validación en los datos enviados'
    
    // Limpiamos los prefijos feos que agrega Pydantic automáticamente
    mensaje = mensaje.replace(/^Value error,\s*/i, '')
    mensaje = mensaje.replace(/^Assertion failed,\s*/i, '')
    
    return mensaje
  }
  
  // Para otros errores (400, 403, 404, 500) que sí devuelven string en detail
  return err.response?.data?.detail || err.message || 'Ocurrió un error inesperado en el servidor'
}