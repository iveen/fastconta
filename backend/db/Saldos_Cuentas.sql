--- Cuentas de Resultados
SELECT c.codigo, c.nombre,
       COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0) AS sum_debe,
       COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0) AS sum_haber,
       CASE WHEN c.naturaleza = 'deudora' THEN
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0)
       ELSE
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0)
       END AS saldo
FROM tenant_contaguate.plan_cuentas c
LEFT JOIN tenant_contaguate.detalle_partidas d ON d.cuenta_id = c.id
WHERE c.empresa_id = '4c79a36b-7bb7-41bf-bd2d-3e78fe3568e3'
  AND c.tipo IN ('ingreso', 'gasto')
GROUP BY c.id
ORDER BY c.codigo;

--- Cuentas de Patrimonio
SELECT c.codigo, c.nombre,
       COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0) AS sum_debe,
       COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0) AS sum_haber,
       CASE WHEN c.naturaleza = 'deudora' THEN
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0)
       ELSE
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'haber' THEN d.monto ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN d.tipo_movimiento = 'debe' THEN d.monto ELSE 0 END), 0)
       END AS saldo
FROM tenant_contaguate.plan_cuentas c
LEFT JOIN tenant_contaguate.detalle_partidas d ON d.cuenta_id = c.id
WHERE c.empresa_id = '4c79a36b-7bb7-41bf-bd2d-3e78fe3568e3'
  AND (c.codigo IN ('3.4', '3.3.1') OR c.tipo IN ('activo', 'pasivo'))
GROUP BY c.id;

