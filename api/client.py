import requests
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


class Conlic:
    """Realiza consultas a API da Conlicitações e faz o download dos editais disponíveis"""

    def __init__(self):

        self.API_TOKEN = os.environ.get("CONLIC_API_TOKEN")
        if self.API_TOKEN == None:
            print("Token da API não encontrado")

        self.DOMAIN = "https://consultaonline.conlicitacao.com.br"
        self.BASE_URL = f"{self.DOMAIN}/api"
        self.headers = {"x-auth-token": self.API_TOKEN}
        self.testar_conexao()
        self.criar_pastas()

    def criar_pastas(self):
        """Criação de Diretórios"""
        fuso = ZoneInfo("America/Sao_Paulo")  # Define o fuso
        tempo = datetime.now(fuso).strftime("%d-%m-%Y_%H-%M-%S")
        self.PASTA= f"Requisição{tempo}"
        self.PASTA_DOWNLOAD = os.path.join("requisições",self.PASTA,"downloads")
        self.PASTA_LISTADEBOLETINS = os.path.join("requisições",self.PASTA,"lista de boletins")
        self.PASTA_BOLETINS = os.path.join("requisições",self.PASTA,"boletins")
        
        for pasta in [self.PASTA_DOWNLOAD,self.PASTA_LISTADEBOLETINS,self.PASTA_BOLETINS]:
            if not os.path.exists(pasta):
                os.makedirs(pasta)
                print(f"Pasta '{pasta}' criada.")

    def salvar_json(self,dados,filename,pasta):
        with open(os.path.join(pasta,filename), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

    def testar_conexao(self):
        endpoint = f"{self.BASE_URL}/filtros" 
        response = requests.get(endpoint, headers=self.headers)
        if response.status_code == 200:
            print("Conexão bem-sucedida")
        else : raise(Exception(f"Erro ao conectar \n {response.text}"))
        
    def obter_filtros(self,verbose=False) -> dict|None:
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
        
    def obter_lista_de_boletins(self,filtro_id, quantidade: int = 1,verbose=False) -> list[dict]:
        """Busca os boletins disponiveis de um filtro específico."""
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
                    self.salvar_json(data["boletins"],f"lista.json",self.PASTA_LISTADEBOLETINS)
                    return data['boletins']
                else:
                    print("Erro: Nenhum boletim encontrado para este filtro.")
                    return []
            else:
                print(f"Erro ao buscar boletins: {response.status_code}")
                print(f"Resposta: {response.text}")
                return []
                
        except requests.RequestException as e:
            print(f"Erro na obtenção dos boletins: {e}")
            return []
        
    def buscar_boletim(self,boletim_id,verbose=False):
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
        
                self.salvar_json(boletim_data,f"{boletim_data["datahora_fechamento"]}.json",self.PASTA_BOLETINS)
                return boletim_data
            else:
                print(f"Erro ao buscar dados do boletim: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Erro de conexão na busca pelos dados do boletim: {e}")
            return None

    def obter_ultimo_boletim(self):
        filtro_id = 78239
        listaB = self.obter_lista_de_boletins(filtro_id)
        if listaB:
            boletim_id = listaB[0]["id"]
            boletim = self.buscar_boletim(boletim_id)
            editais = []
            for lic in boletim["licitacoes"]:
                for doc in lic["documento"]:
                    f_name, f_type = os.path.splitext(doc["filename"])
                    edit = {"id": lic["id"],
                            "type": f_type,
                            "filename": f_name,
                            "url":self.DOMAIN+doc["url"]}
                    editais.append(edit)
            self.salvar_json(editais,f"downloads[{boletim["id"]}].json",self.PASTA_DOWNLOAD)
        return editais
        


if __name__ == "__main__":      
    CL = Conlic()
    CL.obter_ultimo_boletim()
    # filtros = CL.obter_filtros(False)
    # filtro_id = 78239
    # Boletins = CL.obter_lista_de_boletins(filtro_id,3,False) # type: ignore
    # for b in Boletins:
    #     Dados = CL.buscar_boletim(b["id"],False) # type: ignore
  
    