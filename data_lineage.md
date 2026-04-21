# Data Lineage - Omie ERP Integration

This document describes the flow of data from Omie ERP to the PostgreSQL database and the subsequent views used in the BI dashboards.

## 1. Data Sources (Sync Process)

The `sync.py` script performs a full sync (Truncate & Append) for the following modules:

| Table Name | Omie Endpoint | Omie Method | Key Purpose |
|------------|---------------|-------------|-------------|
| `omie_clientes` | `geral/clientes` | `ListarClientes` | Base for customers and suppliers. |
| `omie_produtos` | `geral/produtos` | `ListarProdutos` | Catalog for sales analysis. |
| `omie_pedidos_venda` | `produtos/pedido` | `ListarPedidos` | Sales pipeline and order details. |
| `omie_notas_fiscais` | `produtos/nf_consultar` | `ListarNF` | Product billing (Revenue). |
| `omie_nfse` | `servicos/nfse` | `ListarNFSE` | Service billing (Revenue). |
| `omie_contratos` | `servicos/contrato` | `ListarContratos` | Contract totals and recurring service data. |
| `omie_contas_receber` | `financas/contareceber` | `ListarContasReceber` | Accounts receivable / Cash flow projection. |
| `omie_contas_pagar` | `financas/contapagar` | `ListarContasPagar` | Accounts payable / Cash flow projection. |
| `omie_lancamentos_financeiros` | `financas/contacorrentelancamentos` | `ListarLancCC` | Bank movements/reconciliation (Actualized Cash Flow). |
| `omie_categorias` | `geral/categorias` | `ListarCategorias` | Financial classification hierarchy. |
| `omie_projetos` | `geral/projetos` | `ListarProjetos` | Cost center / Project grouping. |

## 2. Dynamic Metric Calculations

To ensure data integrity, the following metrics are now calculated dynamically from Omie data, avoiding hardcoded manual entries:

### Valor do Contrato
- **Source**: `omie_contratos`
- **Logic**: Sum of all contract values registered in the ERP.
- **View**: `v_dashboard_kpis_contrato`

### Faturamento Total
- **Source**: Union of `omie_notas_fiscais` and `omie_nfse`.
- **Logic**: Combines billing from both products and services for a 100% view of revenue.

## 3. Support Data Dependencies (Fragile Blocks)

The following logic still depends on manual data entry patterns in Omie:

- **Amortizations/Performance/Insurance**: Extracted via REGEX from the `detalhes.cObs` field in `omie_lancamentos_financeiros`. It is critical that these descriptions follow the standard pattern:
    - `Amortização: [Valor]`
    - `PERFORMANCE: [Valor]`
    - `SEGURO: [Valor]`

## 4. Maintenance / Update Frequency

- **Sync Command**: `python sync.py`
- **Views Update**: Run `create_finance_views.sql` in the database after any schema change.
