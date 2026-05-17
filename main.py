from config import MANIFEST_URL, NUM_SEGMENTS, SEGMENT_DURATION
from network import baixar_manifesto, baixar_segmento
from buffer_manager import BufferManager
from abr import RateBasedABR
from metrics_logger import MetricsLogger
from utils import timestamp_iso

def main():
    
    # Inicialização dos Módulos
    logger = MetricsLogger("dados_entrega1.csv")
    buffer = BufferManager()

    manifesto = baixar_manifesto(MANIFEST_URL)
    
    abr = RateBasedABR(manifesto)
    
    # Variável para guardar a banda medida no loop anterior
    ultima_vazao_kbps = 0.0 

    # Loop Principal do Vídeo
    for segment_id in range(1, NUM_SEGMENTS + 1):
        
        # O ABR olha para a banda anterior e devolve a Qualidade escolhida e a URL
        qualidade_escolhida, url_segmento, bitrate_nominal = abr.escolher_qualidade(ultima_vazao_kbps)

        # Retorna um dicionário com vazão, tempo de download e jitter
        dados_rede = baixar_segmento(url_segmento)
        
        # Calcula se travou ou se rodou liso
        dados_buffer = buffer.atualizar_buffer(
            dados_rede["download_time_s"], 
            SEGMENT_DURATION
        )
        
        # Monta o dicionário
        metricas = {
            "segment": segment_id,
            "timestamp": timestamp_iso(),
            "server_id": "A", 
            "quality": qualidade_escolhida,
            "bitrate_kbps": bitrate_nominal,
            "vazao_kbps": dados_rede["vazao_kbps"],
            "download_time_s": dados_rede["download_time_s"],
            "jitter_network_ms": dados_rede["jitter_network_ms"],
            "jitter_ewma_ms": 0, 
            "buffer_level_s": dados_buffer["buffer_level_s"],
            "buffer_can_play": dados_buffer["buffer_can_play"],
            "rebuffer_event": dados_buffer["rebuffer_event"],
            "stall_duration_s": dados_buffer["stall_duration_s"],
            "failover_total": 0 
        }
        
        # Log no CSV
        logger.log_segment(metricas)
        
        ultima_vazao_kbps = dados_rede["vazao_kbps"]

    # Geração dos Gráficos
    logger.plotar_grafico()

if __name__ == "__main__":
    main()