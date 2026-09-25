# device_systems

API REST `device_systems` construida con FastAPI, SQLAlchemy 2, SQLite y Alembic. Gestiona usuarios, dispositivos tecnológicos y préstamos con relaciones, integridad referencial y consultas con joins.

## Requisitos

- Python 3.10 o superior
- Git
- Alembic

## Instalación y ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Para crear la base de datos mediante migraciones:
|   |-- database/connection.py
|   |-- dependencies/database_dependency.py
|   |-- models/user_model.py, device_model.py, loan_model.py
|   |-- routes/user_routes.py, device_routes.py, loan_routes.py
|   |-- schemas/user_schema.py, device_schema.py, loan_schema.py
|   |-- services/user_service.py, device_service.py, loan_service.py
|   `-- main.py
|-- alembic/
|   |-- versions/0001_initial_device_systems.py
|   |-- env.py
|   `-- script.py.mako
|-- alembic.ini

|-- tests/test_devices_loans.py
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Estructura

```text
device_systems/
|-- app/
|   |-- database/connection.py
|   |-- dependencies/database_dependency.py
|   |-- models/user_model.py
|   |-- routes/user_routes.py
|   |-- schemas/user_schema.py
|   |-- services/user_service.py
|   `-- main.py
|-- tests/test_users.py
|-- requirements.txt
`-- README.md
```

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/users` | Crea un usuario |
| GET | `/users` | Lista y filtra por `role`, `is_active` y `order_by` |
| GET | `/users/{user_id}` | Consulta un usuario |
| PUT | `/users/{user_id}` | Reemplaza todos los datos editables |
| PATCH | `/users/{user_id}` | Actualiza solo los campos enviados |
| DELETE | `/users/{user_id}` | Elimina un usuario y responde 204 |

### Dispositivos

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/devices` | Crea un dispositivo |
| GET | `/devices` | Lista y filtra por tipo, marca, disponibilidad o nombre |
| GET | `/devices/{device_id}` | Consulta un dispositivo |
| PUT/PATCH | `/devices/{device_id}` | Actualiza un dispositivo |
| DELETE | `/devices/{device_id}` | Elimina un dispositivo sin historial |
| GET | `/devices/{device_id}/loans` | Consulta el historial del dispositivo |

### Préstamos

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/loans` | Crea un préstamo y marca el dispositivo como no disponible |
| GET | `/loans` | Lista préstamos con filtros por estado, correo y tipo |
| GET | `/loans/{loan_id}` | Consulta un préstamo con usuario y dispositivo |
| PATCH | `/loans/{loan_id}/return` | Registra la devolución y libera el dispositivo |
| GET | `/users/{user_id}/loans` | Consulta los préstamos del usuario |

Los tags de Swagger son `Users`, `Devices` y `Loans`. La respuesta de los préstamos incluye los datos relacionados del usuario y del dispositivo.

Roles permitidos: `admin`, `support` y `user`. El nombre requiere mínimo 3 caracteres, el email debe tener formato válido y es único. Los errores de usuario inexistente responden 404, el email repetido 400 y los datos inválidos 422.

## Modelo y schemas

`User` es el modelo SQLAlchemy que representa la tabla `users` y sus constraints en SQLite. `UserCreate`, `UserUpdate`, `UserPatch` y `UserResponse` son schemas Pydantic: validan los datos que entran y controlan la forma de los datos que salen de la API. Separarlos evita exponer directamente la estructura de persistencia.

## Evidencias de captura para la entrega

La carpeta [captures](captures) guarda la evidencia final del proyecto. Aquí están las imágenes ya organizadas con los nombres definitivos para la entrega.

### Capturas principales

- [captures/01_alembic_init.png](captures/01_alembic_init.png) - Captura de la inicialización de Alembic.
- [captures/02_alembic_revision_autogenerate.png](captures/02_alembic_revision_autogenerate.png) - Generación de la migración.
- [captures/03_alembic_upgrade_head.png](captures/03_alembic_upgrade_head.png) - Aplicación de la migración.
- [captures/04_alembic_history.png](captures/04_alembic_history.png) - Historial de Alembic.
- [captures/05_swagger_docs.png](captures/05_swagger_docs.png) - Swagger UI del proyecto.
- [captures/06_redoc.png](captures/06_redoc.png) - Documentación ReDoc.
- [captures/07_crear_usuario.png](captures/07_crear_usuario.png) - Creación de usuario.
- [captures/08_crear_dispositivo.png](captures/08_crear_dispositivo.png) - Creación de dispositivo.
- [captures/09_crear_prestamo.png](captures/09_crear_prestamo.png) - Creación de préstamo.
- [captures/10_listar_prestamos_join.png](captures/10_listar_prestamos_join.png) - Consulta con joins.
- [captures/11_filtro_estado.png](captures/11_filtro_estado.png) - Filtro por estado.
- [captures/12_filtro_tipo_dispositivo.png](captures/12_filtro_tipo_dispositivo.png) - Filtro por tipo de dispositivo.
- [captures/13_prestamos_usuario.png](captures/13_prestamos_usuario.png) - Historial de préstamos del usuario.
- [captures/14_devolucion_dispositivo.png](captures/14_devolucion_dispositivo.png) - Devolución del préstamo.
- [captures/15_dispositivo_disponible.png](captures/15_dispositivo_disponible.png) - Verificación de disponibilidad del dispositivo.
- [captures/api_evidence.json](captures/api_evidence.json) - Evidencia JSON de la API con resultados reales.

### Orden recomendado para la presentación

1. `01_alembic_init.png`
2. `02_alembic_revision_autogenerate.png`
3. `03_alembic_upgrade_head.png`
4. `04_alembic_history.png`
5. `05_swagger_docs.png`
6. `06_redoc.png`
7. `07_crear_usuario.png`
8. `08_crear_dispositivo.png`
9. `09_crear_prestamo.png`
10. `10_listar_prestamos_join.png`
11. `11_filtro_estado.png`
12. `12_filtro_tipo_dispositivo.png`
13. `13_prestamos_usuario.png`
14. `14_devolucion_dispositivo.png`
15. `15_dispositivo_disponible.png`

### Cómo tomar cada captura

- Abre la terminal y ejecuta el comando correspondiente.
- Toma la pantalla completa de la ventana de PowerShell o terminal.
- Para Swagger y ReDoc, abre la ruta en el navegador y captura la vista completa.
- Para las peticiones de la API, usa Swagger UI y toma la respuesta con el código HTTP visible.
- Guarda cada imagen en la carpeta [captures](captures) con el nombre indicado arriba.

> Importante: la evidencia final debe mostrar claramente el comando ejecutado o el endpoint validado, con su respuesta correspondiente.

## Pruebas

```powershell
pytest -q
```

Las pruebas cubren creación, consulta, filtros, PUT, PATCH, DELETE, email y serial duplicados, validaciones, respuestas 404, préstamo no disponible, joins, historiales y devolución.

## Migraciones

La configuración de Alembic está en `alembic.ini`, el entorno carga `Base.metadata` desde los tres modelos y `alembic/versions/0001_initial_device_systems.py` crea las tablas `users`, `devices` y `loans`, incluyendo índices y claves foráneas.

## Flujo Git de la actividad

La actividad se entrega mediante la rama `device_systems_alembic_relaciones`, integrada posteriormente a `main`.

```powershell
git switch main
git switch -c develop
git switch -c device_systems_alembic_relaciones
git add .
git commit -m "feat: integrar alembic relaciones y prestamos"
git switch develop
git merge --no-ff device_systems_alembic_relaciones
git switch main
git merge --no-ff develop
git push -u origin main
```

La rama de trabajo contiene la implementación de la guía y debe unificarse con `main` después de revisar las pruebas.