import requests
import json
import os
from tqdm import tqdm




class ConLic:
    """Realiza consultas a API da Conlicitações e faz o download dos editais disponíveis"""

    def __init__(self, api_token: str, output_folder:str = "downloads"):

        self.API_TOKEN = api_token
        self.PASTA_DOWNLOAD = output_folder
        self.PASTA_BOLETINS = "boletins"
        self.PASTA_LICITACOES = "licitacoes"
        self.DOMAIN = "https://consultaonline.conlicitacao.com.br"
        self.BASE_URL = f"{self.DOMAIN}/api"

        self.headers = {"x-auth-token": api_token}

        for pasta in [self.PASTA_DOWNLOAD,self.PASTA_BOLETINS,self.PASTA_LICITACOES]:
            if not os.path.exists(pasta):
                os.makedirs(pasta)
                print(f"Pasta '{pasta}' criada.")

    def salvar_json(self,dados,filename,pasta):
        with open(os.path.join(pasta,filename), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)


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

                    self.salvar_json(data["filtros"],"filtros.json",os.curdir)
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
        

    def buscar_boletins(self,filtro_id, quantidade: int = 1,verbose=False) -> dict|None:
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
                    self.salvar_json(data["boletins"],f"[{filtro_id}]Boletins.json",self.PASTA_BOLETINS)
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
        

    def buscar_dados_boletim(self,boletim_id,verbose=False) -> dict|None:
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
        
                self.salvar_json(data,f"[{boletim_id}]DadosBoletim.json",self.PASTA_LICITACOES)
                return data
            else:
                print(f"Erro ao buscar dados do boletim: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Erro de conexão na busca pelos dados do boletim: {e}")
            return None


    def fazer_download(self,filename,relative_url):
        """Baixa um arquivo de edital e salva na pasta."""
        # Cria a pasta de download se ela não existir
        if not os.path.exists(self.PASTA_DOWNLOAD):
            os.makedirs(self.PASTA_DOWNLOAD)
            print(f"Pasta '{self.PASTA_DOWNLOAD}' criada.")

        try:
            # Monta a URL de download completa
            download_url = f"{self.DOMAIN}{relative_url}"
            
            # Define o caminho local para salvar o arquivo
            local_filepath = os.path.join(self.PASTA_DOWNLOAD,filename)

            print(f"  Baixando {filename} ...")
            
            # Faz a requisição de download. 
            # Note que NÃO usamos os 'headers' aqui, pois a autenticação
            # está no token da própria URL de download.
            file_response = requests.get(download_url)

            if file_response.status_code == 200:
                # Salva o arquivo no modo 'wb' (write binary)
                with open(local_filepath, 'wb') as f:
                    f.write(file_response.content)
                print(f"  SUCESSO: Arquivo salvo em '{local_filepath}'")
            else:
                print(f"  ERRO: Falha ao baixar o arquivo. Status: {file_response.status_code}")
                # O link pode ter expirado (são válidos por 24h) 

        except requests.RequestException as e:
            print(f"  ERRO: Exceção de conexão ao baixar o arquivo: {e}")
        except Exception as e:
            print(f"  ERRO: Ocorreu um erro inesperado no download: {e}")


    def baixar_editais(self, qtd_boletim: int = 1, verbose : bool = False) -> None:
            """Realiza o download dos editais mais recentes"""
            
            # 1. Obter filtros (e tratar se for None)
            filtros = self.obter_filtros(verbose)
            if not filtros:
                print("Nenhum filtro encontrado ou erro na API. Abortando downloads.")
                return 

            # TQDM NÍVEL 1: Iterando sobre os filtros
            for f in tqdm(filtros, desc="Processando Filtros"):
                
                boletins = self.buscar_boletins(f["id"], qtd_boletim, verbose)
                if not boletins:
                    if verbose: print(f"Nenhum boletim para o filtro {f['id']}. Pulando.")
                    continue 

                # TQDM NÍVEL 2: Iterando sobre os boletins de CADA filtro
                # 'leave=False' faz a barra sumir após a conclusão, limpando o terminal
                for b in tqdm(boletins, desc=f"Boletins (Filtro {f['id']})", leave=False):
                    
                    dados = self.buscar_dados_boletim(b["id"], verbose)
                    if not dados or "licitacoes" not in dados:
                        if verbose: print(f"Nenhum dado ou licitação para o boletim {b['id']}. Pulando.")
                        continue

                    licitacoes = dados["licitacoes"]
                    if not licitacoes:
                        continue

                    # TQDM NÍVEL 3: Iterando sobre as licitações (onde o download ocorre)
                    for lic in tqdm(licitacoes, desc=f"Download (Boletim {b['id']})", leave=False):
                        
                        if "documento" in lic and lic["documento"]:
                            for doc in lic["documento"]:
                                filename = f"[{f['id']}][{b['id']}][{lic['id']}]-{doc['filename']}"
                                url = doc["url"]
                                
                                # O método fazer_download já imprime seu status
                                # (ex: " Baixando... SUCESSO:")
                                self.fazer_download(filename, url)


if __name__ == "__main__":
    API_TOKEN = "3e501248-a43c-421a-9f33-c6bf7e7004e7"# os.environ.get("CONLIC_API_TOKEN")
    Inst = ConLic(API_TOKEN,"downloads")
    filtros = Inst.obter_filtros(False)
    filtros_id  =[filtros[3]]
    for f in filtros:
        Boletins = Inst.buscar_boletins(f["id"],2,False) # type: ignore
        for b in Boletins:
            Dados = Inst.buscar_dados_boletim(b["id"],False) # type: ignore
    # Boletins = Inst.buscar_boletins(filtros[0]["id"],10,False) # type: ignore
    # for b in Boletins:
    #     Dados = Inst.buscar_dados_boletim(b["id"],False) # type: ignore

    #print(json.dumps(Boletins, indent=2, ensure_ascii=False))
    # print("#"*100)
    #Inst.baixar_editais(1,False)
    