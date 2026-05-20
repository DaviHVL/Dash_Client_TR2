# network.py
import requests
import time
from utils import calcular_vazao


def baixar_manifesto(url):
    """
    Faz GET do manifesto e retorna JSON como dicionário
    """
    response = requests.get(url)
    response.raise_for_status()  # garante erro se falhar
    return response.json()


def baixar_segmento(url):
    """
    Baixa segmento em chunks e mede:
    - vazão (kbps)
    - tempo total (s)
    - jitter (ms)
    """
    
    t_inicio = time.time()
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_bytes = 0
    tempos_chunks = []
    
    ultimo_tempo = None
    
    # Baixar em pedaços
    for chunk in response.iter_content(chunk_size=4096):
        if not chunk:
            continue
        
        agora = time.time()
        
        total_bytes += len(chunk)
        
        # Marca tempo de chegada de cada chunk
        if ultimo_tempo is not None:
            delta = agora - ultimo_tempo
            tempos_chunks.append(delta)
        
        ultimo_tempo = agora
    
    t_fim = time.time()
    
    # Tempo total
    tempo_total = t_fim - t_inicio
    
    # Vazão
    vazao_kbps = calcular_vazao(total_bytes, tempo_total)
    
    # Cálculo de jitter
    jitter_ms = 0.0
    if len(tempos_chunks) > 1:
        variacoes = []
        for i in range(1, len(tempos_chunks)):
            variacao = abs(tempos_chunks[i] - tempos_chunks[i-1])
            variacoes.append(variacao)
        
        if variacoes:
            jitter_ms = (sum(variacoes) / len(variacoes)) * 1000  # para ms
    
    return {
        "vazao_kbps": vazao_kbps,
        "download_time_s": tempo_total,
        "jitter_network_ms": jitter_ms
    }
