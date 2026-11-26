# Plataforma de alojamientos

Aplicación web de gestión para dueños de cabañas, departamentos y casas de alquiler temporario. Cada dueño administra sus propios complejos, alojamientos, reservas, pagos, inventario y reportes; la plataforma no ofrece reservas públicas.

## Estado del MVP

La primera etapa cubre cuentas de dueños con cambio obligatorio de contraseña inicial y el catálogo de complejos y alojamientos. Las siguientes etapas agregarán calendario y reservas, precios configurables, cobros en varias monedas con cotización oficial BCRA, gastos, inventario y reportes.

## Desarrollo local

Requiere Python 3.12+ y usa SQLite para desarrollo. PostgreSQL se configura mediante `DATABASE_URL` para despliegue.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Entrá a `/admin/` con la cuenta administrativa y después a `/plataforma/cuentas/` para crear el acceso inicial de cada dueño. La contraseña temporal debe cambiarse al primer ingreso.

No agregues credenciales reales al repositorio. Usá variables de entorno para los secretos de despliegue.
