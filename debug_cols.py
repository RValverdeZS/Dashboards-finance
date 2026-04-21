import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL)

def check():
    try:
        print("--- PEGANDO UMA LINHA COMPLETA COM NOMES DE COLUNA ---")
        df = pd.read_sql("SELECT * FROM omie_contas_receber LIMIT 1", engine)
        if df.empty:
            print("TABELA VAZIA!")
            return
            
        print("COLUNAS QUE REALMENTE EXISTEM:")
        all_cols = sorted(df.columns.tolist())
        for c in all_cols:
            print(f"'{c}'")
            
        print("\nEXEMPLO DA PRIMEIRA LINHA:")
        print(df.iloc[0].to_dict())
            
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check()
