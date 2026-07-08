```
.
├── Dockerfile
├── README.md
├── estructura.md
├── index.html
├── jsconfig.json
├── nginx.conf
├── node_modules
│   ├── @lucide
│   │   └── vue -> ../.pnpm/@lucide+vue@1.17.0_vue@3.5.34/node_modules/@lucide/vue
│   ├── @tailwindcss
│   │   └── vite -> ../.pnpm/@tailwindcss+vite@4.3.0_vite@8.0.13_jiti@2.7.0_yaml@2.9.0_/node_modules/@tailwindcss/vite
│   ├── @vitejs
│   │   └── plugin-vue -> ../.pnpm/@vitejs+plugin-vue@6.0.7_vite@8.0.13_jiti@2.7.0_yaml@2.9.0__vue@3.5.34/node_modules/@vitejs/plugin-vue
│   ├── axios -> .pnpm/axios@1.16.1/node_modules/axios
│   ├── pinia -> .pnpm/pinia@3.0.4_vue@3.5.34/node_modules/pinia
│   ├── tailwindcss -> .pnpm/tailwindcss@4.3.0/node_modules/tailwindcss
│   ├── vite -> .pnpm/vite@8.0.13_jiti@2.7.0_yaml@2.9.0/node_modules/vite
│   ├── vite-plugin-vue-devtools -> .pnpm/vite-plugin-vue-devtools@8.1.2_vite@8.0.13_jiti@2.7.0_yaml@2.9.0__vue@3.5.34/node_modules/vite-plugin-vue-devtools
│   ├── vue -> .pnpm/vue@3.5.34/node_modules/vue
│   ├── vue-router -> .pnpm/vue-router@5.0.7_@vue+compiler-sfc@3.5.34_pinia@3.0.4_vue@3.5.34__vue@3.5.34/node_modules/vue-router
│   └── vue3-toastify -> .pnpm/vue3-toastify@0.2.9_vue@3.5.34/node_modules/vue3-toastify
├── package.json
├── pnpm-lock.yaml
├── public
│   ├── favicon.ico
│   └── favicon.svg
├── src
│   ├── App.vue
│   ├── components
│   │   ├── ActivosFijos
│   │   │   └── ProcesarDepreciacionModal.vue
│   │   ├── DateInput.vue
│   │   ├── Shared
│   │   │   └── BuscadorCuentas.vue
│   │   ├── Sidebar.vue
│   │   ├── SuperAdminContextSelector.vue
│   │   ├── TopNavbar.vue
│   │   ├── configuracion
│   │   │   ├── ConfigCard.vue
│   │   │   ├── ConfiguracionHub.vue
│   │   │   └── formularios
│   │   │       ├── CasillaItem.vue
│   │   │       ├── CasillaModal.vue
│   │   │       ├── FormularioDetail.vue
│   │   │       ├── FormularioDuplicarModal.vue
│   │   │       ├── FormularioHistorialView.vue
│   │   │       ├── FormularioList.vue
│   │   │       ├── FormularioModal.vue
│   │   │       ├── SeccionItem.vue
│   │   │       └── SeccionModal.vue
│   │   ├── declaraciones
│   │   │   ├── AjusteManual.vue
│   │   │   ├── CasillaRow.vue
│   │   │   ├── FormularioSombra.vue
│   │   │   ├── KpiCard.vue
│   │   │   ├── ModalDrillDown.vue
│   │   │   └── SeccionFormulario.vue
│   │   └── empresas
│   │       ├── DomicilioManager.vue
│   │       └── RepresentanteManager.vue
│   ├── composables
│   │   ├── catalogos
│   │   │   ├── useActividadesApi.js
│   │   │   ├── useCategoriasActivosApi.js
│   │   │   ├── useGeografiaApi.js
│   │   │   ├── useMonedasApi.js
│   │   │   └── useTiposPersonaApi.js
│   │   ├── configuracion
│   │   │   ├── useRegimenDTEApi.js
│   │   │   ├── useRegimenesApi.js
│   │   │   └── useTiposDTEApi.js
│   │   ├── useDeclaraciones.js
│   │   └── useToast.js
│   ├── index.css
│   ├── layouts
│   │   └── SuperadminLayout.vue
│   ├── main.js
│   ├── router
│   │   └── index.js
│   ├── services
│   │   ├── activosFijosService.js
│   │   ├── api.js
│   │   ├── casillasService.js
│   │   ├── declaraciones.js
│   │   ├── empresas.js
│   │   ├── formulariosService.js
│   │   ├── planCuentasService.js
│   │   ├── seccionesService.js
│   │   └── users.js
│   ├── stores
│   │   ├── activosFijos.js
│   │   ├── auth.js
│   │   ├── casillas.js
│   │   ├── company.js
│   │   ├── counter.js
│   │   ├── formularios.js
│   │   ├── secciones.js
│   │   └── superAdmin.js
│   ├── utils
│   │   ├── dates.js
│   │   └── errorHandler.js
│   └── views
│       ├── ActivoFijoForm.vue
│       ├── ActivoFijoList.vue
│       ├── ActivoFijoProyeccion.vue
│       ├── Cierre.vue
│       ├── Dashboard.vue
│       ├── Declaraciones.vue
│       ├── Empresas.vue
│       ├── FacturaDetalle.vue
│       ├── Facturas.vue
│       ├── LibroMayor.vue
│       ├── Login.vue
│       ├── PartidaDetalle.vue
│       ├── Partidas.vue
│       ├── PeriodosFiscales.vue
│       ├── PlanCuentas.vue
│       ├── Reportes.vue
│       ├── SatLibros.vue
│       ├── ToastContainer.vue
│       ├── Usuarios.vue
│       └── configuracion
│           ├── ActividadesEconomicas.vue
│           ├── CategoriasActivos.vue
│           ├── FormulariosSAT.vue
│           ├── Geografia.vue
│           ├── Monedas.vue
│           ├── RegimenDTE.vue
│           ├── RegimenesFiscales.vue
│           ├── TiposDTE.vue
│           └── TiposPersona.vue
├── tailwind.config.js
└── vite.config.js

35 directories, 99 files
```
