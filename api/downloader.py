import requests
import json
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class ConLic:
    """Realiza consultas a API da Conlicitações e faz o download dos editais disponíveis"""

    def __init__(self, api_token: str, output_folder:str = "downloads"):

        self.API_TOKEN = api_token
        self.PASTA_DOWNLOAD = output_folder
        self.DOMAIN = "https://consultaonline.conlicitacao.com.br"
        self.BASE_URL = f"{self.DOMAIN}/api"

        self.headers = {"x-auth-token": api_token}

        if not os.path.exists(self.PASTA_DOWNLOAD):
            os.makedirs(self.PASTA_DOWNLOAD)
            print(f"Pasta '{self.PASTA_DOWNLOAD}' criada.")


    def obter_filtros(self,verbose=False) -> list[dict]|None:
        """Busca a lista de filtros do cliente."""
        endpoint = f"{self.BASE_URL}/filtros" 

        try:
            response = requests.get(endpoint, headers=self.headers)
            
            # Verifica se a requisição foi bem-sucedida (código 200)
            if response.status_code == 200:
                data = response.json()
        
                # Verifica se existe algum filtro na resposta
                if data.get('filtros'):
                    if verbose: 
                        for filtro in data['filtros']:
                            filtro_id = filtro.get('id')
                            filtro_desc = filtro.get('descricao')
                            print(f"Filtro encontrado: '{filtro_desc}' (ID: {filtro_id})")

                    return data['filtros']
                else:
                    print("Erro: Nenhum filtro encontrado para este cliente.")
                    return None
            else:
                print(f"Erro ao buscar filtros: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Erro de conexão na busca por filtros: {e}")
            return None 
        

    def buscar_boletins(self,filtro_id, quantidade: int = 1,verbose=False) -> list[dict]|None:
        """Busca os boletins de um filtro específico."""
        endpoint = f"{self.BASE_URL}/filtro/{filtro_id}/boletins" 
        
        #Por padrão busca apenas o mais recente boletim 
        params = {
            "page":1,
            "per_page": quantidade,      
            "order": "desc"     
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('boletins'):
                    if verbose: 
                        for boletim in data['boletins']:
                            boletim_id = boletim.get('id')
                            boletim_data = boletim.get('datahora_fechamento')
                            print(f"Boletim encontrado: ID {boletim_id} (Data: {boletim_data})")

                    return data['boletins']
                else:
                    print("Erro: Nenhum boletim encontrado para este filtro.")
                    return None
            else:
                print(f"Erro ao buscar boletins: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Erro na obtenção dos boletins: {e}")
            return None
        

    def buscar_dados_boletim(self,boletim_id,verbose=False) -> list[dict]|None:
        """Busca os dados de um boletim (licitações e acompanhamentos)."""
        endpoint = f"{self.BASE_URL}/boletim/{boletim_id}"  
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                boletim_data = data.get('boletim', {})
                if verbose:
                    print(f"\n--- SUCESSO! Dados do Boletim {boletim_id} ---")
                    print(f"Total de Licitações: {boletim_data.get('quantidade_licitacoes')}")
                    print(f"Total de Acompanhamentos: {boletim_data.get('quantidade_acompanhamentos')}")
        
                
                return data
            else:
                print(f"Erro ao buscar dados do boletim: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Erro de conexão na busca pelos dados do boletim: {e}")
            return None


    def fazer_download(self, filename, relative_url):
        """Baixa um arquivo de edital e salva na pasta."""
        # A criação da pasta já deve estar no __init__
        
        try:
            # Monta a URL de download completa
            download_url = f"{self.DOMAIN}{relative_url}"
            local_filepath = os.path.join(self.PASTA_DOWNLOAD, filename)

            # Use tqdm.write para impressão thread-safe
            tqdm.write(f"  Baixando {filename} ...")
            
            file_response = requests.get(download_url)

            if file_response.status_code == 200:
                with open(local_filepath, 'wb') as f:
                    f.write(file_response.content)
                tqdm.write(f"  SUCESSO: Arquivo salvo em '{local_filepath}'")
                return local_filepath # Retorna o caminho em caso de sucesso
            else:
                tqdm.write(f"  ERRO: Falha ao baixar {filename}. Status: {file_response.status_code}")
                return None

        except requests.RequestException as e:
            tqdm.write(f"  ERRO: Exceção de conexão ao baixar {filename}: {e}")
            return None
        except Exception as e:
            tqdm.write(f"  ERRO: Ocorreu um erro inesperado no download de {filename}: {e}")
            return None


    def baixar_editais(self, qtd_boletim: int = 1, verbose : bool = False, max_threads: int = 10) -> None:
        """Realiza o download dos editais mais recentes usando threads."""
        
        # --- FASE 1: COLETAR TAREFAS ---
        print("Coletando lista de downloads...")
        tarefas_download = [] # Lista para guardar tuplas (filename, url)

        filtros = self.obter_filtros(verbose)
        if not filtros:
            print("Nenhum filtro encontrado.")
            return 

        for f in tqdm(filtros, desc="Coletando Filtros"):
            boletins = self.buscar_boletins(f["id"], qtd_boletim, verbose)
            if not boletins:
                continue 

            for b in boletins:
                dados = self.buscar_dados_boletim(b["id"], verbose)
                if not dados or "licitacoes" not in dados:
                    continue

                licitacoes = dados["licitacoes"]
                for lic in licitacoes:
                    if "documento" in lic and lic["documento"]:
                        for doc in lic["documento"]:
                            filename = f"[{f['id']}][{b['id']}][{lic['id']}]-{doc['filename']}"
                            url = doc["url"]
                            # Adiciona a tarefa à lista
                            tarefas_download.append( (filename, url) )

        if not tarefas_download:
            print("Nenhum edital encontrado para baixar.")
            return
            
        print(f"Coleta concluída. {len(tarefas_download)} arquivos para baixar.")

        # --- FASE 2: EXECUTAR DOWNLOADS EM PARALELO ---
        
        # 'max_workers' é o número de threads simultâneas
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            
            # 1. Submete todas as tarefas para o pool
            # 'future' é um objeto que representa o trabalho "futuro"
            futures = {
                executor.submit(self.fazer_download, filename, url): (filename, url)
                for (filename, url) in tarefas_download
            }

            # 2. Processa os resultados À MEDIDA QUE FICAM PRONTOS
            # 'as_completed' espera a *próxima* tarefa terminar, não importa qual
            # Envolvemos com 'tqdm' para ter a barra de progresso
            
            print(f"\nIniciando downloads com {max_threads} threads...")
            
            kwargs = {
                'total': len(tarefas_download),
                'desc': "Progresso Downloads",
                'unit': 'arquivo',
            }

            for future in tqdm(as_completed(futures), **kwargs):
                # 'future.result()' pega o valor retornado por 'fazer_download'
                resultado = future.result() 
                
                if resultado is None:
                   tqdm.write("Um download falhou (veja log acima)")
                

        print("\nTodos os downloads foram concluídos.")

if __name__ == "__main__":
    API_TOKEN = os.environ.get("CONLIC_API_TOKEN")
    Inst = ConLic(API_TOKEN,"downloads1")
    #filtros = Inst.obter_filtros(False)
    #Boletins = Inst.buscar_boletins(filtros[0]["id"],1,False) # type: ignore
    # Dados = Inst.buscar_dados_boletim(Boletins[0]["id"],True) # type: ignore
    #print(json.dumps(Boletins, indent=2, ensure_ascii=False))
    # print("#"*100)
    Inst.baixar_editais(1,False,10)

    