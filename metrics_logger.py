import csv
import pandas as pd
import matplotlib.pyplot as plt
import os

class MetricsLogger:
    def __init__(self, arquivo, entrega=""):
        self.arquivo = arquivo
        self.entrega = entrega 

        pasta = os.path.dirname(self.arquivo)
        
        if pasta and not os.path.exists(pasta):
            os.makedirs(pasta)
        
        self.cabecalho = [
            "segment", "timestamp", "server_id", "quality", "bitrate_kbps",
            "vazão_kbps", "download_time_s", "variação de atraso (jitter)_network_ms",
            "variação de atraso (jitter)_ewma_ms", "buffer_level_s",
            "buffer_can_play", "rebuffer_event", "stall_duration_s", "failover_total"
        ]
        
        with open(self.arquivo, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.cabecalho)

    def log_segment(self, dados_dict):
        # Mapeia as chaves do dicionário para a ordem exata do cabeçalho.
        linha = [
            dados_dict.get("segment", 0),
            dados_dict.get("timestamp", ""),
            dados_dict.get("server_id", "A"),
            dados_dict.get("quality", ""),
            dados_dict.get("bitrate_kbps", 0.0),
            dados_dict.get("vazao_kbps", 0.0),         
            dados_dict.get("download_time_s", 0.0),
            dados_dict.get("jitter_network_ms", 0.0), 
            dados_dict.get("jitter_ewma_ms", 0.0),   
            dados_dict.get("buffer_level_s", 0.0),
            dados_dict.get("buffer_can_play", 1),
            dados_dict.get("rebuffer_event", 0),
            dados_dict.get("stall_duration_s", 0.0),
            dados_dict.get("failover_total", 0)
        ]
        
        # Adiciona a linha no final do arquivo
        with open(self.arquivo, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(linha)

    def plotar_grafico(self):
        # Lê os dados do CSV que acabamos de gerar
        try:
            df = pd.read_csv(self.arquivo)
        except FileNotFoundError:
            print(f"Erro: O arquivo {self.arquivo} não foi encontrado.")
            return

        # Define o tamanho da figura 
        plt.figure(figsize=(10, 6))
        
        # Eixo Y 1: Plota a Vazão Medida 
        plt.plot(df["segment"], df["vazão_kbps"], 
                 label="Vazão Medida da Rede (kbps)", marker='o', linestyle='-', color='#1f77b4')
        
        # Eixo Y 2: Plota o Bitrate Selecionado 
        plt.step(df["segment"], df["bitrate_kbps"], 
                 label="Qualidade Selecionada (kbps)", marker='s', linestyle='--', color='#ff7f0e', where='mid')

        # Títulos, legendas e grade
        titulo_base = "Desempenho ABR: Vazão da Rede vs Qualidade Selecionada"
        if self.entrega:
            plt.title(f"{titulo_base} - Política {self.entrega}")
        else:
            plt.title(titulo_base)
        plt.xlabel("Número do Segmento")
        plt.ylabel("Taxa de Transferência (kbps)")
        
        # Adiciona os rótulos de qualidade 
        for i, row in df.iterrows():
            plt.annotate(row["quality"], (row["segment"], row["bitrate_kbps"]), 
                         textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend(loc="upper left")
        
        # Salva a imagem na mesma pasta e a exibe na tela
        nome_imagem = self.arquivo.replace(".csv", ".png")
        plt.savefig(nome_imagem, dpi=300, bbox_inches="tight")
        plt.show()