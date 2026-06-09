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

    plt.figure(figsize=(12, 6))

    # Plota a Vazão da Rede (Política 2)
    plt.plot(df_p2["segment"], df_p2["vazão_kbps"], 
             label="Vazão Medida da Rede (Cenário)", color='black', linestyle='--', alpha=1)

    # Plota o Bitrate da Política 1 (Baseline)
    plt.step(df_base["segment"], df_base["bitrate_kbps"], 
             label="Política 1: Rate-Based (Baseline)", marker='o', linestyle='-', color='#d62728', where='mid')

    # Plota o Bitrate da Política 2 (HybridABR)
    plt.step(df_p2["segment"], df_p2["bitrate_kbps"], 
             label="Política 2: Histerese + Buffer", marker='s', linestyle='-', color='#1f77b4', where='mid', linewidth=2)

    # Configurações do gráfico
    plt.title("Comparação de Políticas ABR: Baseline vs Híbrida")
    plt.xlabel("Número do Segmento")
    plt.ylabel("Taxa de Transferência (kbps)")
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc="upper left")

    # Salva e exibe
    caminho_imagem = "docs/comparacao_final.png"
    plt.savefig(caminho_imagem, dpi=300, bbox_inches="tight")
    print(f"Gráfico comparativo salvo em '{caminho_imagem}'")
    plt.show()

if __name__ == "__main__":
    plotar_comparacao("docs/dados_baseline.csv", "docs/dados_politica2.csv")