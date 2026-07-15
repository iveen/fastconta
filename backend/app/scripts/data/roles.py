"""
Catálogo de Roles de Acceso (RBAC)
Define los niveles de acceso y permisos base del sistema FastConta.
"""

ROLES = [
    {
        "codigo": "superadmin",
        "nombre": "Super Administrador",
        "nivel_acceso": 100,
        "descripcion": "Acceso total al sistema y gestión de tenants."
    },
    {
        "codigo": "tenant_manager",
        "nombre": "Administrador de Firma",
        "nivel_acceso": 80,
        "descripcion": "Administra su firma contable, usuarios y clientes asignados."
    },
    {
        "codigo": "tenant_member",
        "nombre": "Contador de Firma",
        "nivel_acceso": 60,
        "descripcion": "Miembro de la firma con acceso a clientes y funciones contables asignadas."
    },
    {
        "codigo": "tenant_client",
        "nombre": "Cliente",
        "nivel_acceso": 20,
        "descripcion": "Acceso de solo lectura a la información de su propia empresa."
    },
]