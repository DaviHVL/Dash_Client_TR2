import pandas as pd
import matplotlib.pyplot as plt
import os

def plotar_comparacao(csv_baseline, csv_politica2):
    if not os.path.exists(csv_baseline) or not os.path.exists(csv_politica2):
        print("ERRO: É preciso executar as duas políticas antes de gerar a comparação")
        print(f"Verifique se {csv_baseline} e {csv_politica2} existem.")
        return

    # Lê os dados gerados
    df_base = pd.read_csv(csv_baseline)
    df_p2 = pd.read_csv(csv_politica2)

    # Garante que o diretório "docs" existe antes de salvar
    os.makedirs("docs", exist_ok=True)

    # Inicializa a variável com escopo correto para ser usada por todos os gráficos
    segmento_failover = None

    # ==========================================================
    # GRÁFICO 1: POLÍTICA 1 (RATE-BASED / BASELINE)
    # ==========================================================
    plt.figure(figsize=(12, 6))

    # Plota a Vazão da Rede 
    plt.plot(df_p2["segment"], df_p2["vazão_kbps"], 
             label="Vazão Medida da Rede (kbps)", color='black', linestyle='--', marker='o', alpha=1)

    # Plota o Bitrate da Política 1
    plt.step(df_base["segment"], df_base["bitrate_kbps"], 
             label="Política 1: Rate-Based (Baseline)", marker='o', linestyle='-', color='#d62728', where='mid')

    # Adiciona os rótulos com a QUALIDADE escolhida (abaixo do ponto para não sobrepor)
    for i, row in df_base.iterrows():
        plt.annotate(row["quality"], (row["segment"], row["bitrate_kbps"]), 
                     textcoords="offset points", xytext=(0,-12), ha='center', fontsize=8, color='#d62728')

    plt.title("Desempenho ABR - Política 1 (Baseline)")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Taxa de Transferência (kbps)")
    plt.xticks(df_p2["segment"]) 
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")

    caminho_imagem_p1 = "docs/grafico_politica1.png"
    plt.savefig(caminho_imagem_p1, dpi=300, bbox_inches="tight")
    print(f"Gráfico da Política 1 salvo em '{caminho_imagem_p1}'")
    plt.show() 

    # ==========================================================
    # GRÁFICO 2: POLÍTICA 2 (HÍBRIDA)
    # ==========================================================
    plt.figure(figsize=(12, 6))

    # Plota a Vazão da Rede
    plt.plot(df_p2["segment"], df_p2["vazão_kbps"], 
             label="Vazão Medida da Rede (kbps)", color='black', linestyle='--', marker='o', alpha=1)

    # Plota o Bitrate da Política 2
    plt.step(df_p2["segment"], df_p2["bitrate_kbps"], 
             label="Política 2: Histerese + Buffer", marker='s', linestyle='-', color='#1f77b4', where='mid', linewidth=2)

    # Adiciona os rótulos com a QUALIDADE escolhida (abaixo do ponto para não sobrepor)
    for i, row in df_p2.iterrows():
        plt.annotate(row["quality"], (row["segment"], row["bitrate_kbps"]), 
                     textcoords="offset points", xytext=(0,-12), ha='center', fontsize=8, color='#1f77b4')

    plt.title("Desempenho ABR - Política 2 (Híbrida)")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Taxa de Transferência (kbps)")
    plt.xticks(df_p2["segment"]) 

    # Detecta e indica visualmente onde ocorreu o Failover (Apenas na P2)
    teve_failover = False
    if "failover_total" in df_p2.columns:
        for i in range(1, len(df_p2)):
            if df_p2.loc[i, "failover_total"] > df_p2.loc[i-1, "failover_total"]:
                segmento_failover = df_p2.loc[i, "segment"]
                
                label_f = "Queda de Servidor (Failover)" if not teve_failover else ""
                plt.axvline(x=segmento_failover, color='red', linestyle='-.', linewidth=2, label=label_f)
                
                plt.annotate("Failover!", (segmento_failover, plt.ylim()[1] * 0.95), 
                             textcoords="offset points", xytext=(5,0), ha='left', color='red', fontweight='bold')
                teve_failover = True

    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")

    caminho_imagem_p2 = "docs/grafico_politica2.png"
    plt.savefig(caminho_imagem_p2, dpi=300, bbox_inches="tight")
    print(f"Gráfico da Política 2 salvo em '{caminho_imagem_p2}'")
    plt.show()

    # ==========================================================
    # GRÁFICO 3: EVOLUÇÃO DO NÍVEL DO BUFFER COM REBUFFERING
    # ==========================================================
    plt.figure(figsize=(12, 5))
    
    # Adição dos limites regulamentares e comerciais do protocolo DASH
    plt.axhline(y=15.0, color='green', linestyle=':', alpha=0.6, label="Alvo ($15\\text{s}$)")
    plt.axhline(y=30.0, color='red', linestyle=':', alpha=0.6, label="Teto ($30\\text{s}$)")
    plt.axhline(y=4.0, color='orange', linestyle=':', alpha=0.6, label="Mínimo ($4\\text{s}$)")

    # Curvas contínuas das duas políticas
    plt.plot(df_base["segment"], df_base["buffer_level_s"], 
             label="Política 1: Baseline", color='#d62728', linestyle='-', marker='o', alpha=0.8)
    plt.plot(df_p2["segment"], df_p2["buffer_level_s"], 
             label="Política 2: Híbrida", color='#1f77b4', linestyle='-', marker='s', alpha=0.8)

    # Identificação e marcação proativa de eventos de Rebuffering (Mapeamento de Stalls)
    df_base_rebuf = df_base[df_base["rebuffer_event"] == 1]
    if not df_base_rebuf.empty:
        plt.scatter(df_base_rebuf["segment"], df_base_rebuf["buffer_level_s"], 
                    color='red', marker='X', s=150, zorder=5, label="Rebuffering (P1)")
        for _, row in df_base_rebuf.iterrows():
            plt.annotate(f"Stall! {row['stall_duration_s']:.1f}s", (row["segment"], row["buffer_level_s"]),
                         textcoords="offset points", xytext=(0, 10), ha='center', color='red', fontweight='bold', fontsize=9)

    df_p2_rebuf = df_p2[df_p2["rebuffer_event"] == 1]
    if not df_p2_rebuf.empty:
        plt.scatter(df_p2_rebuf["segment"], df_p2_rebuf["buffer_level_s"], 
                    color='darkred', marker='X', s=150, zorder=5, label="Rebuffering (P2)")
        for _, row in df_p2_rebuf.iterrows():
            plt.annotate(f"Stall! {row['stall_duration_s']:.1f}s", (row["segment"], row["buffer_level_s"]),
                         textcoords="offset points", xytext=(0, 10), ha='center', color='darkred', fontweight='bold', fontsize=9)

    # Linha vertical unificada para registrar o impacto do Failover no amortecimento
    if segmento_failover is not None:
        plt.axvline(x=segmento_failover, color='red', linestyle='-.', linewidth=2, label="Failover (Srv A $\\rightarrow$ B)")

    plt.title("Evolução Dinâmica do Nível do Buffer")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Nível do Buffer ($s$)")
    plt.xticks(df_p2["segment"])
    plt.ylim(0, max(max(df_base["buffer_level_s"]), max(df_p2["buffer_level_s"]), 30) + 5)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")
    plt.savefig("docs/grafico_buffer.png", dpi=300, bbox_inches="tight")
    plt.show()
    print("Gráfico do Buffer salvo com sucesso em 'docs/grafico_buffer.png'")

    # ==========================================================
    # GRÁFICO 4: EVOLUÇÃO DO JITTER (INSTANTÂNEO VS EWMA)
    # ==========================================================
    plt.figure(figsize=(12, 5))
    
    for i in range(len(df_p2)):
        seg = df_p2.loc[i, "segment"]
        srv = str(df_p2.loc[i, "server_id"]).strip()
        
        cor_fundo = '#fff7ec' if 'A' in srv or 'A' == srv else '#f2f0f7'
        plt.axvspan(seg - 0.5, seg + 0.5, color=cor_fundo, alpha=0.7, zorder=1)

    df_srv_a = df_p2[df_p2["server_id"].astype(str).str.contains('A', na=False)]
    df_srv_b = df_p2[~df_p2["server_id"].astype(str).str.contains('A', na=False)]

    plt.plot(df_p2["segment"], df_p2["variação de atraso (jitter)_network_ms"], 
             color="#000000", linestyle=':', linewidth=1.2, label="Jitter Instantâneo (Por Segmento)", zorder=2)

    plt.plot(df_p2["segment"], df_p2["variação de atraso (jitter)_ewma_ms"], 
             color='#4a4a4a', linestyle='-', linewidth=1.5, label="Jitter EWMA", zorder=3)

    plt.scatter(df_srv_a["segment"], df_srv_a["variação de atraso (jitter)_ewma_ms"], 
                color='#d62728', marker='o', s=65, label="Conexão: Servidor A (8080)", zorder=4)
    plt.scatter(df_srv_b["segment"], df_srv_b["variação de atraso (jitter)_ewma_ms"], 
                color='#1f77b4', marker='s', s=65, label="Conexão: Servidor B (8081)", zorder=4)

    if segmento_failover is not None:
        plt.axvline(x=segmento_failover, color='red', linestyle='-.', linewidth=2.5, label="Instante do Failover")
        
        max_y_real = max(df_p2["variação de atraso (jitter)_network_ms"].max(), df_p2["variação de atraso (jitter)_ewma_ms"].max())
        posicao_y_texto = max_y_real * 0.85
        
        plt.text(segmento_failover / 2, posicao_y_texto, "SERVIDOR A\n(Porta 8080)", 
                 color='#b35806', fontsize=11, fontweight='bold', ha='center', va='center', alpha=0.85, zorder=5)
        
        seg_max = df_p2["segment"].max()
        plt.text(segmento_failover + (seg_max - segmento_failover) / 2, posicao_y_texto, "SERVIDOR B\n(Porta 8081)", 
                 color='#542788', fontsize=11, fontweight='bold', ha='center', va='center', alpha=0.85, zorder=5)

    plt.title("Jitter Instantâneo vs Jitter EWMA")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Variação de Atraso / Jitter ($ms$)")
    plt.xticks(df_p2["segment"])
    plt.grid(True, linestyle=':', alpha=0.4, zorder=1)
    plt.legend(loc="upper left")
    
    plt.savefig("docs/grafico_jitter.png", dpi=300, bbox_inches="tight")
    plt.show()
    print("Gráfico do Jitter EWMA salvo com sucesso em 'docs/grafico_jitter.png'")

if __name__ == "__main__":
    plotar_comparacao("docs/dados_baseline.csv", "docs/dados_politica2.csv")