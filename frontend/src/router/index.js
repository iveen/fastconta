// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import Empresas from '@/views/Empresas.vue'
import PlanCuentas from '@/views/PlanCuentas.vue'
import Partidas from '@/views/Partidas.vue'
import Reportes from '@/views/Reportes.vue'
import Cierre from '@/views/Cierre.vue'
import PartidaDetalle from '@/views/PartidaDetalle.vue'
import PeriodosFiscales from '@/views/PeriodosFiscales.vue'
import SatLibros from '@/views/SatLibros.vue'
import LibroMayor from '@/views/LibroMayor.vue'
import Facturas from '@/views/Facturas.vue'
import FacturaDetalle from '@/views/FacturaDetalle.vue'
import Usuarios from '@/views/Usuarios.vue'
import ActivoFijoList from '@/views/ActivoFijoList.vue'
import ActivoFijoForm from '@/views/ActivoFijoForm.vue'
import ActivoFijoProyeccion from '@/views/ActivoFijoProyeccion.vue'
import ConfiguracionHub from '@/components/configuracion/ConfiguracionHub.vue'
import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'

const routes = [
  { 
    path: '/', 
    redirect: '/dashboard'  // ✅ Cambiado: redirige a dashboard si está autenticado
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard/empresas' },
      { path: 'empresas', name: 'Empresas', component: Empresas },
      { path: 'plan-cuentas', name: 'PlanCuentas', component: PlanCuentas },
      { path: 'partidas', name: 'Partidas', component: Partidas },
      { path: 'reportes', name: 'Reportes', component: Reportes },
      { path: 'cierre', name: 'Cierre', component: Cierre },
      { path: 'partidas/:id', name: 'PartidaDetalle', component: PartidaDetalle },
      { path: 'periodos-fiscales', name: 'PeriodosFiscales', component: PeriodosFiscales },
      { path: 'reportes/libro-mayor/:cuenta_id', name: 'LibroMayor', component: LibroMayor },
      { path: 'facturas', name: 'Facturas', component: Facturas },
      { path: 'facturas/:factura_id', name: 'FacturaDetalle', component: FacturaDetalle, props: true },
      { path: 'sat-libros', name: 'SATLibros', component: SatLibros },
      { path: 'usuarios', name: 'Usuarios', component: Usuarios },
      { path: 'activos-fijos', name: 'ActivosFijos', component: ActivoFijoList, meta: { requiresAuth: true } },
      { path: 'activos-fijos/nuevo', name: 'ActivosFijosCrear', component: ActivoFijoForm, meta: { requiresAuth: true } },
      { path: 'activos-fijos/editar/:id', name: 'ActivosFijosEditar', component: ActivoFijoForm, meta: { requiresAuth: true } },
      { path: 'activos-fijos/:id/proyeccion', name: 'ActivosFijosProyeccion', component: ActivoFijoProyeccion, meta: { requiresAuth: true } }
    ]
  },
  {
    path: '/declaraciones',
    name: 'Declaraciones',
    component: () => import('@/views/Declaraciones.vue'),
    meta: { requiresAuth: true, title: 'Declaraciones SAT' }
  },
  {
    path: '/configuracion',
    name: 'ConfiguracionHub',
    component: ConfiguracionHub,
    meta: { requiresAuth: true, title: 'Configuración del Sistema' }
  },
  {
    path: '/configuracion/formularios-sat',
    name: 'ConfiguracionFormulariosSAT',
    component: () => import('@/views/configuracion/FormulariosSAT.vue'),
    meta: { requiresAuth: true, title: 'Formularios SAT' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ✅ CORRECCIÓN: Router guard simplificado y correcto
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const companyStore = useCompanyStore()

  // Rutas públicas (login)
  if (to.meta.requiresAuth === false) {
    if (authStore.isAuthenticated) {
      return next('/dashboard')  // ✅ Redirige a dashboard, no a "/"
    }
    return next()
  }

  // Verificar autenticación
  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  // Si llegamos aquí, el usuario está autenticado
  next()
})

export default router