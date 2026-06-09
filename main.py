from config import MANIFEST_URL, NUM_SEGMENTS, SEGMENT_DURATION, MAX_BUFFER_SIZE
from network import baixar_manifesto, baixar_segmento
from buffer_manager import BufferManager
from abr import HybridABR
from metrics_logger import MetricsLogger
from utils import timestamp_iso
from network import ServerManager
import time


def main():
    print("Iniciando Cliente DASH - Entrega 1...")
    
    # Inicialização dos Módulos
    logger = MetricsLogger("docs/dados_entrega1.csv")
    buffer = BufferManager()

    print("Baixando manifesto...")
    manifesto = baixar_manifesto(MANIFEST_URL)
    server_manager = ServerManager(manifesto)
    
    abr = HybridABR(manifesto)
    
    # Variável para guardar a banda medida no loop anterior
    ultima_vazao_kbps = 0.0 

    jitter_ewma_ms = 0.0  # Nova variável para guardar o histórico
    alfa_ewma = 0.125     # Peso padrão para cálculos de rede

    # Loop Principal do Vídeo
    for segment_id in range(1, NUM_SEGMENTS + 1):
        print(f"\n--- Processando Segmento {segment_id}/{NUM_SEGMENTS} ---")

        if buffer.buffer_level_s + SEGMENT_DURATION > MAX_BUFFER_SIZE:
            tempo_espera = (buffer.buffer_level_s + SEGMENT_DURATION) - MAX_BUFFER_SIZE
            print(f"CONTROLE DE CAPACIDADE: Buffer atual ({buffer.buffer_level_s:.2f}s) próximo do limite. Aguardando {tempo_espera:.2f}s...")
            time.sleep(tempo_espera)
            buffer.consumir_buffer(tempo_espera)
        
        # O ABR olha para a banda anterior e devolve a Qualidade escolhida e a URL
        qualidade_escolhida, url_segmento, bitrate_nominal = abr.escolher_qualidade(ultima_vazao_kbps, buffer.buffer_level_s)
        print(f"Decisão ABR -> Qualidade: {qualidade_escolhida} ({bitrate_nominal} kbps) | Banda Anterior: {ultima_vazao_kbps:.2f} kbps")

        # Retorna um dicionário com vazão, tempo de download e jitter
        dados_rede = baixar_segmento(url_segmento, server_manager)
        print(f"Rede -> Vazão Medida: {dados_rede['vazao_kbps']:.2f} kbps | Tempo: {dados_rede['download_time_s']:.2f}s | Jitter: {dados_rede['jitter_network_ms']:.2f} ms")
        
        # Calcula se travou ou se rodou liso
        dados_buffer = buffer.atualizar_buffer(
            dados_rede["download_time_s"], 
            SEGMENT_DURATION
        )
        if dados_buffer["buffer_can_play"] or segment_id == 1:
            estado_buffer = "ESTÁVEL" 
        else: 
            estado_buffer ="BUFFER CHEIO"
        print(f"Buffer -> Nível Atual: {dados_buffer['buffer_level_s']:.2f}s | Status: {estado_buffer}")

        if dados_buffer["rebuffer_event"] == 1 and segment_id != 1:
            print(f"TRAVAMENTO DETECTADO: O vídeo parou por {dados_buffer['stall_duration_s']:.2f}s! Estimativa de vazão zerada para próxima iteração.")
            ultima_vazao_kbps = 0.0
        else:
            ultima_vazao_kbps = dados_rede["vazao_kbps"]

        jitter_atual = dados_rede["jitter_network_ms"]
        # Atualiza a média móvel exponencial
        jitter_ewma_ms = (alfa_ewma * jitter_atual) + ((1 - alfa_ewma) * jitter_ewma_ms)
        
        # Monta o dicionário
        metricas = {
            "segment": segment_id,
            "timestamp": timestamp_iso(),
            "server_id": dados_rede["server_id"],
            "quality": qualidade_escolhida,
            "bitrate_kbps": bitrate_nominal,
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
        
        # Log no CSV
        logger.log_segment(metricas)
        
        ultima_vazao_kbps = dados_rede["vazao_kbps"]

    print("\nDownload concluído! Gerando gráficos de desempenho...")
    # Geração dos Gráficos
    logger.plotar_grafico()

if __name__ == "__main__":
    main()
