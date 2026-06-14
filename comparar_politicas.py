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

    # ==========================================================
    # GRÁFICO 1: POLÍTICA 1 (RATE-BASED / BASELINE)
    # ==========================================================
    plt.figure(figsize=(12, 6))

    # Plota a Vazão da Rede (sempre baseada na P2 para manter o mesmo cenário)
    plt.plot(df_p2["segment"], df_p2["vazão_kbps"], 
             label="Vazão Medida da Rede (Cenário)", color='black', linestyle='--', marker='o', alpha=1)

    # Plota o Bitrate da Política 1
    plt.step(df_base["segment"], df_base["bitrate_kbps"], 
             label="Política 1: Rate-Based (Baseline)", marker='o', linestyle='-', color='#d62728', where='mid')

    plt.title("Desempenho ABR - Política 1 (Baseline)")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Taxa de Transferência (kbps)")
    plt.xticks(df_p2["segment"]) # Apenas números naturais no eixo X
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")

    caminho_imagem_p1 = "docs/grafico_politica1.png"
    plt.savefig(caminho_imagem_p1, dpi=300, bbox_inches="tight")
    print(f"Gráfico da Política 1 salvo em '{caminho_imagem_p1}'")
    plt.show() # Exibe o primeiro gráfico (feche a janela para ver o segundo)

    # ==========================================================
    # GRÁFICO 2: POLÍTICA 2 (HÍBRIDA)
    # ==========================================================
    plt.figure(figsize=(12, 6))

    # Plota a Vazão da Rede
    plt.plot(df_p2["segment"], df_p2["vazão_kbps"], 
             label="Vazão Medida da Rede (Cenário)", color='black', linestyle='--', marker='o', alpha=1)

    # Plota o Bitrate da Política 2
    plt.step(df_p2["segment"], df_p2["bitrate_kbps"], 
             label="Política 2: Histerese + Buffer", marker='s', linestyle='-', color='#1f77b4', where='mid', linewidth=2)

    plt.title("Desempenho ABR - Política 2 (Híbrida)")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Taxa de Transferência (kbps)")
    plt.xticks(df_p2["segment"]) # Apenas números naturais no eixo X

    # Detecta e indica visualmente onde ocorreu o Failover (Apenas na P2)
    teve_failover = False
    if "failover_total" in df_p2.columns:
        for i in range(1, len(df_p2)):
            if df_p2.loc[i, "failover_total"] > df_p2.loc[i-1, "failover_total"]:
                segmento_falha = df_p2.loc[i, "segment"]
                
                label_f = "Queda de Servidor (Failover)" if not teve_failover else ""
                plt.axvline(x=segmento_falha, color='red', linestyle='-.', linewidth=2, label=label_f)
                
                plt.annotate("Failover!", (segmento_falha, plt.ylim()[1] * 0.95), 
                             textcoords="offset points", xytext=(5,0), ha='left', color='red', fontweight='bold')
                teve_failover = True

    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")

    caminho_imagem_p2 = "docs/grafico_politica2.png"
    plt.savefig(caminho_imagem_p2, dpi=300, bbox_inches="tight")
    print(f"Gráfico da Política 2 salvo em '{caminho_imagem_p2}'")
    plt.show()

if __name__ == "__main__":
    plotar_comparacao("docs/dados_baseline.csv", "docs/dados_politica2.csv")