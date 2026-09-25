# device_systems

API REST `device_systems` construida con **FastAPI, SQLAlchemy 2, SQLite, Alembic y Pydantic v2**.
Gestiona usuarios, dispositivos tecnológicos y préstamos con relaciones, integridad referencial y
consultas con joins, e incorpora una capa completa de seguridad: **hash de contraseñas con passlib,
autenticación OAuth2 + JWT, autorización por roles, middleware de trazabilidad, CORS y rate limiting**.

- Versión actual: `3.0.0` (actividad `GA1-220501096-01-AA1-EV11 – FastAPI Seguridad`).
- Rama de trabajo: `device_systems_security` (se integra a `main` siguiendo Git Flow).

## Requisitos

- Python 3.10 o superior
- Git
- SQLite (incluido con Python)

## Instalación y ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env        # ajustar SECRET_KEY antes de usarlo
python -m alembic upgrade head     # crea device_systems.db y aplica las migraciones
uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs> (botón **Authorize** para OAuth2)
- ReDoc: <http://127.0.0.1:8000/redoc>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

## Variables de entorno (`.env.example`)

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `SECRET_KEY` | Clave con la que se firman los JWT (HS256) | clave de desarrollo (cambiar) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del access token en minutos | `30` |
| `ALLOWED_ORIGINS` | Orígenes CORS autorizados, separados por coma | `http://localhost:5173,http://localhost:3000` |

El archivo `.env` está en `.gitignore`: los secretos nunca se suben al repositorio.

## Estructura del proyecto

```text
device_systems/
|-- app/
|   |-- main.py                        # FastAPI, tags, CORS, rate limiting y middlewares
|   |-- auth/
|   |   |-- auth_routes.py             # POST /auth/register, POST /auth/login, GET /auth/me
|   |   |-- auth_service.py            # Registro y autenticación de credenciales
|   |   `-- security.py                # Hash passlib + creación/validación de JWT
|   |-- docs/
|   |   `-- swagger_es.py              # Traducción al español de la interfaz de /docs
|   |-- errors/
|   |   |-- handlers.py                # Errores 401, 404, 422 y 429 con mensajes en español
|   |   `-- mensajes_es.py             # Diccionarios de traducción de mensajes
|   |-- database/
|   |   `-- connection.py              # Engine, SessionLocal y Base de SQLAlchemy
|   |-- models/                        # user_model.py, device_model.py, loan_model.py
|   |-- schemas/                       # Pydantic v2: user, device, loan, auth, security
|   |-- routes/                        # user_routes.py, device_routes.py, loan_routes.py,
|   |                                  # security_routes.py
|   |-- services/                      # Lógica de negocio y consultas con joins
|   |-- dependencies/
|   |   |-- database_dependency.py     # get_db
|   |   `-- auth_dependency.py         # get_current_user, get_current_active_user,
|   |                                  # require_admin, require_staff, require_roles
|   `-- middlewares/
|       |-- request_middleware.py      # Tiempo, X-Request-ID, cabeceras y logging
|       `-- rate_limiter.py            # Limiter de slowapi y límites por endpoint
|-- alembic/
|   |-- env.py                         # Carga Base.metadata y los tres modelos
|   `-- versions/                      # 0001_initial, eaf5bb584fec, 6f13097d5c18,
|                                      # a2c51e9d043b (campos de autenticación)
|-- tests/                             # test_users.py, test_devices_loans.py, test_security.py
|-- scripts/create_admin.py            # Bootstrap del usuario admin para pruebas
|-- captures/                          # Evidencias en imágenes
|-- alembic.ini
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Seguridad implementada

### 1. Validaciones avanzadas con Pydantic v2

- `model_config = ConfigDict(from_attributes=True)` en todos los schemas de respuesta para leer objetos SQLAlchemy.
- `model_config = ConfigDict(extra="forbid")` en `UserRegister`: rechaza campos no declarados (por ejemplo `role`).
- `Field()` con `min_length`, `max_length`, `description` y `examples` en los schemas.
- `field_validator` para la política de contraseñas y el saneamiento del nombre.
- `model_validator(mode="after")` en `UserRegister` para impedir contraseñas que contengan el correo o el nombre del usuario.
- `hashed_password` no existe en ningún response model: la API nunca devuelve el hash.

### 2. Hash de contraseñas con passlib

`app/auth/security.py` centraliza `get_password_hash`, `verify_password`, `create_access_token` y
`decode_access_token` usando `CryptContext(schemes=["bcrypt_sha256"])`. Ninguna contraseña se guarda
ni se devuelve en texto plano; en la base de datos solo se almacena el hash.

> Nota: se fija `bcrypt>=4.0,<4.1` porque passlib 1.7.4 no inicializa su backend con bcrypt 4.1 o
> superior (internamente prueba una contraseña de más de 72 bytes y esas versiones lanzan `ValueError`).

### 3. Autenticación OAuth2 con JWT

- `POST /auth/login` recibe el formulario OAuth2 (`username` = email, `password` = contraseña).
- Se verifica la contraseña contra el hash y se responde `{"access_token": "...", "token_type": "bearer"}`.
- El token incluye `sub` (id del usuario), `role` y `exp` (30 minutos por defecto) y se firma con HS256.
- `decode_access_token` valida firma y expiración; cualquier token inválido produce `401 Unauthorized`.
- En Swagger UI el botón **Authorize** completa el flujo `password` contra `/auth/login`.

### 4. Protección de rutas y autorización por roles

Dependencias de `app/dependencies/auth_dependency.py`:

| Dependencia | Comportamiento |
| --- | --- |
| `get_current_user` | Decodifica el JWT de `Authorization: Bearer <token>` y carga el usuario. Sin token o token inválido → `401` |
| `get_current_active_user` | Además exige `is_active = True`; en caso contrario → `403` |
| `require_admin` | Solo rol `admin`; otro rol → `403` |
| `require_staff` | Roles `admin` o `support`; otro rol → `403` |
| `require_roles("a", "b")` | Fábrica reutilizable para exigir cualquiera de los roles indicados |

Matriz de protección aplicada:

| Ruta | Protección requerida |
| --- | --- |
| `GET /users` | Usuario autenticado |
| `GET /users/{user_id}` | Usuario autenticado |
| `GET /users/{user_id}/loans` | Usuario autenticado (rol `user` solo el propio) |
| `POST /users`, `PUT`, `PATCH /users/{id}` | `admin` o `support` |
| `DELETE /users/{user_id}` | `admin` |
| `GET /devices`, `GET /devices/{device_id}` | Usuario autenticado |
| `POST /devices`, `PUT`, `PATCH /devices/{id}` | `admin` o `support` |
| `DELETE /devices/{device_id}` | `admin` |
| `POST /loans` | Usuario autenticado (rol `user` solo para sí mismo) |
| `GET /loans`, `GET /loans/details`, `GET /loans/{loan_id}` | `admin` o `support` |
| `PATCH /loans/{loan_id}/return` | `admin` o `support` |
| `GET /auth/me` | Usuario autenticado |
| `GET /`, `GET /security/policy` | Público |

Códigos de error de seguridad: `401 Unauthorized` si falta el token o es inválido/expirado,
`403 Forbidden` si el usuario existe pero no tiene el rol requerido.

### 5. Middleware personalizado

`app/middlewares/request_middleware.py` se registra con `app.middleware("http")` y en cada petición:

1. Mide el tiempo de proceso con `time.perf_counter()`.
2. Genera un `X-Request-ID` nuevo (UUID) o propaga el enviado por el cliente si tiene formato válido.
3. Agrega las cabeceras `X-Process-Time`, `X-App-Name`, `X-Request-ID`, `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy`.
4. Registra en el log método, ruta, código de estado, duración, request id y cliente.

```text
X-App-Name: device_systems
X-Process-Time: 0.0042
X-Request-ID: 8f42e9c1-...
X-Content-Type-Options: nosniff
```

### 6. CORS

`main.py` registra `CORSMiddleware` con `allow_origins` tomado de `ALLOWED_ORIGINS`
(`http://localhost:5173` y `http://localhost:3000` en desarrollo), `allow_credentials=True`,
`allow_methods=["*"]` y `allow_headers=["*"]`.

**¿Por qué no se recomienda `"*"` en producción cuando hay credenciales?**
Con `allow_credentials=True` el origen autorizado debe ser explícito: si se responde
`Access-Control-Allow-Origin: *` junto con `Access-Control-Allow-Credentials: true`, el navegador bloquea la
petición por política de CORS. Además, el comodín permitiría que cualquier sitio hiciera peticiones
autenticadas con las credenciales del usuario (riesgo de CSRF y robo de sesión). En producción se debe
listar únicamente el dominio real del frontend, limitar los métodos permitidos y restringir cabeceras.

### 7. Rate limiting

Configurado con **slowapi** (`app/middlewares/rate_limiter.py`), con la IP del cliente como clave y
cabeceras `X-RateLimit-*` / `Retry-After` habilitadas. Al superar el cupo la API responde
`429 Too Many Requests` mediante el manejador `RateLimitExceeded`.

| Endpoint | Límite |
| --- | --- |
| `POST /auth/login` | 5 solicitudes por minuto |
| `POST /auth/register` | 3 solicitudes por minuto |
| `GET /users` | 30 solicitudes por minuto |
| `POST /loans` | 10 solicitudes por minuto |

### 8. Migración de Alembic para los campos de autenticación

```powershell
python -m alembic revision --autogenerate -m "add authentication fields to users"
python -m alembic upgrade head
```

La migración `a2c51e9d043b_add_authentication_fields_to_users.py` agrega `users.hashed_password`
(`String(255)`, obligatorio); la tabla `users` queda como
`id, name, email, role, is_active, created_at, hashed_password`.

## Idioma de la API y de la documentación

Todo el texto que ve un cliente de la API está en español:

- **Mensajes de error**: `app/errors/handlers.py` y `app/errors/mensajes_es.py` traducen los mensajes
  que FastAPI, Pydantic y slowapi generan en inglés. Por ejemplo, un `401` responde
  `{"detail": "No autenticado: envía el token en la cabecera 'Authorization: Bearer <token>'"}` y un `422`
  responde `{"detail": "Los datos enviados no son válidos", "errores": [{"campo": "password", "mensaje": "Debe tener al menos 8 caracteres"}]}`.
- **Interfaz de Swagger UI (`/docs`)**: Swagger UI es una librería de terceros publicada solo en inglés
  (no ofrece opciones de idioma). `app/docs/swagger_es.py` sirve la página `/docs` con una capa de traducción
  que cambia las etiquetas de la interfaz —incluido el diálogo **Authorize → Autorizar**— y respeta los
  bloques de código y los ejemplos, que nunca se traducen para no alterar los nombres reales del contrato.
- **Títulos, descripciones, `summary` y `response_description`** de todos los endpoints y schemas están redactados en español.
- **README, `.env.example`, comentarios y docstrings** están en español.

Se mantienen en inglés, por convención técnica, los **identificadores de código** (clases como `UserRegister`
o `LoanDetailResponse`, funciones como `get_password_hash` o `require_admin`, tablas y columnas como `users`
o `hashed_password`), porque la guía de la actividad los define así y hacen parte del contrato de la API;
también permanecen en inglés las frases estándar de los códigos HTTP y la interfaz de ReDoc (`/redoc`),
que tampoco permite traducción.

## Endpoints

### Autenticación (`Auth`)

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/auth/register` | Registra un usuario activo con rol `user` y contraseña hasheada |
| POST | `/auth/login` | Valida credenciales y devuelve el JWT (`access_token`, `token_type`) |
| GET | `/auth/me` | Devuelve el usuario autenticado sin `hashed_password` |

### Usuarios (`Users`)

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/users` | Crea un usuario (admin/support) |
| GET | `/users` | Lista y filtra por `role`, `is_active` y `order_by` |
| GET | `/users/{user_id}` | Consulta un usuario |
| GET | `/users/{user_id}/loans` | Historial de préstamos del usuario (join) |
| PUT | `/users/{user_id}` | Reemplaza todos los datos editables |
| PATCH | `/users/{user_id}` | Actualiza solo los campos enviados |
| DELETE | `/users/{user_id}` | Elimina un usuario (admin) y responde 204 |


### Dispositivos (`Devices`)

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/devices` | Crea un dispositivo (admin/support) |
| GET | `/devices` | Lista y filtra por tipo, marca, disponibilidad o nombre |
| GET | `/devices/{device_id}` | Consulta un dispositivo |
| PUT/PATCH | `/devices/{device_id}` | Actualiza un dispositivo (admin/support) |
| DELETE | `/devices/{device_id}` | Elimina un dispositivo sin historial (admin) |
| GET | `/devices/{device_id}/loans` | Historial de préstamos del dispositivo |

### Préstamos (`Loans`)

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/loans` | Crea un préstamo y marca el dispositivo como no disponible |
| GET | `/loans` | Lista préstamos con filtros por estado, correo y tipo (admin/support) |
| GET | `/loans/details` | Lista préstamos con los objetos `user` y `device` anidados (admin/support) |
| GET | `/loans/{loan_id}` | Consulta un préstamo con usuario y dispositivo |
| PATCH | `/loans/{loan_id}/return` | Registra la devolución y libera el dispositivo (admin/support) |

### Seguridad (`Security`)

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/` | Estado de la API |
| GET | `/security/policy` | Política de seguridad activa: CORS, límites, cabeceras y rutas protegidas |

Los tags de Swagger son `Auth`, `Users`, `Devices`, `Loans` y `Security`. Cada endpoint documenta
`summary`, `description`, `response_description` y los códigos esperados; los schemas incluyen `examples`.
Roles permitidos: `admin`, `support` y `user`. El nombre requiere mínimo 3 caracteres, el email debe tener
formato válido y es único. Error de recurso inexistente: `404`; dato duplicado: `400`; regla de negocio
incumplida: `409`; validación: `422`; límite superado: `429`.

## Modelo y schemas

`User`, `Device` y `Loan` son los modelos SQLAlchemy con `relationship()` y `back_populates`. Los schemas
Pydantic v2 (`user_schema.py`, `device_schema.py`, `loan_schema.py`, `auth_schema.py`, `security_schema.py`)
validan las entradas, controlan las salidas con `from_attributes=True` y garantizan que `hashed_password`
nunca se exponga.


## Evidencias de captura para la entrega

La carpeta [captures](captures) guarda la evidencia del proyecto. Las evidencias de la actividad anterior
(estructura, migraciones, CRUD y joins) se conservan; las nuevas evidencias de seguridad van del `16` al `28`.

### Parte 1 – migraciones, relaciones y joins (actividad anterior)

- [captures/01_alembic_init.png](captures/01_alembic_init.png) - Inicialización de Alembic.
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

### Parte 2 – seguridad (esta actividad)

| # | Archivo | Evidencia |
| --- | --- | --- |
| 16 | `16_estructura_proyecto.png` | Estructura de carpetas del proyecto con `app/auth`, `app/middlewares`, `app/dependencies` |
| 17 | `17_alembic_upgrade_head_auth.png` | `python -m alembic upgrade head` aplicando `a2c51e9d043b` + `alembic current` |
| 18 | `18_swagger_oauth2.png` | Swagger UI con el botón **Authorize** (OAuth2 password flow) y los tags Auth/Users/Devices/Loans/Security |
| 19 | `19_register_usuario.png` | `POST /auth/register` con respuesta `201` |
| 20 | `20_login_token.png` | `POST /auth/login` mostrando `access_token` y `token_type: bearer` |
| 21 | `21_auth_me.png` | `GET /auth/me` con el token en `Authorization: Bearer` |
| 22 | `22_acceso_sin_token.png` | Ruta protegida sin token → `401 Unauthorized` |
| 23 | `23_acceso_rol_no_permitido.png` | Usuario con rol `user` intentando `DELETE /devices/{id}` → `403 Forbidden` |
| 24 | `24_middleware_headers.png` | Cabeceras `X-App-Name`, `X-Process-Time`, `X-Request-ID` en la respuesta |
| 25 | `25_rate_limiting_429.png` | Varias llamadas a `/auth/login` y la última con `429 Too Many Requests` |
| 26 | `26_hash_en_base_de_datos.png` | Contenido de `users.hashed_password` mostrando el hash (nunca texto plano) |
| 27 | `27_cors_preflight.png` | Petición `OPTIONS` con `Origin: http://localhost:5173` y cabeceras `Access-Control-Allow-*` |
| 28 | `28_pruebas_pytest.png` | Salida de `pytest -q` con todas las pruebas en verde |


### Cómo preparar el entorno para las capturas

```powershell
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Crear un usuario administrador inicial (bootstrap) para poder grabar dispositivos y usuarios:

```powershell
python -m scripts.create_admin
```

Crea `admin@sena.edu.co` / `AdminSeguro123` con rol `admin`. Se pueden pasar otros datos:

```powershell
python -m scripts.create_admin admin2@sena.edu.co OtraClaveSegura123 "Admin Dos"
```

### Cómo tomar cada captura de la parte 2

| # | Procedimiento |
| --- | --- |
| 16 | En VS Code abre el explorador de archivos y expande `app/` mostrando `auth`, `middlewares`, `dependencies` y `schemas` |
| 17 | Terminal: `python -m alembic upgrade head` y luego `python -m alembic current` (debe mostrar `a2c51e9d043b (head)`) |
| 18 | Navegador en <http://127.0.0.1:8000/docs>: captura el botón **Authorize** abierto y los tags Auth, Users, Devices, Loans y Security |
| 19 | Swagger `POST /auth/register` → *Try it out* con `{"name":"Ana Torres","email":"aprendiz@sena.edu.co","password":"ClaveSegura123"}` → respuesta `201` |
| 20 | Swagger **Authorize** con `aprendiz@sena.edu.co` / `ClaveSegura123`, o `POST /auth/login`; captura el `access_token` y `token_type: bearer` |
| 21 | Swagger `GET /auth/me` con el token autorizado → respuesta `200` sin `hashed_password` |
| 22 | `curl.exe -s -i http://127.0.0.1:8000/users` → `401` con `{"detail":"No autenticado: envía el token en la cabecera 'Authorization: Bearer <token>'"}` |
| 23 | Autoriza Swagger con el token del rol `user` y ejecuta `DELETE /devices/1` → `403 Forbidden` |
| 24 | `curl.exe -s -D - -o NUL http://127.0.0.1:8000/` → muestra `X-App-Name`, `X-Process-Time` y `X-Request-ID` |
| 25 | `1..6 \| % { curl.exe -s -o NUL -w "%{http_code}`n" -X POST http://127.0.0.1:8000/auth/login -d "username=aprendiz@sena.edu.co&password=Mal123" }` → cinco `401` y un `429` |
| 26 | `python -c "import sqlite3; print(list(sqlite3.connect('device_systems.db').execute('select id, email, hashed_password from users')))"` |
| 27 | `curl.exe -s -D - -o NUL -X OPTIONS http://127.0.0.1:8000/users -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: GET"` |
| 28 | Terminal: `pytest -q` con las 17 pruebas en verde y sus nombres en español |

> Importante: cada captura debe mostrar el comando o endpoint usado y su respuesta con el código HTTP visible.

## Pruebas

```powershell
pytest -q
```

Escenarios cubiertos por la suite (`tests/`):

1. Registro de usuario (`201`) y respuesta sin `hashed_password`.
2. Registro con contraseña débil (`422`, incluida la variante que contiene el correo).
3. Registro con email duplicado (`400`).
4. Login correcto con token JWT.
5. Login con contraseña incorrecta (`401`).
6. Consulta de `/auth/me` con el token (`200`).
7. Acceso a rutas protegidas sin token (`401`) y con token inválido (`401`).
8. Acceso con usuario sin permisos (`403` en `/loans`, `/loans/details` y `DELETE /devices/{id}`).
9. Creación de dispositivo con rol permitido (`201`).
10. Eliminación de dispositivo con rol no permitido (`403`).
11. Cabeceras del middleware (`X-App-Name`, `X-Process-Time`, `X-Request-ID`, cabeceras de seguridad).
12. CORS: preflight `OPTIONS` con origen autorizado.
13. Rate limiting en `/auth/register` y `/auth/login` (`429` + `Retry-After`).
14. CRUD de usuarios, filtros, préstamos, joins y devoluciones de la actividad anterior.
15. Endpoint `/security/policy` con la política de seguridad vigente.
16. Mensajes de error y de validación en español (`401`, `404` y `422`).

## Migraciones

La configuración está en `alembic.ini`, el entorno carga `Base.metadata` desde los tres modelos y la
carpeta `alembic/versions` contiene:

| Revisión | Descripción |
| --- | --- |
| `0001_initial` | Crea `users`, `devices` y `loans` con índices y claves foráneas |
| `eaf5bb584fec` | Índices únicos de `users.email` y `devices.serial_number` |
| `6f13097d5c18` | Revisión intermedia sin cambios estructurales |
| `a2c51e9d043b` | Agrega `users.hashed_password` (campos de autenticación) |

```powershell
python -m alembic history
python -m alembic current
```


## Flujo Git de la actividad (Git Flow)

Ramas del repositorio:

- `main`: versión estable entregada.
- `develop`: integración de las actividades.
- `device_systems_alembic_relaciones`: actividad anterior (ya integrada a `main`).
- `device_systems_security`: rama de esta actividad, que debe unificarse con `main`.

```powershell
git switch main
git pull origin main
git switch -c device_systems_security     # o: git switch device_systems_security
git add .
git commit -m "feat: seguridad oauth2 jwt cors middleware y rate limiting"
git push -u origin device_systems_security

# integración siguiendo Git Flow
git switch develop
git merge --no-ff device_systems_security
git switch main
git merge --no-ff develop
git push origin main
```

## Reflexión final sobre la seguridad en APIs REST

Construir un CRUD funcional no es suficiente: una API REST sin controles expone datos y permite abuso.
Con esta actividad entendí que la seguridad se aplica en capas y todas son necesarias:

- **Contraseñas**: guardarlas en texto plano es el error más grave; con passlib y `bcrypt_sha256` el hash es
  irreversible y se compara sin revelar el valor original. Además, una política mínima de complejidad y
  `model_validator` evitan contraseñas predecibles o basadas en datos del usuario.
- **Autenticación**: el flujo OAuth2 con JWT entrega credenciales temporales (con expiración) en lugar de
  enviar usuario y contraseña en cada petición; el token se firma, por lo que no puede alterarse sin la
  `SECRET_KEY`.
- **Autorización**: cada endpoint declara quién puede usarlo. Separar `get_current_user`,
  `get_current_active_user`, `require_admin` y `require_staff` hace explícito el modelo de permisos y
  responde `401` o `403` de forma coherente.
- **Validación**: Pydantic v2 filtra la entrada antes de tocar la base de datos, impide campos extra
  (como `role` en el registro) y garantiza que el hash nunca salga en una respuesta.
- **Trazabilidad y observabilidad**: el middleware con `X-Request-ID`, tiempo de respuesta y logs permite
  auditar y depurar cada petición; las cabeceras de seguridad endurecen el cliente.
- **CORS**: abrir `*` con credenciales es una puerta abierta; solo se autorizan los orígenes del frontend.
- **Rate limiting**: limita el abuso y los ataques de fuerza bruta contra `/auth/login`, devolviendo `429`.

La conclusión es que la seguridad no es un módulo que se agrega al final: es un conjunto de decisiones
que atraviesan el modelo de datos, los schemas, las rutas, las dependencias y la configuración del
servidor, y que deben verificarse con pruebas funcionales.
