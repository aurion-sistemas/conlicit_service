from celery import Celery, group, chord
import os
import requests
from pathlib import Path
from api.client import Conlic

app = Celery('tasks',
             broker=os.environ.get("CELERY_BROKER_URL"),
             backend=os.environ.get("CELERY_BACKEND_URL"))
app.conf.enable_utc = True
app.conf.timezone = 'UTC'

PARSEWAY_INBOX_DIR = os.environ.get("PARSEWAY_INBOX_DIR", "/storage/inbox")
PARSEWAY_URL = os.environ.get("PARSEWAY_URL", "http://licitacao-service:8003")
PARSEWAY_EQUIPMENT_JSON = os.environ.get("PARSEWAY_EQUIPMENT_JSON", "/storage/equipamentos.json")


# ==============================================================================
# PASSO 1: BUSCA OS EDITAIS E DISPARA O PIPELINE (Roda no Servidor)
# ==============================================================================

@app.task(queue='server_queue')
def executar_pipeline():
    """Ponto de entrada: busca editais da API e dispara downloads em paralelo."""
    CL = Conlic()
    editais = CL.obter_ultimo_boletim()

    if not editais:
        print("[PIPELINE] Nenhum edital encontrado.")
        return "Nenhum edital encontrado"

    print(f"[PIPELINE] {len(editais)} editais encontrados. Enfileirando downloads...")

    chord(
        group(fazer_download.s(item) for item in editais)
    )(analise_final.s())

    return f"{len(editais)} downloads enfileirados"


@app.task(queue='server_queue')
def obter_links():
    """Retorna a lista de editais do último boletim sem disparar o pipeline."""
    CL = Conlic()
    return CL.obter_ultimo_boletim()


# ==============================================================================
# PASSO 2: DOWNLOAD PARALELO (Roda Local)
# ==============================================================================

@app.task(queue='local_queue', autoretry_for=(Exception,), max_retries=3, retry_backoff=True)
def fazer_download(item):
    """Baixa um arquivo de edital e salva no inbox do parseway."""
    os.makedirs(PARSEWAY_INBOX_DIR, exist_ok=True)

    filename = f"{item['filename']}{item['type']}"
    dest = os.path.join(PARSEWAY_INBOX_DIR, filename)

    if os.path.exists(dest):
        print(f"[DOWNLOAD] Já existe, pulando: {filename}")
        return dest

    print(f"[DOWNLOAD] Baixando: {filename}")
    response = requests.get(item["url"], timeout=120)
    response.raise_for_status()

    with open(dest, "wb") as f:
        f.write(response.content)

    print(f"[DOWNLOAD] Salvo em {dest}")
    return dest


# ==============================================================================
# PASSO 3: ENFILEIRA NO PARSEWAY (Roda Local, após todos os downloads)
# ==============================================================================

@app.task(queue='local_queue')
def analise_final(paths):
    """Recebe os caminhos baixados e enfileira o processamento no parseway."""
    valid_paths = [p for p in paths if p and os.path.exists(p)]

    if not valid_paths:
        print("[PARSEWAY] Nenhum arquivo válido para processar.")
        return {"status": "noop", "count": 0}

    filenames = [Path(p).name for p in valid_paths]
    print(f"[PARSEWAY] Enviando {len(filenames)} editais para processamento...")

    payload = {
        "input_paths": filenames,
        "equipment_json_path": PARSEWAY_EQUIPMENT_JSON,
    }

    resp = requests.post(
        f"{PARSEWAY_URL}/process-batch",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()

    print(f"[PARSEWAY] Jobs criados: {result}")
    return result
