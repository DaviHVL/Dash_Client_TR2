from config import SAFETY_FACTOR

class HybridABR:
    def __init__(self, manifesto):
        self.representations = manifesto.get("representations", [])

        self.representations_ordenadas = sorted(
            self.representations,
            key=lambda r: r.get("bitrate_kbps", 0),
            reverse=True
        )

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
            multiplicador = 0.5
        elif buffer_segundos <= 10:
            multiplicador = 0.8
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

            if self.contador_subida >= 3:
                self.representacao_atual = representacao_alvo
                self.contador_subida = 0

        return (
            self.representacao_atual.get("quality", ""),
            self.representacao_atual.get("url_path", ""),
            self.representacao_atual.get("bitrate_kbps", 0)
        )