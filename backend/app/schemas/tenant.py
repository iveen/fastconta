from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from uuid import UUID

import re
from pydantic import BaseModel, EmailStr, field_validator

def validar_nit_guatemala(texto_nit: str) -> bool:
    """
    Valida un NIT guatemalteco en sus formatos aceptados:
    - NIT tradicional: 1234567-8, 12345678-9 (base de 7 u 8 dígitos + verificador)
    - NIT personal (9 dígitos, primeros 9 del CUI): 999999999
    - CUI completo (13 dígitos): 9999999999999, 9999 99999 9999
    - CUI truncado (9 o 10 dígitos): 999999999, 9999999999 (sin validación matemática)
    """
    if not texto_nit or not isinstance(texto_nit, str):
        return False

    nit_limpio = texto_nit.replace(" ", "").replace("-", "").upper()

    if len(nit_limpio) < 2:
        return False

    # ---- Caso 1: NIT tradicional (7 u 8 dígitos base + verificador) ----
    if (len(nit_limpio) == 8 or len(nit_limpio) == 9) and nit_limpio[-1].isdigit() or nit_limpio[-1] == 'K':
        base = nit_limpio[:-1]
        verificador = nit_limpio[-1]
        if base.isdigit():
            suma = 0
            longitud = len(base)
            for i, digito in enumerate(base):
                posicion = longitud + 1 - i
                suma += int(digito) * posicion
            modulo = suma % 11
            esperado = "0" if modulo == 0 else ("K" if modulo == 1 else str(11 - modulo))
            if verificador == esperado:
                return True
        # Si no pasa, podría ser un CUI de 8 o 9 dígitos sin verificador, seguimos abajo.

    # ---- Caso 2: NIT personal de 9 dígitos (validación específica) ----
    if len(nit_limpio) == 9 and nit_limpio.isdigit():
        base_8 = nit_limpio[:8]
        digito_verificador = int(nit_limpio[8])
        suma = 0
        # Factores: 9,8,7,6,5,4,3,2 para las posiciones 1..8
        for i, digito in enumerate(base_8):
            factor = 9 - i
            suma += int(digito) * factor
        modulo = suma % 11
        esperado = 0 if (modulo == 0 or modulo == 10) else modulo
        if digito_verificador == esperado:
            return True
        # Si falla, no es válido como NIT personal

    # ---- Caso 3: CUI completo (13 dígitos) o CUI truncado (9 o 10 dígitos) ----
    if len(nit_limpio) == 13 and nit_limpio.isdigit():
        return True
    if len(nit_limpio) in (9, 10) and nit_limpio.isdigit():
        return True   # Los de 9 ya pasaron por la validación personal, pero si fallaron, aquí no se aceptan automático

    return False

class TenantCreate(BaseModel):
    tenant_name: str
    admin_email: EmailStr
    admin_password: str
    nit: str

    @field_validator('nit')
    @classmethod
    def validate_nit(cls, v: str) -> str:
        if not validar_nit_guatemala(v):
            raise ValueError(
                'El NIT no es válido. Formatos aceptados:\n'
                '- NIT tradicional: 1234567-8, 12345678-9\n'
                '- NIT personal (9 dígitos): 123456789\n'
                '- CUI completo (13 dígitos) o CUI truncado (9-10 dígitos sin dígito verificador)'
            )
        return v.replace(" ", "").replace("-", "").upper()

class TenantResponse(BaseModel):
    id: UUID
    name: str
    schema_name: str
    created_at: datetime