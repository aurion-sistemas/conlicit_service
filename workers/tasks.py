from celery import Celery, group, chord
import os
import time
from api.client import Conlic

# --- Configuração ---
app = Celery('tasks',
             broker=os.environ.get("CELERY_BROKER_URL"),
             backend=os.environ.get("CELERY_BACKEND_URL"))
app.conf.enable_utc = True
app.conf.timezone = 'UTC'

# ==============================================================================
# PASSO 1: GERADOR (Roda no Servidor)
# ==============================================================================
@app.task(queue='server_queue')
def obter_links():
    """
    Simula a criação de uma lista de dados no servidor.
    Ex: Ler um CSV gigante e retornar os IDs das linhas.
    """

    CL = Conlic()
    editais = CL.obter_ultimo_boletim()
    
    return editais


@app.task(queue='local_queue')
def fazer_download(item):
    """
    Esta tarefa será executada dezenas de vezes em paralelo.
    """
    # Simula processamento
    time.sleep(0.5) 
    
    resultado = item
    
    print(f"--- [LOCAL - FILHA] Item {item} processado. Resultado: {resultado}")
    return resultado


@app.task(queue='local_queue')
def converter2md(item):
    """
    Esta tarefa será executada dezenas de vezes em paralelo.
    """
    # Simula processamento
    time.sleep(0.5) 
    
    resultado = item
    
    print(f"--- [LOCAL - FILHA] Item {item} processado. Resultado: {resultado}")
    return resultado


@app.task(queue='local_queue')
def executar_rag(item):
    """
    Esta tarefa será executada dezenas de vezes em paralelo.
    """
    # Simula processamento
    time.sleep(0.5) 
    
    resultado = item 
    
    print(f"--- [LOCAL - FILHA] Item {item} processado. Resultado: {resultado}")
    return resultado



@app.task(queue='local_queue')
def analise_final(lista_de_resultados):
    """
    Esta tarefa é chamada AUTOMATICAMENTE quando todas as tarefas filhas terminam.
    Ela recebe uma lista contendo o retorno de cada filha.
    """
    msg = f"Sucesso!  Todos os Itens foram processados"
    print(msg)
    return msg


    #celery -A tasks worker --loglevel=info -n worker_server@%h -Q server_queue