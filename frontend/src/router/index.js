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

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
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
      { path: 'partidas/:id', name: 'PartidaDetalle', component: PartidaDetalle},
      { path: 'periodos-fiscales', name: 'PeriodosFiscales', component: PeriodosFiscales},
      { path: 'reportes/libro-mayor/:cuenta_id', name: 'LibroMayor', component: LibroMayor },
      { path: 'facturas', name: 'Facturas', component: Facturas },
      { path: 'facturas/:factura_id', name: 'FacturaDetalle', component: FacturaDetalle, 'props': true },
      { path: 'sat-libros', name: "SAT Libros", component: SatLibros},
      { path: 'usuarios', name: 'Usuarios', component: Usuarios},
      { path: 'activos-fijos', name:"Activos Fijos", component: ActivoFijoList, meta: { requiresAuth: true} },
      { path: '/dashboard/activos-fijos/nuevo', name: 'ActivosFijosCrear', component: ActivoFijoForm, meta: { requiresAuth: true } },
      { 
        path: 'activos-fijos', 
        name: "Activos Fijos", 
        component: ActivoFijoList, 
        meta: { requiresAuth: true } 
      },
      { 
        path: 'activos-fijos/nuevo', 
        name: 'ActivosFijosCrear', 
        component: ActivoFijoForm, 
        meta: { requiresAuth: true } 
      },
      { 
        path: 'activos-fijos/editar/:id', 
        name: 'ActivosFijosEditar', 
        component: ActivoFijoForm, 
        meta: { requiresAuth: true } 
      },
      { 
        path: 'activos-fijos/:id/proyeccion', 
        name: 'ActivosFijosProyeccion', 
        component: ActivoFijoProyeccion, 
        meta: { requiresAuth: true } 
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router