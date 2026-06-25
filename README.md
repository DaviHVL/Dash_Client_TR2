# Cliente DASH Adaptativo com Controle de Banda e Failover

Este repositório contém a implementação de um cliente streaming simplificado baseado no protocolo **DASH (Dynamic Adaptive Streaming over HTTP)** em Python puro. O projeto foi desenvolvido como trabalho final para a disciplina de *Teleinformática e Redes 2 (TR2)* na Universidade de Brasília (UnB).

O ecossistema é capaz de gerenciar o saldo temporal de mídia armazenada localmente (buffer), mitigar variações agudas na camada de transporte por meio de filtros e realizar a recuperação automática de falhas de infraestrutura (*failover*) de forma síncrona.

---

## Recursos Implementados

* **Parser Dinâmico de Manifesto:** Leitura estruturada do arquivo JSON obtido diretamente do servidor.
* **Gerenciamento Avançado de Buffer:** Simulação precisa de reprodução contínua (*continuous play*) com mecanismos ativos de retenção (*throttling*) e teto regulamentar (*capping*).
* **Três Políticas ABR Distintas:** Algoritmos que vão desde a abordagem puramente reativa até motores analíticos focados em Qualidade de Experiência (QoE).
* **Mecanismo de Tolerância a Falhas:** Sistema defensivo com monitoramento proativo de saúde (*health checks*) e captura reativa de exceções de rede.
* **Telemetria Completa:** Geração automatizada de logs estruturados em formato `.csv` contendo 14 campos regulamentares para auditoria de tráfego.

---

## Estrutura do Projeto

O código foi projetado seguindo princípios de modularidade e orientação a objetos:

* `config.py`: Concentra todas as constantes operacionais do ecossistema (URLs, durações e limiares de buffer).
* `main.py`: Orquestrador central síncrono que coordena o loop principal de requisições de mídia de todas as políticas.
* `abr.py`: Arquitetura onde residem as classes dos motores de decisão adaptativa (`RateBasedABR`, `HybridABR` e `AdaptiveHybridABR`).
* `buffer_manager.py`: Máquina de estados do buffer local encarregada de computar o saldo temporal, travar o crescimento e contabilizar congelamentos de tela (*stalls*).
* `network.py`: Subsistema de rede responsável pelas requisições HTTP por chunks, cálculo de jitter por blocos e gerência de servidores (*ServerManager*).
* `metrics_logger.py`: Camada de persistência em disco encarregada de registrar e auditar as métricas de sessão.
* `utils.py`: Funções utilitárias auxiliares para tratamento de tempo no padrão ISO 8601 e equações de vazão útil.
* `comparar_politicas.py`: Script analítico para renderização de curvas de desempenho sobrepostas.

---

## Políticas de Adaptação de Bitrate (ABR)

### 1. Política 1 (Baseline — Rate-Based Puro)
Seleciona a representação de maior qualidade cujo bitrate seja estritamente inferior à vazão medida no exato segmento anterior, aplicando uma margem de segurança fixa (`SAFETY_FACTOR = 0.92`). Não possui memória ou consciência do estado do buffer.

### 2. Política 2 (Híbrida — Buffer-Aware + Histerese)
Abandona a dependência unilateral da última amostra e introduz uma **Janela Deslizante de 3 Segmentos** para suavizar a leitura de banda. Utiliza o nível do buffer como modulador de confiança dividindo a operação em três estados:
* **Modo Emergência (< 4s):** Força o recuo imediato para 240p para estancar riscos de travamento.
* **Modo Conservador ($\le$ 10s):** Limita o crescimento aplicando um fator restritivo sobre a banda média.
* **Modo Confiança Total (> 10s):** Remove travas de segurança permitindo saltos agressivos de bitrate.
* *Histerese:* Quedas de qualidade ocorrem de forma imediata, mas subidas exigem duas confirmações consecutivas e ocorrem em degraus de apenas um nível por vez.

### 3. Política 3 (Híbrida Adaptativa — Amortecida por Jitter)
Adiciona à lógica híbrida da Política 2 um monitoramento de variabilidade temporal da rede. O jitter microscópico entre chunks de um mesmo segmento é suavizado por meio de uma **Média Móvel Exponencial Ponderada (EWMA)** com peso $\alpha = 0.125$. O valor resultante atua como um indexador ativo de penalização de largura de banda, injetando um viés conservador inteligente quando o canal apresenta alta instabilidade de latência.

---

## Limiares Regulamentares do Buffer

Os parâmetros de controle de fluxo configurados no arquivo `config.py` mapeiam as diretrizes comerciais de players de vídeo do mercado:

| Parâmetro Constante | Valor | Função no Sistema |
| :--- | :---: | :--- |
| `BUFFER_MAX_S` | `30.0s` | Teto máximo físico de alocação de mídia local. |
| `BUFFER_TARGET_S` | `15.0s` | Nível alvo. Acima dele, o cliente ativa o *throttling* via `time.sleep()`. |
| `BUFFER_MIN_S` | `4.0s` | Zona de risco iminente de rebufferização. |
| `BUFFER_CRITICAL_S` | `1.0s` | Limiar crítico de esvaziamento total (dispara a contagem de *stall*). |

---

## Pré-requisitos e Como Executar

### Pré-requisitos
O cliente DASH foi projetado para rodar em **Python 3.6 ou superior** utilizando apenas bibliotecas nativas para sua execução principal. A biblioteca `requests` é exigida para a comunicação de rede, e as bibliotecas `pandas` e `matplotlib` são necessárias para a geração dos gráficos analíticos.

Instale as dependências executando:
```bash
pip install requests pandas matplotlib
```

## Execução do Cliente
 
Para rodar a simulação síncrona das três políticas simultaneamente e gerar os arquivos de logs CSV na pasta `docs/`, execute:
 
```bash
python main.py
```
 
---
 
## Geração dos Gráficos Analíticos
 
Após a conclusão das sessões, você pode gerar de forma unificada os gráficos comparativos exigidos para o relatório final (Vazão vs. Bitrate com linhas verticais de failover, curvas dinâmicas de buffer e comportamento do Jitter EWMA) rodando o script:
 
```bash
python comparar_politicas.py
```
 
As imagens em alta resolução (`.png`) serão salvas automaticamente dentro do diretório `docs/`.
 
---
 
## Matriz de Logs de Auditoria (CSV)
 
Cada linha gerada nos arquivos de telemetria dentro da pasta `docs/` mapeia detalhadamente o comportamento do player em rede por meio de 14 campos estruturados:
 
| Campo | Descrição |
|---|---|
| `segment` | Identificador sequencial do bloco de vídeo. |
| `timestamp` | Carimbo de data e hora no padrão ISO 8601. |
| `server_id` | Identificação do nó ativo (`A` para principal na porta 8080 ou `srv-B` para fallback na porta 8081). |
| `quality` | Resolução nominal selecionada pelo motor ABR (240p a 1080p). |
| `bitrate_kbps` | Taxa de bits nominal da representação escolhida. |
| `vazão_kbps` | Velocidade líquida de download medida na iteração. |
| `download_time_s` | Tempo total gasto na rodada de transferência física. |
| `jitter_network_ms` | Jitter instantâneo medido entre os blocos do segmento. |
| `jitter_ewma_ms` | Histórico do jitter suavizado exponencialmente. |
| `buffer_level_s` | Saldo temporal instantâneo restante no player. |
| `buffer_can_play` | Flag booleana (`1` se havia mídia suficiente para continuous play, `0` em caso de congelamento). |
| `rebuffer_event` | Sinalizador de ocorrência de travamento no bloco atual. |
| `stall_duration_s` | Magnitude exata da rebufferização medida em segundos. |
| `failover_total` | Acumulador atômico do número de migrações de servidores executadas. |
 
---
 
## Integrantes do Grupo
 
| Nome | Matrícula |
|---|---|
| Caio Medeiros Balaniuk | 231025190 |
| Davi Henrique Vieira Lima | 231013529 |
| Isaac Silva | 231025216 |