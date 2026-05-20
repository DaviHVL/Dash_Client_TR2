import datetime

def calcular_vazao(bytes_recebidos, tempo_s):
    """
    Calcula a vazão em kbps.
    Fórmula: (bytes * 8 / 1000) / tempo
    """
    if tempo_s <= 0:
        return 0.0
    return (bytes_recebidos * 8 / 1000) / tempo_s


def timestamp_iso():
    """
    Retorna timestamp no formato ISO 8601
    """
    return datetime.datetime.now().isoformat()
