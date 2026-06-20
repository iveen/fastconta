<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 mb-2">
        ⚙️ Configuración del Sistema
      </h1>
      <p class="text-gray-600">
        Administra todos los catálogos y parámetros del sistema contable
      </p>
    </div>

    <!-- Grid de grupos -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Grupo 1: Motor Tributario -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
          <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-2xl">🏛️</span>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-800">Motor Tributario</h2>
            <p class="text-sm text-gray-500">Regímenes, impuestos y tipos de documentos</p>
          </div>
        </div>
        
        <div class="space-y-3">
          <ConfigCard
            icon="🏢"
            title="Regímenes Fiscales"
            description="Administra regímenes y su asociación con formularios SAT"
            to="/configuracion/regimenes"
          />
          <ConfigCard
            icon="📄"
            title="Tipos DTE"
            description="Catálogo de documentos tributarios electrónicos"
            to="/configuracion/tipos-dte"
          />
          <ConfigCard
            icon="🔗"
            title="Configuración Régimen-DTE"
            description="Define qué DTE puede emitir cada régimen"
            to="/configuracion/regimen-dte"
          />
        </div>
      </div>

      <!-- Grupo 2: Declaraciones SAT -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
          <div class="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
            <span class="text-2xl">📋</span>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-800">Declaraciones SAT</h2>
            <p class="text-sm text-gray-500">Formularios, casillas y reglas de cálculo</p>
          </div>
        </div>
        
        <div class="space-y-3">
          <ConfigCard
            icon="📝"
            title="Formularios SAT"
            description="Versionado de formularios (2237, 2046, 2276, etc.)"
            to="/configuracion/formularios-sat"
          />
          <ConfigCard
            icon="📑"
            title="Secciones y Casillas"
            description="Estructura de formularios y sus campos"
            to="/configuracion/secciones"
          />
          <ConfigCard
            icon="🔍"
            title="Reglas de Filtrado"
            description="Define qué facturas alimentan cada casilla"
            to="/configuracion/reglas-filtrado"
          />
          <ConfigCard
            icon="🔢"
            title="Mapeo Contable"
            description="Vincula casillas SAT con cuentas contables"
            to="/configuracion/mapeo-contable"
          />
        </div>
      </div>

      <!-- Grupo 3: Catálogos -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
          <div class="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
            <span class="text-2xl">📚</span>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-800">Catálogos</h2>
            <p class="text-sm text-gray-500">Catálogos base del sistema</p>
          </div>
        </div>
        
        <div class="space-y-3">
          <ConfigCard
            icon="💼"
            title="Actividades Económicas"
            description="Catálogo SAT de actividades económicas"
            to="/configuracion/actividades"
          />
          <ConfigCard
            icon="💱"
            title="Monedas"
            description="Catálogo Banguat / ISO 4217"
            to="/configuracion/monedas"
          />
          <ConfigCard
            icon="🗺️"
            title="Geografía"
            description="Departamentos y municipios de Guatemala"
            to="/configuracion/geografia"
          />
          <ConfigCard
            icon="👤"
            title="Tipos de Persona"
            description="Natural, Jurídica, etc."
            to="/configuracion/tipos-persona"
          />
          <ConfigCard
            icon="🏗️"
            title="Categorías Activos"
            description="Tasas de depreciación (Decreto 10-2012)"
            to="/configuracion/categorias-activos"
          />
        </div>
      </div>

      <!-- Grupo 4: Administración -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
          <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
            <span class="text-2xl">👥</span>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-800">Administración</h2>
            <p class="text-sm text-gray-500">Usuarios y permisos del sistema</p>
          </div>
        </div>
        
        <div class="space-y-3">
          <ConfigCard
            icon="👨‍💼"
            title="Usuarios"
            description="Gestión de usuarios y accesos"
            to="/dashboard/usuarios"
          />
          <ConfigCard
            icon="🔐"
            title="Roles y Permisos"
            description="Configuración de roles RBAC"
            to="/configuracion/roles"
          />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import ConfigCard from '@/components/configuracion/ConfigCard.vue'
</script>