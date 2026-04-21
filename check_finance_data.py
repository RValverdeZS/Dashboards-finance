import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL)

def check():
    try:
        df_pagar = pd.read_sql("SELECT * FROM omie_contas_pagar LIMIT 1", engine)
        print("Colunas que contm 'valor' ou 'fornec' ou 'cliente' em 'omie_contas_pagar':")
        print([c for c in df_pagar.columns if 'valor' in c or 'fornec' in c or 'cliente' in c])
        
        df_receber = pd.read_sql("SELECT * FROM omie_contas_receber LIMIT 1", engine)
        print("\nColunas que contm 'valor' ou 'fornec' ou 'cliente' em 'omie_contas_receber':")
        print([c for c in df_receber.columns if 'valor' in c or 'fornec' in c or 'cliente' in c])
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check()
