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

    def escolher_qualidade(self, vazao_medida_kbps, buffer_segundos=0):
        
        if not self.representations_ordenadas:
            return ("unknown", "", 0)

        # Cold Start: se vazão é 0, usa a menor representação
        if vazao_medida_kbps == 0:
            representacao_min = self.representations_ordenadas[-1]
            return (
                representacao_min.get("quality", ""),
                representacao_min.get("url_path", ""),
                representacao_min.get("bitrate_kbps", 0)
            )

        banda_estimada_kbps = vazao_medida_kbps * SAFETY_FACTOR

        for representacao in self.representations_ordenadas:
            # CORREÇÃO: estava representacao_min.get(), o correto é representacao.get()
            bitrate_kbps = representacao.get("bitrate_kbps", 0)
            if bitrate_kbps <= banda_estimada_kbps:
                return (
                    representacao.get("quality", ""),
                    representacao.get("url_path", ""),
                    bitrate_kbps
                )

        representacao_min = self.representations_ordenadas[-1]
        return (
            representacao_min.get("quality", ""),
            representacao_min.get("url_path", ""),
            representacao_min.get("bitrate_kbps", 0)
        )


class HybridABR:
    def __init__(self, manifesto):
        self.representations = manifesto.get("representations", [])

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

        # Estado do algoritmo
        self.contador_subida = 0
        self.representacao_atual = None

    def escolher_qualidade(self, vazao_medida_kbps, buffer_segundos):

        # Caso não haja representações
        if not self.representations_ordenadas:
            return ("unknown", "", 0)

    
        # COLD START
        if self.representacao_atual is None:
            rep = self.representations_ordenadas[-1]  # menor qualidade
            self.representacao_atual = rep
            return (
                rep.get("quality", ""),
                rep.get("url_path", ""),
                rep.get("bitrate_kbps", 0)
            )

        
        # MODULADOR DE CONFIANÇA (BUFFER)
        if buffer_segundos < 4:
            multiplicador = 0.7
        elif buffer_segundos <= 10:
            multiplicador = 0.9
        else:
            multiplicador = 1.0

        # BANDA ESTIMADA
        banda_estimada = vazao_medida_kbps * multiplicador

        # QUALIDADE ALVO
        representacao_alvo = self.representations_ordenadas[-1]

        for r in self.representations_ordenadas:
            if r.get("bitrate_kbps", 0) <= banda_estimada:
                representacao_alvo = r
                break

        # HISTERES E (ANTI-OSCILAÇÃO)
        bitrate_atual = self.representacao_atual.get("bitrate_kbps", 0)
        bitrate_alvo = representacao_alvo.get("bitrate_kbps", 0)

        # Queda imediata (segurança)
        if bitrate_alvo < bitrate_atual:
            self.contador_subida = 0
            self.representacao_atual = representacao_alvo

        # Mantém
        elif bitrate_alvo == bitrate_atual:
            self.contador_subida = 0

        # Subida controlada
        else:
            self.contador_subida += 1

            if self.contador_subida >= 2:
                indice_atual = self.representations_ordenadas.index(self.representacao_atual)
                
                if indice_atual > 0:
                    self.representacao_atual = self.representations_ordenadas[indice_atual - 1]
                self.contador_subida = 0

        return (
            self.representacao_atual.get("quality", ""),
            self.representacao_atual.get("url_path", ""),
            self.representacao_atual.get("bitrate_kbps", 0)
        )