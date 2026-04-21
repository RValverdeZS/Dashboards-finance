# Omie API Dashboard Integration

Este projeto fornece uma estrutura completa para integrar a API da Omie com um banco de dados **PostgreSQL**, facilitando a criao de dashboards no Power BI, Tableau ou outras ferramentas.

## Funes Principais
- **Sincronizao Automtica:** Script Python que busca dados de Clientes, Produtos, Pedidos, Notas Fiscais e Lanamentos Financeiros.
- **Lidando com Paginao:** O client (`omie_client.py`) gerencia automaticamente mltiplas pginas de dados da Omie.
- **Base para Dashboards:** Armazena os dados em Tabelas SQL, permitindo consultas rpidas e histricos.

## Como Usar
1. Instale as dependncias: `pip install -r requirements.txt`
2. Configure o arquivo `.env` com suas chaves (veja o `.env.example`).
3. Execute a sincronizao: `python sync.py`

## Power BI
Conecte o Power BI diretamente ao seu PostgreSQL ou use o template em `PowerQuery_Template.m` para consultas rpidas via Web (POST).
