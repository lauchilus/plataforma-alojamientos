# Plataforma de alojamientos

Aplicación web de gestión para que distintos dueños administren cabañas, departamentos y casas desde cuentas separadas. No recibe reservas públicas: cada dueño carga sus huéspedes y reservas.

## MVP implementado en esta rama

- Administración de cuentas con contraseña inicial y cambio obligatorio al primer ingreso.
- Complejos y alojamientos con capacidad, dormitorios, camas, tamaño y tarifa base.
- Reglas de precios por alojamiento, huéspedes, períodos y mínimo de noches; precio sugerido editable en cada reserva.
- Calendario mensual y reservas manuales con control de superposición, huéspedes, pagos y saldo.
- Pagos parciales en varias monedas y medios. Las conversiones consultan el BCRA y guardan cotización, fecha y fuente.
- Gastos particulares o generales, con opción de distribuir gastos generales entre alojamientos.
- Inventario configurable; movimientos de blanquería por estadía para entregas limpias, reposiciones, retiros de usadas, limpieza, daños y faltantes.
- Informes de cobros, gastos, resultado neto, ocupación y resultados por alojamiento.

## Ejecutar localmente

Requiere Python 3.12+. SQLite se usa para desarrollo local y PostgreSQL para despliegue.

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Con la cuenta administrativa, abrí /plataforma/cuentas/ para crear accesos iniciales de dueños. Cada dueño debe cambiar su contraseña al ingresar.

## PostgreSQL y configuración

Definí DATABASE_URL con formato postgresql://usuario:clave@host:5432/base. Para proveedores que requieren SSL, definí DATABASE_SSL=true. Copiá .env.example a .env, completá DJANGO_SECRET_KEY y DJANGO_ALLOWED_HOSTS, y configurá DJANGO_DEBUG=false en producción.

Cada dueño elige la moneda de referencia y la serie del BCRA desde Configuración. Las cotizaciones aplicadas quedan guardadas; cambios posteriores no reescriben operaciones anteriores.

## Verificaciones

GitHub Actions ejecuta el chequeo de Django, comprueba que las migraciones estén sincronizadas y corre las pruebas automatizadas.
