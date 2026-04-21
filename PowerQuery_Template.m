let
    // ---------------------------------------------------------
    // TEMPLATE PARA CONEXO DIRETA POWER BI -> OMIE
    // ---------------------------------------------------------
    // Use este script no "Editor Avanado" do Power BI
    
    // 1. Defina suas credenciais
    AppKey = "SEU_APP_KEY",
    AppSecret = "SEU_APP_SECRET",
    
    // 2. Defina o Endpoint e o Mtodo
    // Ex: geral/clientes/ e ListarClientes
    Url = "https://app.omie.com.br/api/v1/geral/clientes/",
    Metodo = "ListarClientes",
    
    // 3. Montagem do Corpo (Body) do POST
    Body = Json.FromValue([
        call = Metodo,
        app_key = AppKey,
        app_secret = AppSecret,
        param = { [ pagina = 1, registros_por_pagina = 100, apenas_importado_api = "N" ] }
    ]),
    
    // 4. Execuo da Requisio
    Response = Web.Contents(Url, [
        Headers = [#"Content-Type"="application/json"],
        Content = Body
    ]),
    
    // 5. Tratamento do JSON
    Source = Json.Document(Response),
    
    // 6. Extrao da Lista (Exemplo para Clientes)
    // O nome da chave varia conforme o mtodo (ex: 'clientes_cadastro')
    ListaDeDados = Source[clientes_cadastro],
    Table = Table.FromList(ListaDeDados, Splitter.SplitByNothing(), null, null, ExtraValues.Error)
in
    Table
