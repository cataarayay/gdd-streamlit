# GDD ACHS — Streamlit

Dashboard de accidentabilidad y cobertura con login por roles.

## Deploy en Streamlit Community Cloud (3 pasos)

1. Sube esta carpeta a un repo en GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu GitHub
3. Selecciona el repo → archivo `app.py` → Deploy

Tu app queda en: `https://tuapp.streamlit.app`

## Gestión de usuarios

Editar `setup_users.py` con los usuarios nuevos y correr:
```bash
python setup_users.py
```
Luego subir el `config_usuarios.yaml` actualizado a GitHub.

## Actualizar datos

1. Login como admin
2. Ir a ⚙️ Cargar datos
3. Subir el CSV nuevo → Confirmar

## Archivos
```
gdd-streamlit/
├── app.py                  # App completa (un solo archivo)
├── setup_users.py          # Script para crear usuarios
├── config_usuarios.yaml    # Usuarios y contraseñas
├── requirements.txt        # Dependencias
└── .streamlit/
    └── config.toml         # Tema ACHS (colores verdes)
```
