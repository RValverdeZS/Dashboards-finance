import requests
import json
import logging
import time

# Configurao de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OmieClient:
    """
    Cliente genrico para interagir com a API Omie usando JSON-RPC.
    """
    BASE_URL = "https://app.omie.com.br/api/v1/"

    def __init__(self, app_key, app_secret):
        self.app_key = str(app_key).strip() if app_key else ""
        self.app_secret = str(app_secret).strip() if app_secret else ""
        
        if not self.app_key or not self.app_secret:
            logger.warning("Cuidado: App Key ou App Secret esto vazios!")
        else:
            # Mostrar apenas os primeiros 3 caracteres para segurana
            logger.info(f"OmieClient inicializado com chaves: {self.app_key[:3]}... / {self.app_secret[:3]}...")

    def call(self, endpoint, method, params=None):
        """
        Realiza uma chamada para a API Omie.
        :param endpoint: Ex: 'geral/clientes/'
        :param method: Ex: 'ListarClientes'
        :param params: Dicionrio com os parmetros da chamada.
        """
        url = f"{self.BASE_URL}{endpoint.strip('/')}/"
        
        if params is None:
            params = [{}]
        elif not isinstance(params, list):
            params = [params]

        payload = {
            "call": method,
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "param": params
        }

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # Se for 500, o Omie ainda pode ter enviado um JSON com o motivo
            if response.status_code == 500:
                try:
                    data = response.json()
                    # Cdigo de erro especfico para "Página vazia"
                    if "faultcode" in data and "5113" in data.get("faultcode", ""):
                        logger.info(f"Aviso: Nenhum registro encontrado para {method} (página vazia).")
                        return {"param": params, "total_de_paginas": 0, "registros": []} # Formato dummy
                    
                    logger.error(f"Erro na API Omie (500 - {method}): {data.get('faultstring')}")
                    return None
                except:
                    pass

            response.raise_for_status()
            data = response.json()
            
            # Verificar se a resposta contm erro (padro Omie)
            if "faultstring" in data:
                logger.error(f"Erro na API Omie ({method}): {data.get('faultstring')}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisio HTTP ({method}): {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Detalhes: {e.response.text}")
            return None

    def list_all(self, endpoint, method, base_params=None, records_per_page=100, page_param="pagina", records_param="registros_por_pagina", total_pages_param="nTotalPaginas"):
        """
        Itera sobre todas as páginas de um método de listagem.
        """
        all_records = []
        page = 1
        
        if base_params is None:
            base_params = {}

        while True:
            logger.info(f"Buscando página {page} de {method}...")
            
            # Adicionar paginação aos parâmetros
            current_params = base_params.copy()
            current_params.update({
                page_param: page,
                records_param: records_per_page
            })
            
            response = self.call(endpoint, method, current_params)
            
            if not response:
                break
                
            # Omie costuma retornar os dados em uma chave que depende do método.
            # Procuramos por uma lista que não seja a 'param' e que contenha dados.
            records = None
            
            # Ordem de preferência: listas que parecem conter os dados principais (geralmente a maior lista)
            candidate_lists = [v for k, v in response.items() if isinstance(v, list) and k != "param"]
            
            if candidate_lists:
                # Pegar a lista com mais itens (evita pegar listas de erros ou meta-informação menores)
                records = max(candidate_lists, key=len)
            
            if records:
                all_records.extend(records)
                logger.info(f"Página {page} recuperada: {len(records)} registros.")
            else:
                logger.warning(f"Nenhum registro encontrado na página {page}.")
                # Se não tem registros na primeira página, paramos. 
                # Se for página > 1, pode ser apenas o fim dos dados.
                if page == 1:
                    break
                
            # Verificar total de páginas
            # Alguns endpoints usam nomes diferentes, pegamos o primeiro que parece ser um número de total de páginas
            total_pages = response.get(total_pages_param)
            
            # Fallback: tentar outros nomes comuns de total de páginas se o padrão falhar
            if total_pages is None:
                for alt_key in ["nTotalPaginas", "nTotPaginas", "total_de_paginas"]:
                    if alt_key in response:
                        total_pages = response[alt_key]
                        break
            
            # Se ainda for None ou 0, e temos registros, assumimos que pode haver mais páginas
            # mas o seguro é parar se não soubermos o total e a página atual não veio cheia
            if total_pages is None or total_pages == 0:
                if records and len(records) < records_per_page:
                    break
            elif page >= int(total_pages):
                break
                
            page += 1
            # Respeitar limite de taxa (rate limit) se necessário (Omie permite 4 chamadas/segundo em média)
            time.sleep(0.25) 
            
        logger.info(f"Total de registros recuperados para {method}: {len(all_records)}")
        return all_records
