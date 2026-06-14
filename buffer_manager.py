from config import BUFFER_CRITICAL_S
from config import BUFFER_MAX_S

class BufferManager:
    def __init__(self):
        self.buffer_level_s = 0.0

    def atualizar_buffer(self, tempo_de_download_s, duracao_segmento_s):
        rebuffer_event = 0
        stall_duration_s = 0.0
        buffer_can_play = 1

        self.buffer_level_s -= tempo_de_download_s

        # Se o buffer ficar negativo, houve stall e o player ficou aguardando o segmento.
        if (self.buffer_level_s) < BUFFER_CRITICAL_S:
            rebuffer_event = 1
            stall_duration_s = BUFFER_CRITICAL_S - self.buffer_level_s
            self.buffer_level_s = BUFFER_CRITICAL_S
            buffer_can_play = 0
        
        # Após o download, o segmento adiciona sua duração ao buffer.
        self.buffer_level_s += duracao_segmento_s

        self.buffer_level_s = min(BUFFER_MAX_S, self.buffer_level_s)

        return {
            "buffer_level_s": self.buffer_level_s,
            "buffer_can_play": buffer_can_play,
            "rebuffer_event": rebuffer_event,
            "stall_duration_s": stall_duration_s,
        }
    
    def consumir_buffer(self, tempo_s):
        # Deduz o tempo do buffer enquanto o sistema pausa (throttling).
        self.buffer_level_s -= tempo_s
        if self.buffer_level_s < 0:
            self.buffer_level_s = 0.0