import os
import json
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from omie_client import OmieClient
import logging

# Configurao
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Credenciais
OMIE_APP_KEY = os.getenv("OMIE_APP_KEY")
OMIE_APP_SECRET = os.getenv("OMIE_APP_SECRET")
POSTGRES_URL = os.getenv("POSTGRES_URL")

def get_db_engine():
    """Cria a engine de conexo com o PostgreSQL."""
    return create_engine(POSTGRES_URL)

def sync_data(client, endpoint, method, table_name, engine, base_params=None, page_param="pagina", records_param="registros_por_pagina", total_pages_param="nTotalPaginas"):
    """
    Sincroniza dados da Omie para uma tabela no PostgreSQL.
    """
    logger.info(f"Iniciando sincronização de {table_name}...")
    
    try:
        # 1. Recuperar todos os registros da API
        records = client.list_all(endpoint, method, base_params, page_param=page_param, records_param=records_param, total_pages_param=total_pages_param)
        
        if not records:
            logger.info(f"Nenhum registro retornado para {table_name}.")
            return

        # 2. Converter para DataFrame do Pandas
        df = pd.json_normalize(records)
        
        # 2.1 TRATAMENTO DE TIPOS COMPLEXOS (dicts/lists)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

        # 3. Salvar no PostgreSQL (Usando Truncate + Append para evitar erro de dependência de views)
        with engine.begin() as connection:
            # Verifica se a tabela existe antes de truncar
            table_exists = pd.read_sql(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')", connection).iloc[0,0]
            if table_exists:
                logger.info(f"Limpando tabela {table_name}...")
                connection.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
            
            # Salvar os dados
            df.to_sql(table_name, connection, if_exists='append', index=False)
            
        logger.info(f"Sincronização de {table_name} concluída! {len(df)} registros salvos.")
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar {table_name}: {e}")

def main():
    if not all([OMIE_APP_KEY, OMIE_APP_SECRET, POSTGRES_URL]):
        logger.error("Erro: Credenciais no preenchidas no arquivo .env")
        return

    # Iniciar cliente e engine
    client = OmieClient(OMIE_APP_KEY, OMIE_APP_SECRET)
    engine = get_db_engine()

    # 1. Sincronizar Clientes
    sync_data(
        client, 
        endpoint="geral/clientes", 
        method="ListarClientes", 
        table_name="omie_clientes", 
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 2. Sincronizar Produtos
    sync_data(
        client, 
        endpoint="geral/produtos", 
        method="ListarProdutos", 
        table_name="omie_produtos", 
        engine=engine,
        base_params={"filtrar_apenas_omiepdv": "N"}
    )

    # 3. Sincronizar Pedidos de Venda
    sync_data(
        client, 
        endpoint="produtos/pedido", 
        method="ListarPedidos", 
        table_name="omie_pedidos_venda", 
        engine=engine,
        base_params={"filtrar_por_data_de": "01/01/2000"}
    )

    # 4. Sincronizar Notas Fiscais (Produtos)
    sync_data(
        client, 
        endpoint="produtos/nf_consultar", 
        method="ListarNF", 
        table_name="omie_notas_fiscais", 
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 5. Sincronizar Contas a Receber (Financeiro)
    sync_data(
        client, 
        endpoint="financas/contareceber", 
        method="ListarContasReceber", 
        table_name="omie_contas_receber", 
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 6. Sincronizar Contas a Pagar (Financeiro)
    sync_data(
        client, 
        endpoint="financas/contapagar", 
        method="ListarContasPagar", 
        table_name="omie_contas_pagar", 
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 7. Sincronizar Ordens de Serviço (Caso o cliente seja prestador)
    sync_data(
        client, 
        endpoint="servicos/os", 
        method="ListarOS", 
        table_name="omie_ordens_servico", 
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 8. Sincronizar Categorias Financeiras
    sync_data(
        client,
        endpoint="geral/categorias",
        method="ListarCategorias",
        table_name="omie_categorias",
        engine=engine
    )

    # 9. Sincronizar Contas Correntes
    sync_data(
        client,
        endpoint="geral/contacorrente",
        method="ListarContasCorrentes",
        table_name="omie_contas_correntes",
        engine=engine
    )

    # 10. Sincronizar Projetos
    sync_data(
        client,
        endpoint="geral/projetos",
        method="ListarProjetos",
        table_name="omie_projetos",
        engine=engine
    )

    # 11. Sincronizar Vendedores
    sync_data(
        client,
        endpoint="geral/vendedores",
        method="ListarVendedores",
        table_name="omie_vendedores",
        engine=engine
    )

    # 12. Sincronizar Lançamentos Financeiros (Fluxo de Caixa Realizado)
    sync_data(
        client, 
        endpoint="financas/contacorrentelancamentos", 
        method="ListarLancCC", 
        table_name="omie_lancamentos_financeiros", 
        engine=engine,
        base_params={"dtPagInicial": "01/01/2000"},
        page_param="nPagina",
        records_param="nRegPorPagina",
        total_pages_param="nTotPaginas"
    )

    # 13. Sincronizar Contratos de Serviço (Para valor de contrato dinâmico)
    sync_data(
        client,
        endpoint="servicos/contrato",
        method="ListarContratos",
        table_name="omie_contratos",
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    # 14. Sincronizar Notas Fiscais de Serviço (NFS-e)
    sync_data(
        client,
        endpoint="servicos/nfse",
        method="ListarNFSE",
        table_name="omie_nfse",
        engine=engine,
        base_params={"apenas_importado_api": "N"}
    )

    logger.info("Processo de sincronização completado com sucesso.")

if __name__ == "__main__":
    main()
