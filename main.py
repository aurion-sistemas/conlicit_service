import os

# Carrega o .env manualmente
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

from api.client import Conlic

cl = Conlic()
filtros = cl.obter_filtros(verbose=True)

if filtros:
    for f in filtros:
        print(f"\nBuscando boletim do filtro {f['id']}...")
        cl.obter_ultimo_boletim(f["id"])
