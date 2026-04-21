import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configuração
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

POSTGRES_URL = os.getenv("POSTGRES_URL")

def get_engine():
    return create_engine(POSTGRES_URL)

def robust_read_excel(file_path, sheet_name, keywords=['Fornecedor', 'Valor']):
    """Encontra o cabeçalho correto e lê o excel."""
    try:
        df_preview = pd.read_excel(file_path, sheet_name=sheet_name, nrows=15)
        header_row = 0
        for i, row in df_preview.iterrows():
            row_str = " ".join(row.astype(str))
            if any(kw.lower() in row_str.lower() for kw in keywords):
                header_row = i + 1
                break
        return pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    except Exception as e:
        logger.error(f"Erro ao ler {sheet_name} de {file_path}: {e}")
        return pd.DataFrame()

def map_and_filter(df, required_cols):
    """Mapeia colunas dinamicamente e garante que todas as colunas necessárias existam."""
    mapping = {}
    found_targets = set()
    
    for col in df.columns:
        c = str(col)
        target = None
        if 'Vencimento' in c or ('Data' in c and 'Venc' in c): target = 'data_vencimento'
        elif 'Data' in c: target = 'data_evento'
        if 'Fornecedor' in c: target = 'fornecedor'
        if 'Categoria' in c: target = 'categoria'
        if 'Valor' in c: target = 'valor'
        if 'Documento Fiscal' in c or 'NF' in c or 'Nmero' in c or 'N.' in c: target = 'nf'
        
        if target and target not in found_targets:
            mapping[col] = target
            found_targets.add(target)
            
    df = df.rename(columns=mapping)
    
    # Garante que todas as colunas requeridas existam no DataFrame final
    for req in required_cols:
        if req not in df.columns:
            df[req] = 'N/D'
            
    return df[required_cols]

def save_to_db(df, table_name, engine):
    """Salva o DataFrame no banco usando TRUNCATE CASCADE para não quebrar views."""
    with engine.begin() as connection:
        # Verifica se a tabela existe
        table_exists = pd.read_sql(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')", connection).iloc[0,0]
        if table_exists:
            logger.info(f"Limpando tabela {table_name}...")
            connection.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
            df.to_sql(table_name, connection, if_exists='append', index=False)
        else:
            df.to_sql(table_name, connection, if_exists='replace', index=False)

def sync_mapa_faturamento():
    file_path = 'dashboards/support_tables/7B-Mapa de faturamento_LFM Enotec Cobrape-VF.xlsx'
    if not os.path.exists(file_path): return
    logger.info("Sincronizando Mapa de Faturamento...")
    df = pd.read_excel(file_path, sheet_name=0, header=None)
    valor_bem = df.iloc[32:34, 8].dropna().astype(float).max()
    valor_taxas = df.iloc[32:34, 9].dropna().astype(float).max()
    df_contrato = pd.DataFrame([{"projeto": "7B", "valor_credito": valor_bem, "valor_taxas": valor_taxas, "valor_total_contrato": valor_bem + valor_taxas}])
    engine = get_engine()
    save_to_db(df_contrato, "manual_contrato_7b", engine)

def sync_contas_pagar_manual():
    file_path = 'dashboards/support_tables/7B_CONTAS A PAGAR_TODOS-v02.xlsx'
    if not os.path.exists(file_path): return
    logger.info("Sincronizando Contas a Pagar Manual...")
    df = robust_read_excel(file_path, 'Contas a Pagar')
    if df.empty: return
    df = map_and_filter(df, ['data_vencimento', 'fornecedor', 'categoria', 'valor', 'nf'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0).abs()
    engine = get_engine()
    save_to_db(df, "manual_contas_pagar", engine)
    logger.info(f"manual_contas_pagar: {len(df)} registros.")

def sync_pagamentos_manual():
    file_path = 'dashboards/support_tables/7B_PGTOS_TODOS-v02.xlsx'
    if not os.path.exists(file_path): return
    logger.info("Sincronizando Pagamentos Manuais...")
    df = robust_read_excel(file_path, 'CONTAS PAGAS')
    if df.empty: return
    df = map_and_filter(df, ['data_evento', 'fornecedor', 'categoria', 'valor', 'nf'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0).abs()
    engine = get_engine()
    save_to_db(df, "manual_pagamentos_realizados", engine)
    logger.info(f"manual_pagamentos_realizados: {len(df)} registros.")

def sync_recebimentos_manual():
    file_path = 'dashboards/support_tables/7B_Recebimentos Realizados.xlsx'
    if not os.path.exists(file_path): return
    logger.info("Sincronizando Recebimentos Manuais...")
    df = pd.read_excel(file_path)
    engine = get_engine()
    save_to_db(df, "manual_recebimentos", engine)

if __name__ == "__main__":
    sync_mapa_faturamento()
    sync_contas_pagar_manual()
    sync_pagamentos_manual()
    sync_recebimentos_manual()
