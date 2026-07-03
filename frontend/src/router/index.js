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
import RegimenesFiscales from '@/views/configuracion/RegimenesFiscales.vue'
import FormularioSAT from '@/views/configuracion/FormulariosSAT.vue'
import TiposDTE from '@/views/configuracion/TiposDTE.vue'
import RegimenDTE from '@/views/configuracion/RegimenDTE.vue'
import ActividadesEconomicas from '@/views/configuracion/ActividadesEconomicas.vue'
import Monedas from '@/views/configuracion/Monedas.vue'
import Geografia from '@/views/configuracion/Geografia.vue'
import TiposPersona from '@/views/configuracion/TiposPersona.vue'
import CategoriasActivos from '@/views/configuracion/CategoriasActivos.vue'


import { useAuthStore } from '@/stores/auth'
import { useCompanyStore } from '@/stores/company'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
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
    component: Dashboard,  // ✅ Dashboard como layout padre
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'ConfiguracionHub',
        component: ConfiguracionHub,
        meta: { title: 'Configuración del Sistema' }
      },
      {
        path: 'formularios-sat',
        name: 'ConfiguracionFormulariosSAT',
        component: FormularioSAT,
        meta: { title: 'Formularios SAT' }
      },
      {
        path: 'regimenes',
        name: 'ConfiguracionRegimenes',
        component: RegimenesFiscales,
        meta: { title: 'Regímenes Fiscales' }
      },
      {
        path: 'tipos-dte',
        name: 'ConfiguracionTiposDTE',
        component: TiposDTE,
        meta: { title: 'Tipos DTE' }
      },
      {
        path: 'regimen-dte',
        name: 'ConfiguracionRegimenDTE',
        component: RegimenDTE,
        meta: { title: 'Configuración Régimen-DTE' }
      },
      {
        path: 'actividades',
        name: 'ConfiguracionActividades',
        component: ActividadesEconomicas,
        meta: { title: 'Actividades Económicas' }
      },
      {
        path: 'monedas',
        name: 'ConfiguracionMonedas',
        component: Monedas,
        meta: { title: 'Monedas' }
      },
      {
        path: 'geografia',
        name: 'ConfiguracionGeografia',
        component: Geografia,
        meta: { title: 'Geografía' }
      },
      {
        path: 'tipos-persona',
        name: 'ConfiguracionTiposPersona',
        component: TiposPersona,
        meta: { title: 'Tipos de Persona' }
      },
      {
        path: 'categorias-activos',
        name: 'ConfiguracionCategoriasActivos',
        component: CategoriasActivos,
        meta: { title: 'Categorías de Activos' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const companyStore = useCompanyStore()

  if (to.meta.requiresAuth === false) {
    if (authStore.isAuthenticated) {
      return next('/dashboard')
    }
    return next()
  }

  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  next()
})

export default router