from config import SAFETY_FACTOR


class RateBasedABR:
    def __init__(self, manifesto):
        # Extrai as representações do manifesto no formato real
        self.representations = manifesto.get("representations", [])

        # Ordena as representações por bitrate em ordem DECRESCENTE
        self.representations_ordenadas = sorted(
            self.representations,
            key=lambda r: r.get("bitrate_kbps", 0),
            reverse=True
        )

        # Escolhe o servidor de maior prioridade para construir URLs completas
        servers = manifesto.get("servers", [])
        servers_validos = []
        for s in servers:
            if s.get("url"):
                servers_validos.append(s)
        self.server_base_url = ""
        if servers_validos:
            server_principal = min(servers_validos, key=lambda s: s.get("priority", 999))
            self.server_base_url = server_principal.get("url", "")

    def escolher_qualidade(self, vazao_medida_kbps):
        
        #Escolhe a melhor qualidade baseada na vazão medida.
        #Retorna: (qualidade, url_segmento, bitrate_nominal)
        
        if not self.representations_ordenadas:
            return ("unknown", "", 0)

        # Cold Start: se vazão é 0, usa a menor representação
        if vazao_medida_kbps == 0:
            representacao_min = self.representations_ordenadas[-1]
            return (
                representacao_min.get("quality", ""),
                self._montar_url(representacao_min.get("url_path", "")),
                representacao_min.get("bitrate_kbps", 0)
            )

        banda_estimada_kbps = vazao_medida_kbps * SAFETY_FACTOR

        for representacao in self.representations_ordenadas:
            bitrate_kbps = representacao.get("bitrate_kbps", 0)
            if bitrate_kbps <= banda_estimada_kbps:
                return (
                    representacao.get("quality", ""),
                    self._montar_url(representacao.get("url_path", "")),
                    bitrate_kbps
                )

        representacao_min = self.representations_ordenadas[-1]
        return (
            representacao_min.get("quality", ""),
            self._montar_url(representacao_min.get("url_path", "")),
            representacao_min.get("bitrate_kbps", 0)
        )

    def _montar_url(self, url_path):
        if not url_path:
            return ""
        if self.server_base_url.endswith("/") and url_path.startswith("/"):
            return self.server_base_url[:-1] + url_path
        if not self.server_base_url.endswith("/") and not url_path.startswith("/"):
            return self.server_base_url + "/" + url_path
        return self.server_base_url + url_path
