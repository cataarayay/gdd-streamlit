"""
Script para crear/actualizar usuarios GDD ACHS.
Uso: python setup_users.py

Jerarquía ACHS:
  admin     → Ve todo, gestiona usuarios, carga datos
  jefatura  → Ve todo, resumen de su territorio/subgerencia
  experto   → Ve todo, resumen de su área

Territorios:
  GRTR1010 = Metropolitano
  GRTR1020 = Norte
  GRTR1030 = Sur
  SGMP0001 = MIPE (portafolio especial)
"""
import yaml
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ============================================================
#  EDITAR USUARIOS AQUÍ
#  Copiar el bloque y ajustar para cada usuario nuevo.
#  Campos:
#    name         → Nombre completo
#    email        → Email ACHS
#    password     → hash_password("clave")
#    rol          → "admin" | "jefatura" | "experto"
#    territorio   → código GTE o None para nacional
#    subgerencia  → código SUBG o None para todo el territorio
# ============================================================

usuarios = {

    # ---- ADMINISTRADORES ----
    "cata": {
        "name": "Catalina Araya",
        "email": "charayay@achs.cl",
        "password": hash_password("admin2026"),
        "rol": "admin",
        "territorio": None,
        "subgerencia": None,
    },
    "Javiera Cabalin": {
        "name": "J. Cabalin",
        "email": "jicabalinf@achs.cl",
        "password": hash_password("admin2026"),
        "rol": "admin",
        "territorio": None,
        "subgerencia": None,
    },

    # ---- JEFATURAS TERRITORIO ----
    "terr_metro": {
        "name": "Territorial Metro",
        "email": "rmunita@achs.cl",
        "password": hash_password("metro2026"),
        "rol": "jefatura",
        "territorio": "GRTR1010",
        "subgerencia": None,
    },
    "terr_norte": {
        "name": "Territorial Norte",
        "email": "pariojaz@achs.cl",
        "password": hash_password("norte2026"),
        "rol": "jefatura",
        "territorio": "GRTR1020",
        "subgerencia": None,
    },
    "terr_sur": {
        "name": "Territorial Sur",
        "email": "jbaumann@achs.cl",
        "password": hash_password("sur2026"),
        "rol": "jefatura",
        "territorio": "GRTR1030",
        "subgerencia": None,
    },

    # ---- JEFATURA MIPE ----
    "laura_sierra": {
        "name": "Laura Sierra",
        "email": "lcsierras@achs.cl",
        "password": hash_password("mipe2026"),
        "rol": "jefatura",
        "territorio": "SGMP0001",
        "subgerencia": "SGMP0001",
    },

    # ---- EJEMPLOS JEFATURA SUBGERENCIA ----
    # (Duplicar y ajustar para cada subgerencia real)
    #
    # "jef_subg_ejemplo": {
    #     "name": "Jefe Subgerencia X",
    #     "email": "jsubgx@achs.cl",
    #     "password": hash_password("clave123"),
    #     "rol": "jefatura",
    #     "territorio": "GRTR1010",
    #     "subgerencia": "SGM01010",
    # },

    # ---- EJEMPLOS EXPERTO ----
    # (Duplicar y ajustar para cada experto)
    #
    # "exp_ejemplo": {
    #     "name": "Experto Ejemplo",
    #     "email": "exp@achs.cl",
    #     "password": hash_password("clave123"),
    #     "rol": "experto",
    #     "territorio": "GRTR1010",
    #     "subgerencia": "SGM01010",
    # },
}

# ============================================================
#  NO EDITAR DEBAJO DE ESTA LÍNEA
# ============================================================

config = {
    "credentials": {"usernames": usuarios},
    "cookie": {
        "expiry_days": 30,
        "key": "gdd_achs_cookie_key_2026",
        "name": "gdd_auth",
    },
    "pre-authorized": {"emails": []},
}

with open("config_usuarios.yaml", "w", encoding="utf-8") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"✓ {len(usuarios)} usuario(s) configurados en config_usuarios.yaml")
print()
for u, data in usuarios.items():
    ter = data.get('territorio') or 'Nacional'
    sub = data.get('subgerencia') or ''
    label = f"{ter} → {sub}" if sub else ter
    print(f"  {u:20s} {data['name']:30s} {data['rol']:10s} {label}")
