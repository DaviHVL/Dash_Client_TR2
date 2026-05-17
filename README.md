# Guia de Arquitetura do Cliente DASH - Entrega 1

## 1. `main.py` (O Maestro)
**Status:** Praticamente pronto.
**Responsabilidade:** Orquestrar o fluxo do programa.
* Ele não calcula nada sozinho. Ele pega os dados da rede, passa para o buffer, pede a decisão para o ABR e manda o logger gravar.
* **O que falta:** O arquivo atual já faz o que é necessário para a Entrega 1. Vocês só precisarão ajustá-lo se quiserem adicionar prints de debug ou formatar a saída no terminal para ficar mais legível.

## 2. `config.py` (As Constantes)
**Status:** Pronto.
**Responsabilidade:** Guardar os parâmetros globais do sistema.
* Centralizar variáveis como `MANIFEST_URL`, tamanho do buffer e fatores de segurança evita "números mágicos" espalhados pelo código.
* `SAFETY_FACTOR = 0.8`: Fator de 80% usado no algoritmo Rate-Based para evitar escolhas excessivamente otimistas.

## 3. `network.py` (Módulo de Rede)
**Status:** Precisa ser implementado.
**Responsabilidade:** Fazer as requisições HTTP e medir o tempo.
* **`baixar_manifesto(url)`**: Deve fazer um `requests.get()` na URL e retornar os dados em formato de dicionário (`.json()`).
* **`baixar_segmento(url)`**: **A função mais complexa da Entrega 1.**
    * Vocês precisam usar `requests.get(url, stream=True)` para baixar o vídeo em pedaços (chunks).
    * É obrigatório medir o tempo exato que cada pedaço demora para chegar. A variação de tempo entre eles é o **Jitter**.
    * Precisa calcular o tempo total de download (`t_fim - t_inicio`).
    * Deve retornar um dicionário com: `vazao_kbps` (pode chamar a função do `utils.py`), `download_time_s` e `jitter_network_ms`.

## 4. `buffer_manager.py` (O Simulador do Player)
**Status:** Precisa ser implementado.
**Responsabilidade:** Controlar o "tempo de vídeo" que o usuário tem carregado e se a tela congelou.
* **`__init__`**: Iniciar uma variável como `self.buffer_level_s = 0.0`.
* **`atualizar_buffer(...)`**: 
    1. Deduzir o `tempo_de_download_s` do `buffer_level_s`.
    2. Verificar se o buffer ficou negativo. Se sim, o vídeo travou! Registre `rebuffer_event = 1` e calcule o `stall_duration_s`. O buffer não pode ser menor que zero.
    3. Saber se `buffer_can_play` é 1 ou 0 no momento em que o segmento terminou de baixar.
    4. Adicionar a `duracao_segmento_s` ao buffer.
    5. Retornar um dicionário com os dados de estado para o `main.py` colocar no CSV.

## 5. `abr.py` (A Inteligência do Cliente)
**Status:** Precisa ser implementado.
**Responsabilidade:** Escolher a qualidade ideal do próximo segmento.
* **`__init__`**: Deve receber o dicionário do manifesto, extrair a lista de qualidades e ordená-la (do maior para o menor bitrate).
* **`escolher_qualidade(vazao_medida_kbps)`**:
    * **Cold Start:** Se a `vazao_medida_kbps` for 0 (primeira rodada), retorne a menor qualidade possível (ex: 240p).
    * Se não for zero, multiplique a vazão pelo `SAFETY_FACTOR` (0.8) definido no `config.py` para obter a **banda estimada**.
    * Percorra a lista de qualidades ordenadas e retorne a primeira cujo bitrate exigido seja **menor ou igual** à banda estimada.
    * Retorne a URL formatada do segmento, a qualidade e o bitrate.

## 6. `metrics_logger.py` (Gravação de Dados e Gráficos)
**Status:** Precisa ser implementado.
**Responsabilidade:** Salvar a história no CSV exato e plotar os resultados.
* **`__init__`**: Deve criar o arquivo CSV (ex: `dados_entrega1.csv`) e escrever a linha de cabeçalho **exatamente** com os mesmos nomes solicitados no PDF do professor.
* **`log_segment(dados_dict)`**: Pega o dicionário criado no `main.py` e escreve uma nova linha no arquivo.
* **`plotar_grafico()`**: Usando a biblioteca `matplotlib` (ou `pandas` + `matplotlib`), lê o CSV recém-criado e plota um gráfico mostrando o "Segmento" no Eixo X e a "Vazão vs Qualidade Selecionada" no Eixo Y.

## 7. `utils.py` (Funções Auxiliares)
**Status:** Precisa ser implementado.
**Responsabilidade:** Manter funções utilitárias que podem ser usadas em vários lugares, deixando os arquivos principais mais limpos.
* **`calcular_vazao(bytes, tempo)`**: Pega o tamanho do arquivo recebido e o tempo total em segundos, faz a matemática (`(bytes * 8 / 1000) / tempo`) e devolve em kbps.
* **`timestamp_iso()`**: Retorna a hora atual no formato ISO 8601 (ex: usando `datetime.datetime.now().isoformat()`).

---