import os
import json
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL)

def check():
    try:
        df_pedidos = pd.read_sql("SELECT \"cabecalho.codigo_pedido\", det FROM omie_pedidos_venda LIMIT 1", engine)
        det_json = json.loads(df_pedidos['det'].iloc[0])
        first_item = det_json[0]
        
        if 'produto' in first_item:
             print("\n--- Chaves dentro de 'produto' ---")
             print(first_item['produto'].keys())
             for k, v in first_item['produto'].items():
                 print(f"{k}: {v}")
        
    except Exception as e:
        print(f"Erro ao verificar dados: {e}")

if __name__ == "__main__":
    check()
