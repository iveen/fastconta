```
.
├── Dockerfile
├── TR2026.xlsx
├── alembic
│   ├── README
│   ├── __pycache__
│   │   └── env.cpython-312.pyc
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 06c750bb6c0c_delete_max_companies_limit_on_tenant.py
│       ├── 22cc9e33a26f_initial_public_schema_bigint_softdelete_.py
│       ├── 3769f118301e_change_nullability_users_model.py
│       ├── 9b4ed6096f13_seed_initial_roles_py.py
│       └── __pycache__
│           ├── 06c750bb6c0c_delete_max_companies_limit_on_tenant.cpython-312.pyc
│           ├── 18342bbdcbc3_add_deferred_audit_foreign_keys.cpython-312.pyc
│           ├── 22cc9e33a26f_initial_public_schema_bigint_softdelete_.cpython-312.pyc
│           ├── 3769f118301e_change_nullability_users_model.cpython-312.pyc
│           ├── 9b4ed6096f13_seed_initial_roles.cpython-312.pyc
│           └── 9b4ed6096f13_seed_initial_roles_py.cpython-312.pyc
├── alembic.ini
├── alembic_migrations_refactor.zip
├── alembic_tenant
│   ├── README
│   ├── __pycache__
│   │   └── env.cpython-312.pyc
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 4360f9683f8b_initial_schema_bigint_softelete_audit_py.py
│       └── __pycache__
│           └── 4360f9683f8b_initial_schema_bigint_softelete_audit_py.cpython-312.pyc
├── alembic_tenant.ini
├── alembic_tenant_migrations_refactor.zip
├── app
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-312.pyc
│   │   ├── config.cpython-312.pyc
│   │   └── main.cpython-312.pyc
│   ├── api
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   └── __init__.cpython-312.pyc
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-312.pyc
│   │       │   └── router.cpython-312.pyc
│   │       ├── endpoints
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   ├── activos_fijos.cpython-312.pyc
│   │       │   │   ├── auth.cpython-312.pyc
│   │       │   │   ├── balances.cpython-312.pyc
│   │       │   │   ├── casillas_sat.cpython-312.pyc
│   │       │   │   ├── cierre.cpython-312.pyc
│   │       │   │   ├── declaraciones.cpython-312.pyc
│   │       │   │   ├── domicilios.cpython-312.pyc
│   │       │   │   ├── empresas.cpython-312.pyc
│   │       │   │   ├── facturas.cpython-312.pyc
│   │       │   │   ├── formularios_sat.cpython-312.pyc
│   │       │   │   ├── partidas.cpython-312.pyc
│   │       │   │   ├── periodos_fiscales.cpython-312.pyc
│   │       │   │   ├── plan_cuentas.cpython-312.pyc
│   │       │   │   ├── regimen_dte_config.cpython-312.pyc
│   │       │   │   ├── regimenes_fiscales.cpython-312.pyc
│   │       │   │   ├── reglas_filtrado.cpython-312.pyc
│   │       │   │   ├── representantes_legales.cpython-312.pyc
│   │       │   │   ├── sat_libros.cpython-312.pyc
│   │       │   │   ├── secciones_formulario.cpython-312.pyc
│   │       │   │   ├── tenants.cpython-312.pyc
│   │       │   │   ├── tipos_dte.cpython-312.pyc
│   │       │   │   └── users.cpython-312.pyc
│   │       │   ├── auth.py
│   │       │   ├── base
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   ├── domicilios.cpython-312.pyc
│   │       │   │   │   ├── empresas.cpython-312.pyc
│   │       │   │   │   ├── representantes_legales.cpython-312.pyc
│   │       │   │   │   ├── tenants.cpython-312.pyc
│   │       │   │   │   └── users.cpython-312.pyc
│   │       │   │   ├── domicilios.py
│   │       │   │   ├── empresas.py
│   │       │   │   ├── representantes_legales.py
│   │       │   │   ├── tenants.py
│   │       │   │   └── users.py
│   │       │   ├── catalogos
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   ├── actividades.cpython-312.pyc
│   │       │   │   │   ├── catalogo_impuestos.cpython-312.pyc
│   │       │   │   │   ├── categorias_activos.cpython-312.pyc
│   │       │   │   │   ├── estados_libro.cpython-312.pyc
│   │       │   │   │   ├── formularios_sat.cpython-312.pyc
│   │       │   │   │   ├── geografia.cpython-312.pyc
│   │       │   │   │   ├── monedas.cpython-312.pyc
│   │       │   │   │   ├── regimen_dte_config.cpython-312.pyc
│   │       │   │   │   ├── regimenes_fiscales.cpython-312.pyc
│   │       │   │   │   ├── tipo_persona.cpython-312.pyc
│   │       │   │   │   ├── tipos_dte.cpython-312.pyc
│   │       │   │   │   └── tipos_libro.cpython-312.pyc
│   │       │   │   ├── actividades.py
│   │       │   │   ├── catalogo_impuestos.py
│   │       │   │   ├── categorias_activos.py
│   │       │   │   ├── estados_libro.py
│   │       │   │   ├── geografia.py
│   │       │   │   ├── monedas.py
│   │       │   │   ├── regimen_dte_config.py
│   │       │   │   ├── regimenes_fiscales.py
│   │       │   │   ├── tipo_persona.py
│   │       │   │   ├── tipos_dte.py
│   │       │   │   └── tipos_libro.py
│   │       │   ├── contabilidad
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   ├── activos_fijos.cpython-312.pyc
│   │       │   │   │   ├── balances.cpython-312.pyc
│   │       │   │   │   ├── cierre.cpython-312.pyc
│   │       │   │   │   ├── partidas.cpython-312.pyc
│   │       │   │   │   ├── periodos_fiscales.cpython-312.pyc
│   │       │   │   │   └── plan_cuentas.cpython-312.pyc
│   │       │   │   ├── activos_fijos.py
│   │       │   │   ├── balances.py
│   │       │   │   ├── cierre.py
│   │       │   │   ├── partidas.py
│   │       │   │   ├── periodos_fiscales.py
│   │       │   │   └── plan_cuentas.py
│   │       │   ├── fel
│   │       │   │   ├── __init__.py
│   │       │   │   ├── __pycache__
│   │       │   │   │   ├── __init__.cpython-312.pyc
│   │       │   │   │   └── facturas.cpython-312.pyc
│   │       │   │   └── facturas.py
│   │       │   └── sat
│   │       │       ├── __init__.py
│   │       │       ├── __pycache__
│   │       │       │   ├── __init__.cpython-312.pyc
│   │       │       │   ├── declaraciones.cpython-312.pyc
│   │       │       │   ├── formularios_sat.cpython-312.pyc
│   │       │       │   ├── reglas_filtrado.cpython-312.pyc
│   │       │       │   └── sat_libros.cpython-312.pyc
│   │       │       ├── casillas_sat.py
│   │       │       ├── declaraciones.py
│   │       │       ├── formularios_sat.py
│   │       │       ├── reglas_filtrado.py
│   │       │       ├── sat_libros.py
│   │       │       └── secciones_formulario.py
│   │       └── router.py
│   ├── config.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── empresa_utils.cpython-312.pyc
│   │   │   ├── jwt_utils.cpython-312.pyc
│   │   │   ├── security.cpython-312.pyc
│   │   │   ├── tenant.cpython-312.pyc
│   │   │   ├── tenant_limits.cpython-312.pyc
│   │   │   └── tenant_utils.cpython-312.pyc
│   │   ├── empresa_utils.py
│   │   ├── export
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── builder.cpython-312.pyc
│   │   │   │   ├── excel_exporter.cpython-312.pyc
│   │   │   │   ├── models.cpython-312.pyc
│   │   │   │   └── pdf_exporter.cpython-312.pyc
│   │   │   ├── builder.py
│   │   │   ├── excel_exporter.py
│   │   │   ├── models.py
│   │   │   └── pdf_exporter.py
│   │   ├── file_handlers
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── base.cpython-312.pyc
│   │   │   │   ├── pdf_handler.cpython-312.pyc
│   │   │   │   └── xml_handler.cpython-312.pyc
│   │   │   ├── base.py
│   │   │   ├── pdf_handler.py
│   │   │   └── xml_handler.py
│   │   ├── jwt_utils.py
│   │   ├── security.py
│   │   ├── tenant.py
│   │   ├── tenant_limits.py
│   │   └── tenant_utils.py
│   ├── crud
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── secuencias.cpython-312.pyc
│   │   └── secuencias.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── base.cpython-312.pyc
│   │   │   ├── mixins.cpython-312.pyc
│   │   │   └── session.cpython-312.pyc
│   │   ├── base.py
│   │   ├── mixins.py
│   │   └── session.py
│   ├── dependencies
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   └── empresa.cpython-312.pyc
│   │   └── empresa.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── global_models.cpython-312.pyc
│   │   │   └── tenant_models.cpython-312.pyc
│   │   ├── global_models.py
│   │   └── tenant_models.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── activos_fijos.cpython-312.pyc
│   │   │   ├── auth.cpython-312.pyc
│   │   │   ├── balances.cpython-312.pyc
│   │   │   ├── declaracion.cpython-312.pyc
│   │   │   ├── domicilio.cpython-312.pyc
│   │   │   ├── empresa.cpython-312.pyc
│   │   │   ├── factura.cpython-312.pyc
│   │   │   ├── partida.cpython-312.pyc
│   │   │   ├── periodo_fiscal.cpython-312.pyc
│   │   │   ├── plan_cuentas.cpython-312.pyc
│   │   │   ├── representante_legal.cpython-312.pyc
│   │   │   ├── sat_libros.cpython-312.pyc
│   │   │   ├── tenant.cpython-312.pyc
│   │   │   └── user.cpython-312.pyc
│   │   ├── auth.py
│   │   ├── base
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── domicilio.cpython-312.pyc
│   │   │   │   ├── empresa.cpython-312.pyc
│   │   │   │   ├── representante_legal.cpython-312.pyc
│   │   │   │   ├── tenant.cpython-312.pyc
│   │   │   │   └── user.cpython-312.pyc
│   │   │   ├── domicilio.py
│   │   │   ├── empresa.py
│   │   │   ├── representante_legal.py
│   │   │   ├── tenant.py
│   │   │   └── user.py
│   │   ├── catalogos
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── actividad_economica.cpython-312.pyc
│   │   │   │   ├── categoria_activo.cpython-312.pyc
│   │   │   │   ├── estado_libro.cpython-312.pyc
│   │   │   │   ├── geografia.cpython-312.pyc
│   │   │   │   ├── impuesto.cpython-312.pyc
│   │   │   │   ├── moneda.cpython-312.pyc
│   │   │   │   ├── tipo_dte.cpython-312.pyc
│   │   │   │   ├── tipo_libro.cpython-312.pyc
│   │   │   │   └── tipo_persona.cpython-312.pyc
│   │   │   ├── actividad_economica.py
│   │   │   ├── categoria_activo.py
│   │   │   ├── estado_libro.py
│   │   │   ├── geografia.py
│   │   │   ├── impuesto.py
│   │   │   ├── moneda.py
│   │   │   ├── tipo_dte.py
│   │   │   ├── tipo_libro.py
│   │   │   └── tipo_persona.py
│   │   ├── contabilidad
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── activos_fijos.cpython-312.pyc
│   │   │   │   ├── balances.cpython-312.pyc
│   │   │   │   ├── partida.cpython-312.pyc
│   │   │   │   ├── periodo_fiscal.cpython-312.pyc
│   │   │   │   └── plan_cuentas.cpython-312.pyc
│   │   │   ├── activos_fijos.py
│   │   │   ├── balances.py
│   │   │   ├── partida.py
│   │   │   ├── periodo_fiscal.py
│   │   │   └── plan_cuentas.py
│   │   ├── fel
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   └── factura.cpython-312.pyc
│   │   │   └── factura.py
│   │   └── sat
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-312.pyc
│   │       │   ├── casilla.cpython-312.pyc
│   │       │   ├── declaracion.cpython-312.pyc
│   │       │   ├── formulario.cpython-312.pyc
│   │       │   ├── regimen_fiscal.cpython-312.pyc
│   │       │   ├── regla_filtrado.cpython-312.pyc
│   │       │   ├── sat_libros.cpython-312.pyc
│   │       │   └── seccion.cpython-312.pyc
│   │       ├── casilla.py
│   │       ├── declaracion.py
│   │       ├── formulario.py
│   │       ├── mapeo_casilla.py
│   │       ├── mapeo_casilla_cuenta.py
│   │       ├── regimen_fiscal.py
│   │       ├── regla_filtrado.py
│   │       ├── sat_libros.py
│   │       └── seccion.py
│   ├── scripts
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── create_superadmin.cpython-312.pyc
│   │   │   └── seed_tipos_estados_libro.cpython-312.pyc
│   │   ├── create_superadmin.py
│   │   ├── data
│   │   │   ├── INE_Geografia_Guatemala.xlsx
│   │   │   ├── TR2026.xlsx
│   │   │   ├── catalogo_monedas.csv
│   │   │   └── tipos_dte.csv
│   │   ├── seed_categorias_activos.py
│   │   ├── seed_global.py
│   │   ├── seed_sat_2237.py
│   │   ├── seed_sat_2237_completo.py
│   │   ├── seed_sat_2237_versionado.py
│   │   ├── seed_script.py
│   │   ├── seed_tipos_estados_libro.py
│   │   ├── seed_tipos_persona.py
│   │   └── seeds
│   │       ├── __init__.py
│   │       └── sat_2237_iva.py
│   ├── services
│   │   ├── __pycache__
│   │   │   ├── activos_fijos_service.cpython-312.pyc
│   │   │   ├── banguat_ws.cpython-312.pyc
│   │   │   ├── cierre_contable.cpython-312.pyc
│   │   │   ├── declaraciones_service.cpython-312.pyc
│   │   │   ├── domicilio_service.cpython-312.pyc
│   │   │   ├── empresa_service.cpython-312.pyc
│   │   │   ├── fel_parser.cpython-312.pyc
│   │   │   ├── partida_service.cpython-312.pyc
│   │   │   ├── periodos.cpython-312.pyc
│   │   │   ├── periodos_service.cpython-312.pyc
│   │   │   ├── plan_cuentas_service.cpython-312.pyc
│   │   │   ├── reportes_export.cpython-312.pyc
│   │   │   ├── representante_legal_service.cpython-312.pyc
│   │   │   ├── reversion_cierre.cpython-312.pyc
│   │   │   ├── sat_libros_service.cpython-312.pyc
│   │   │   ├── tenant_setup.cpython-312.pyc
│   │   │   └── validation_service.cpython-312.pyc
│   │   ├── base
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── domicilio_service.cpython-312.pyc
│   │   │   │   ├── empresa_service.cpython-312.pyc
│   │   │   │   └── representante_legal_service.cpython-312.pyc
│   │   │   ├── domicilio_service.py
│   │   │   ├── empresa_service.py
│   │   │   ├── representante_legal_service.py
│   │   │   └── tenant_setup.py
│   │   ├── calculos
│   │   │   ├── __init__.py
│   │   │   └── motor_calculo.py
│   │   ├── catalogos
│   │   │   ├── __pycache__
│   │   │   │   ├── actividad_economica_service.cpython-312.pyc
│   │   │   │   ├── categoria_activo_service.cpython-312.pyc
│   │   │   │   ├── estado_libro_service.cpython-312.pyc
│   │   │   │   ├── geografia_service.cpython-312.pyc
│   │   │   │   ├── impuesto_service.cpython-312.pyc
│   │   │   │   ├── moneda_service.cpython-312.pyc
│   │   │   │   ├── tipo_libro_service.cpython-312.pyc
│   │   │   │   └── tipo_persona_service.cpython-312.pyc
│   │   │   ├── actividad_economica_service.py
│   │   │   ├── categoria_activo_service.py
│   │   │   ├── estado_libro_service.py
│   │   │   ├── geografia_service.py
│   │   │   ├── impuesto_service.py
│   │   │   ├── moneda_service.py
│   │   │   ├── tipo_libro_service.py
│   │   │   └── tipo_persona_service.py
│   │   ├── contabilidad
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── activos_fijos_service.cpython-312.pyc
│   │   │   │   ├── cierre_contable.cpython-312.pyc
│   │   │   │   ├── partida_service.cpython-312.pyc
│   │   │   │   ├── periodos_service.cpython-312.pyc
│   │   │   │   ├── plan_cuentas_service.cpython-312.pyc
│   │   │   │   └── reversion_cierre.cpython-312.pyc
│   │   │   ├── activos_fijos_service.py
│   │   │   ├── cierre_contable.py
│   │   │   ├── partida_service.py
│   │   │   ├── periodos_service.py
│   │   │   ├── plan_cuentas_service.py
│   │   │   └── reversion_cierre.py
│   │   ├── deprecated
│   │   │   └── reportes_export.py
│   │   ├── facturas
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── contabilidad_service.cpython-312.pyc
│   │   │   │   ├── parser_xml_service.cpython-312.pyc
│   │   │   │   ├── tipo_cambio_service.cpython-312.pyc
│   │   │   │   └── validacion_service.cpython-312.pyc
│   │   │   ├── contabilidad_service.py
│   │   │   ├── impuestos_service.py
│   │   │   ├── parser_xml_service.py
│   │   │   ├── tipo_cambio_service.py
│   │   │   └── validacion_service.py
│   │   ├── fel
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   └── context.cpython-312.pyc
│   │   │   ├── context.py
│   │   │   └── strategies
│   │   │       ├── __init__.py
│   │   │       ├── __pycache__
│   │   │       │   ├── __init__.cpython-312.pyc
│   │   │       │   ├── base.cpython-312.pyc
│   │   │       │   ├── pdf_strategy.cpython-312.pyc
│   │   │       │   ├── pdf_text_parser.cpython-312.pyc
│   │   │       │   └── xml_strategy.cpython-312.pyc
│   │   │       ├── base.py
│   │   │       ├── pdf_strategy.py
│   │   │       ├── pdf_text_parser.py
│   │   │       └── xml_strategy.py
│   │   └── sat
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   ├── __init__.cpython-312.pyc
│   │       │   ├── casilla_service.cpython-312.pyc
│   │       │   ├── declaraciones_service.cpython-312.pyc
│   │       │   ├── formulario_service.cpython-312.pyc
│   │       │   ├── regimen_dte_service.cpython-312.pyc
│   │       │   ├── regimen_fiscal_service.cpython-312.pyc
│   │       │   ├── regla_filtrado_service.cpython-312.pyc
│   │       │   ├── sat_libros_service.cpython-312.pyc
│   │       │   ├── seccion_service.cpython-312.pyc
│   │       │   └── tipo_dte_service.cpython-312.pyc
│   │       ├── actividad_economica_service.py
│   │       ├── casilla_service.py
│   │       ├── categoria_activo_service.py
│   │       ├── declaraciones_service.py
│   │       ├── formulario_service.py
│   │       ├── geografia_service.py
│   │       ├── mapeo_casilla_service.py
│   │       ├── moneda_service.py
│   │       ├── regimen_dte_service.py
│   │       ├── regimen_fiscal_service.py
│   │       ├── regla_filtrado_service.py
│   │       ├── sat_libros_service.py
│   │       ├── seccion_service.py
│   │       ├── tipo_dte_service.py
│   │       └── tipo_persona_service.py
│   └── utils
│       ├── __init__.py
│       └── excel_handler.py
├── create_tenant_tables.sql
├── db
│   ├── 0NiM1ouoHaN67SRO2IzXZ5RNI7FeyHpn.xls
│   ├── INE_Geografia_Guatemala.xlsx
│   ├── Saldos_Cuentas.sql
│   ├── catalogo_monedas.csv
│   ├── create_tenant_tables.sql
│   ├── drop_public_tables.sql
│   ├── fastconta_20260527_1640.sql
│   ├── transfer_schema_ownership.sql
│   └── update_fk_tenants.sql
├── debug_routes.py
├── drop_public_tables.sql
├── estructura.md
├── init_test_data.py
├── manage.py
├── migracion.sql
├── requirements.txt
├── requirements.txt.bak
├── seed_actividades_economicas.py
├── seed_data_ine.py
├── seed_partidas.py
├── seed_periodo_fiscal.py
├── seed_plan_cuentas.py
├── seed_regimenes_fiscales.py
├── test_xml_parse.py
└── tests
    └── __init__.py

78 directories, 425 files
```
