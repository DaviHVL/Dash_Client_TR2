import time
from config import MANIFEST_URL, NUM_SEGMENTS, SEGMENT_DURATION, BUFFER_TARGET_S 
from network import baixar_manifesto, baixar_segmento, ServerManager
from buffer_manager import BufferManager
from abr import RateBasedABR, HybridABR
from metrics_logger import MetricsLogger
from utils import timestamp_iso
from comparar_politicas import plotar_comparacao  

def main():
    print("Iniciando Cliente DASH - Entrega 2 (Política Híbrida)...")
    
    # Inicializa os dois loggers (Entrega 1 e 2)
    logger_p1 = MetricsLogger("docs/dados_baseline.csv", "1")
    logger_p2 = MetricsLogger("docs/dados_politica2.csv", "2")
    
    # Inicialização independente dos buffers para garantir a fidelidade dos logs
    buffer_p1 = BufferManager()
    buffer_p2 = BufferManager()

    # Requisição e Armazenamento do Manifesto
    print("Baixando manifesto...")
    manifesto = baixar_manifesto(MANIFEST_URL)
    server_manager = ServerManager(manifesto)

    # Instância das duas políticas de escolha de qualidade
    abr_baseline = RateBasedABR(manifesto)
    abr_hibrida = HybridABR(manifesto)
    
    # Variável para guardar a banda medida no loop anterior
    ultima_vazao_kbps = 0.0

    # Variáveis relativas ao jitter
    jitter_ewma_ms = 0.0  
    alfa_ewma = 0.125     

    # Histórico da Vazão
    historico_vazao = []

    # Loop Principal do Vídeo
    for segment_id in range(1, NUM_SEGMENTS + 1):
        print(f"\n--- Processando Segmento {segment_id}/{NUM_SEGMENTS} ---")

        # Cálculo da Vazão Média 
        if len(historico_vazao) > 0:
            media_vazao = sum(historico_vazao) / len(historico_vazao)
        else:
            media_vazao = 0.0
        
        # Pede a decisão de AMBAS as políticas baseada em seus respectivos estados de buffer
        qualidade_p2, url_segmento, bitrate_p2 = abr_hibrida.escolher_qualidade(media_vazao, buffer_p2.buffer_level_s)
        qualidade_p1, _, bitrate_p1 = abr_baseline.escolher_qualidade(ultima_vazao_kbps, buffer_p1.buffer_level_s)

        # Exibição das informações relativas ao ABR
        print(f"Decisão ABR -> P2 (Híbrida): {qualidade_p2} ({bitrate_p2} kbps) | P1 (Baseline): {qualidade_p1} ({bitrate_p1} kbps)")

        # O download REAL da sessão é feito usando a URL que a Política 2 (Híbrida) escolheu
        try:
            dados_rede = baixar_segmento(url_segmento, server_manager)
        except Exception as e:
            print(f"ERRO CRÍTICO FATAL: {e}")
            break

        # Exibição das informações relativas à rede
        print(f"Rede -> Vazão Medida: {dados_rede['vazao_kbps']:.2f} kbps | Tempo: {dados_rede['download_time_s']:.2f}s | Jitter: {dados_rede['jitter_network_ms']:.2f} ms | Vazão Média: {media_vazao:.2f} kbps")
        
        # Atualiza métricas de ambos os buffers de forma isolada após o download
        dados_buffer_p2 = buffer_p2.atualizar_buffer(dados_rede["download_time_s"], SEGMENT_DURATION)
        dados_buffer_p1 = buffer_p1.atualizar_buffer(dados_rede["download_time_s"], SEGMENT_DURATION)
        
        estado_buffer_p2 = "ESTÁVEL" if (dados_buffer_p2["buffer_can_play"] or segment_id == 1) else "BUFFER CHEIO OU REBUFFERING"
        estado_buffer_p1 = "ESTÁVEL" if (dados_buffer_p1["buffer_can_play"] or segment_id == 1) else "BUFFER CHEIO"

        # Mecanismo de Throttling (Aplica-se estritamente ao player controlado da Política 2)
        if dados_buffer_p2['buffer_level_s'] >= BUFFER_TARGET_S:
            wait = max(0, SEGMENT_DURATION - dados_rede["download_time_s"])
            if wait > 0:
                print(f"Player -> Buffer alvo da Política 2 atingido. Simulando playback (aguardando {wait:.2f}s)...")
                time.sleep(wait)
                
                # Apenas a política controlada drena o buffer com base no tempo de espera do player real
                buffer_p2.consumir_buffer(wait)
                dados_buffer_p2['buffer_level_s'] = buffer_p2.buffer_level_s
        else:
            print("Player -> Política 2 em fase de enchimento: Baixando próximo segmento sem pausas.")

        # Exibição das informações relativas ao Buffer de ambos os contextos
        print(f"Buffer -> P2 (Híbrida) - Nível Atual: {dados_buffer_p2['buffer_level_s']:.2f}s e Status: {estado_buffer_p2} | P1 (Baseline) - Nível Atual: {dados_buffer_p1['buffer_level_s']:.2f}s e Status: {estado_buffer_p1}")

        # Tratamento em caso de Rebufferização (Baseado na linha de execução real do player - P2)
        if dados_buffer_p2["rebuffer_event"] == 1 and segment_id != 1:
            print(f"TRAVAMENTO DETECTADO NA EXECUÇÃO: O vídeo parou por {dados_buffer_p2['stall_duration_s']:.2f}s! Vazão zerada para próxima iteração.")
            ultima_vazao_kbps = 0.0
            historico_vazao = [0.0]
        else:
            ultima_vazao_kbps = dados_rede["vazao_kbps"]
            historico_vazao.append(ultima_vazao_kbps)

            if len(historico_vazao) > 3:
                historico_vazao.pop(0)

        # Cálculos relativos ao Jitter
        jitter_atual = dados_rede["jitter_network_ms"]
        jitter_ewma_ms = (alfa_ewma * jitter_atual) + ((1 - alfa_ewma) * jitter_ewma_ms)

        # Métricas a serem registradas no .CSV da Política 2 
        metricas_p2 = {
            "segment": segment_id,
            "timestamp": timestamp_iso(),
            "server_id": dados_rede["server_id"],
            "quality": qualidade_p2,       
            "bitrate_kbps": bitrate_p2,
            "vazao_kbps": dados_rede["vazao_kbps"],
            "download_time_s": dados_rede["download_time_s"],
            "jitter_network_ms": jitter_atual,
            "jitter_ewma_ms": jitter_ewma_ms, 
            "buffer_level_s": dados_buffer_p2["buffer_level_s"],
            "buffer_can_play": dados_buffer_p2["buffer_can_play"],
            "rebuffer_event": dados_buffer_p2["rebuffer_event"],
            "stall_duration_s": dados_buffer_p2["stall_duration_s"],
            "failover_total": dados_rede["failover_total"]
        }
        logger_p2.log_segment(metricas_p2)

        # Métricas a serem registradas no .CSV da Política 1 (Alinhadas 100% ao Item 8.3)
        metricas_p1 = {
            "segment": segment_id,
            "timestamp": timestamp_iso(),
            "server_id": dados_rede["server_id"],
            "quality": qualidade_p1,    
            "bitrate_kbps": bitrate_p1,
            "vazao_kbps": dados_rede["vazao_kbps"],
            "download_time_s": dados_rede["download_time_s"],
            "jitter_network_ms": jitter_atual,
            "jitter_ewma_ms": jitter_ewma_ms, 
            "buffer_level_s": dados_buffer_p1["buffer_level_s"],
            "buffer_can_play": dados_buffer_p1["buffer_can_play"],
            "rebuffer_event": dados_buffer_p1["rebuffer_event"],
            "stall_duration_s": dados_buffer_p1["stall_duration_s"],
            "failover_total": dados_rede["failover_total"]
        }
        logger_p1.log_segment(metricas_p1)

    print("\nDownload concluído! Gerando os gráficos comparativos...")
    plotar_comparacao("docs/dados_baseline.csv", "docs/dados_politica2.csv")

if __name__ == "__main__":
    main()