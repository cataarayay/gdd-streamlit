"""
Script para crear/actualizar usuarios.
Uso: python setup_users.py
"""
import yaml
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ---------- EDITAR USUARIOS AQUÍ ----------
usuarios = {
    "admin": {
        "name": "Administrador",
        "email": "admin@achs.cl",
        "password": hash_password("admin123"),
        "rol": "admin",
        "territorio": None,
        "subgerencia": None,
    },
    # Ejemplo — agregar más usuarios:
    # "jperez": {
    #     "name": "Juan Pérez",
    #     "email": "jperez@achs.cl",
    #     "password": hash_password("clave123"),
    #     "rol": "jefatura",
    #     "territorio": "GRTR1010",
    #     "subgerencia": "SGM01010",
    # },
}

config = {
    "credentials": {"usernames": usuarios},
    "cookie": {
        "expiry_days": 30,
        "key": "gdd_achs_cookie_key_2026",
        "name": "gdd_auth",
    },
    "pre-authorized": {"emails": []},
}

with open("config_usuarios.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"✓ {len(usuarios)} usuario(s) configurados en config_usuarios.yaml")
for u, data in usuarios.items():
    print(f"  {u} → {data['name']} ({data['rol']})")
