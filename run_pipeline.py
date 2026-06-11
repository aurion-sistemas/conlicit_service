import os
import requests
from api.downloader import ConLic

API_TOKEN = os.environ.get("CONLIC_API_TOKEN")
PARSEWAY_URL = os.environ.get("PARSEWAY_URL", "http://licitacao-service:8003")
PARSEWAY_EQUIPMENT_JSON = os.environ.get("PARSEWAY_EQUIPMENT_JSON", "/storage/equipamentos.json")
INBOX_DIR = os.environ.get("PARSEWAY_INBOX_DIR", "/storage/inbox")

if not API_TOKEN:
    raise RuntimeError("CONLIC_API_TOKEN não definido")

cl = ConLic(API_TOKEN, INBOX_DIR)
cl.baixar_editais(qtd_boletim=1, verbose=True, max_threads=10)

filenames = [f for f in os.listdir(INBOX_DIR) if not f.startswith('.')]

if not filenames:
    print("Nenhum edital encontrado neste boletim.")
else:
    print(f"\n{len(filenames)} edital(is) no inbox. Notificando parseway...")
    resp = requests.post(
        f"{PARSEWAY_URL}/process-batch",
        json={
            "input_paths": filenames,
            "equipment_json_path": PARSEWAY_EQUIPMENT_JSON,
        },
        timeout=30,
    )
    resp.raise_for_status()
    print(f"Parseway respondeu: {resp.json()}")
