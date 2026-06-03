// src/utils/dates.js

/**
 * Formatea una fecha (string ISO o Date) a dd/mm/yyyy
 */
export const formatDateGT = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return dateStr // Si ya viene formateada, devolverla
  return date.toLocaleDateString('es-GT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

/**
 * Formatea fecha + hora al estilo Guatemala
 */
export const formatDateTimeGT = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('es-GT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Valida que una fecha esté en formato ISO (yyyy-mm-dd) para el backend
 */
export const isValidISODate = (str) => {
  return /^\d{4}-\d{2}-\d{2}$/.test(str) && !isNaN(new Date(str).getTime())
}