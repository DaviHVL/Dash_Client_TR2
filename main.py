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
    
    buffer = BufferManager()

    print("Baixando manifesto...")
    manifesto = baixar_manifesto(MANIFEST_URL)
    server_manager = ServerManager(manifesto)

    # Instancia as duas políticas simultaneamente
    abr_baseline = RateBasedABR(manifesto)
    abr_hibrida = HybridABR(manifesto)
    
    # Variável para guardar a banda medida no loop anterior
    ultima_vazao_kbps = 0.0 
    jitter_ewma_ms = 0.0  
    alfa_ewma = 0.125     

    # Loop Principal do Vídeo
    for segment_id in range(1, NUM_SEGMENTS + 1):
        print(f"\n--- Processando Segmento {segment_id}/{NUM_SEGMENTS} ---")
        
        # Pede a decisão de AMBAS as políticas baseada na mesma medição de banda
        qualidade_p2, url_segmento, bitrate_p2 = abr_hibrida.escolher_qualidade(ultima_vazao_kbps, buffer.buffer_level_s)
        qualidade_p1, _, bitrate_p1 = abr_baseline.escolher_qualidade(ultima_vazao_kbps, buffer.buffer_level_s)

        print(f"Decisão ABR -> Qualidade: {qualidade_p2} ({bitrate_p2} kbps) | Banda Anterior: {ultima_vazao_kbps:.2f} kbps")

        # O download REAL é feito usando a URL que a Política 2 (Híbrida) escolheu
        try:
            dados_rede = baixar_segmento(url_segmento, server_manager)
        except Exception as e:
            print(f"ERRO CRÍTICO FATAL: {e}")
            break

        print(f"Rede -> Vazão Medida: {dados_rede['vazao_kbps']:.2f} kbps | Tempo: {dados_rede['download_time_s']:.2f}s | Jitter: {dados_rede['jitter_network_ms']:.2f} ms")
        
        # Atualiza métricas de Buffer e Jitter
        dados_buffer = buffer.atualizar_buffer(dados_rede["download_time_s"], SEGMENT_DURATION)
        estado_buffer = "ESTÁVEL" if (dados_buffer["buffer_can_play"] or segment_id == 1) else "BUFFER CHEIO"

        if dados_buffer['buffer_level_s'] >= BUFFER_TARGET_S:
            wait = max(0, SEGMENT_DURATION - dados_rede["download_time_s"])
            if wait > 0:
                print(f"Player -> Buffer alvo atingido. Simulando playback (aguardando {wait:.2f}s)...")
                time.sleep(wait)
                buffer.consumir_buffer(wait)

                dados_buffer['buffer_level_s'] = buffer.buffer_level_s
        else:
            print("Player -> Fase de enchimento: Baixando próximo segmento sem pausas.")

        print(f"Buffer -> Nível Atual: {dados_buffer['buffer_level_s']:.2f}s | Status: {estado_buffer}")

        if dados_buffer["rebuffer_event"] == 1 and segment_id != 1:
            print(f"TRAVAMENTO DETECTADO: O vídeo parou por {dados_buffer['stall_duration_s']:.2f}s! Vazão zerada para próxima iteração.")
            ultima_vazao_kbps = 0.0
        else:
            ultima_vazao_kbps = dados_rede["vazao_kbps"]

        jitter_atual = dados_rede["jitter_network_ms"]
        jitter_ewma_ms = (alfa_ewma * jitter_atual) + ((1 - alfa_ewma) * jitter_ewma_ms)
        
        metricas_base = {
            "segment": segment_id,
            "timestamp": timestamp_iso(),
            "server_id": dados_rede["server_id"],
            "vazao_kbps": dados_rede["vazao_kbps"],
            "download_time_s": dados_rede["download_time_s"],
            "jitter_network_ms": jitter_atual,
            "jitter_ewma_ms": jitter_ewma_ms, 
            "buffer_level_s": dados_buffer["buffer_level_s"],
            "buffer_can_play": dados_buffer["buffer_can_play"],
            "rebuffer_event": dados_buffer["rebuffer_event"],
            "stall_duration_s": dados_buffer["stall_duration_s"],
            "failover_total": dados_rede["failover_total"]
        }
        
        # Loga as decisões da Política 2 no seu respectivo CSV
        metricas_p2 = metricas_base.copy()
        metricas_p2["quality"] = qualidade_p2
        metricas_p2["bitrate_kbps"] = bitrate_p2
        logger_p2.log_segment(metricas_p2)

        # Loga as decisões da Política 1 
        metricas_p1 = metricas_base.copy()
        metricas_p1["quality"] = qualidade_p1
        metricas_p1["bitrate_kbps"] = bitrate_p1
        logger_p1.log_segment(metricas_p1)

    print("\nDownload concluído! Gerando o gráfico comparativo...")

    plotar_comparacao("docs/dados_baseline.csv", "docs/dados_politica2.csv")

if __name__ == "__main__":
    main()