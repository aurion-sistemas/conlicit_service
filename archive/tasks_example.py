from celery import Celery, group, chord
import time

# --- Configuração ---
app = Celery('tasks',
             broker='pyamqp://guest:guest@localhost:9972//',
             backend='redis://127.0.0.1:9963/0')
app.conf.enable_utc = True
app.conf.timezone = 'UTC'

# ==============================================================================
# PASSO 1: GERADOR (Roda no Servidor)
# ==============================================================================
@app.task(queue='server_queue')
def etapa_1_gerar_dados(quantidade):
    """
    Simula a criação de uma lista de dados no servidor.
    Ex: Ler um CSV gigante e retornar os IDs das linhas.
    """
    print(f"--- [SERVER] Gerando lista com {quantidade} itens...")
    
    # Gera uma lista simples de números
    # IMPORTANTE: Garantir que são 'int' nativos do Python, não numpy.int64
    lista_dados = [int(i) for i in range(quantidade)]
    
    return lista_dados

# ==============================================================================
# O ORQUESTRADOR (Roda Localmente)
# ==============================================================================
@app.task(queue='local_queue')
def etapa_2_distribuir(lista_recebida_do_servidor):
    """
    Recebe a lista do servidor e monta o CHORD (Grupo + Callback).
    """
    print(f"--- [LOCAL - ORQUESTRADOR] Recebi {len(lista_recebida_do_servidor)} itens. Distribuindo...")

    # 1. Cria a lista de assinaturas (as tarefas que vão rodar em paralelo)
    header = [tarefa_filha_processar.s(item) for item in lista_recebida_do_servidor]

    # 2. Define o callback (a tarefa que roda quando todas acima terminarem)
    callback = etapa_3_analise_final.s()

    # 3. Retorna o chord. O Celery executa isso automaticamente.
    return chord(header)(callback)



# ==============================================================================
# PASSO 2: WORKER INDIVIDUAL (Roda Localmente - EM PARALELO)
# ==============================================================================
@app.task(queue='local_queue')
def tarefa_filha_processar(item):
    """
    Esta tarefa será executada dezenas de vezes em paralelo.
    """
    # Simula processamento
    time.sleep(0.5) 
    
    # Exemplo de cálculo: Quadrado do número
    resultado = item * item
    
    print(f"--- [LOCAL - FILHA] Item {item} processado. Resultado: {resultado}")
    return resultado

# ==============================================================================
# PASSO 3: REDUTOR/ANÁLISE FINAL (Roda Localmente - NO FINAL)
# ==============================================================================
@app.task(queue='local_queue')
def etapa_3_analise_final(lista_de_resultados):
    """
    Esta tarefa é chamada AUTOMATICAMENTE quando todas as tarefas filhas terminam.
    Ela recebe uma lista contendo o retorno de cada filha.
    """
    print("--- [LOCAL - FINAL] Todas as tarefas filhas terminaram. Consolidando...")
    
    total_processado = len(lista_de_resultados)
    soma_total = sum(lista_de_resultados)
    
    msg = f"Sucesso! {total_processado} itens processados. Soma total: {soma_total}"
    print(msg)
    return msg






    #celery -A tasks worker --loglevel=info -n worker_server@%h -Q server_queue