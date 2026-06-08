# network.py
import requests
import time
from utils import calcular_vazao

class ServerManager:
    def __init__(self, manifesto):
        # Ordena servidores por prioridade (menor = melhor)
        self.servers = sorted(
            manifesto.get("servers", []),
            key=lambda s: s.get("priority", 999)
        )
        
        self.current_server_index = 0
        self.failover_count = 0

    def get_current_server(self):
        return self.servers[self.current_server_index]

    def montar_url(self, url_path):
        base = self.get_current_server().get("url", "")
        
        if base.endswith("/") and url_path.startswith("/"):
            return base[:-1] + url_path
        if not base.endswith("/") and not url_path.startswith("/"):
            return base + "/" + url_path
        return base + url_path

    def health_check(self, timeout=1):
        server = self.get_current_server()
        url = server.get("url", "") + "/health"
        
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False

    def failover(self):
        if self.current_server_index < len(self.servers) - 1:
            self.current_server_index += 1
            self.failover_count += 1
            print(f"FAILOVER: Mudando para servidor {self.get_current_server().get('id', 'unknown')}")
            return True
        return False


def baixar_manifesto(url):
    """
    Faz GET do manifesto e retorna JSON como dicionário
    """
    response = requests.get(url)
    response.raise_for_status()  # garante erro se falhar
    return response.json()


def baixar_segmento(url_path, server_manager):
    
    tentativa = 0
    max_tentativas = len(server_manager.servers)

    while tentativa < max_tentativas:

        # Verifica saúde antes de baixar
        if not server_manager.health_check():
            if not server_manager.failover():
                raise Exception("Todos os servidores indisponíveis")
            tentativa += 1
            continue

        url = server_manager.montar_url(url_path)

        try:
            t_inicio = time.perf_counter()
            
            response = requests.get(url, stream=True, timeout=3)
            response.raise_for_status()
            
            total_bytes = 0
            tempos_chunks = []
            ultimo_tempo = None

            for chunk in response.iter_content(chunk_size=4096):
                if not chunk:
                    continue

                agora = time.perf_counter()
                total_bytes += len(chunk)

                if ultimo_tempo is not None:
                    tempos_chunks.append(agora - ultimo_tempo)

                ultimo_tempo = agora

            t_fim = time.perf_counter()

            tempo_total = t_fim - t_inicio
            vazao_kbps = calcular_vazao(total_bytes, tempo_total)

            # jitter
            jitter_ms = 0.0
            if len(tempos_chunks) > 1:
                variacoes = [
                    abs(tempos_chunks[i] - tempos_chunks[i-1])
                    for i in range(1, len(tempos_chunks))
                ]
                if variacoes:
                    jitter_ms = (sum(variacoes) / len(variacoes)) * 1000

            return {
                "vazao_kbps": vazao_kbps,
                "download_time_s": tempo_total,
                "jitter_network_ms": jitter_ms,
                "server_id": server_manager.get_current_server().get("id", "unknown"),
                "failover_total": server_manager.failover_count
            }

        except Exception as e:
            print(f"Erro ao baixar: {e}")
            if not server_manager.failover():
                raise Exception("Todos os servidores falharam durante download")
            tentativa += 1

    raise Exception("Falha geral no download")
