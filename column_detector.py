"""
Column Detector - Detecta colunas automaticamente baseado em espaços em branco
"""
from PIL import Image, ImageOps
import numpy as np


class ColumnDetector:
    """Detecta colunas automaticamente analisando densidade de pixels"""
    
    def __init__(self, min_gap_width=10, threshold=240):
        """
        Args:
            min_gap_width: Largura mínima de um gap (espaço vazio) em pixels
            threshold: Threshold para considerar pixel como "branco/vazio" (0-255)
        """
        self.min_gap_width = min_gap_width
        self.threshold = threshold
    
    def analyze_density(self, image):
        """
        Analisa densidade vertical de pixels
        
        Args:
            image: PIL Image
            
        Returns:
            Lista com densidade de cada coluna X (0-1, onde 0 = vazio, 1 = cheio)
        """
        # Converter para grayscale
        if image.mode != 'L':
            gray = ImageOps.grayscale(image)
        else:
            gray = image
        
        # Converter para numpy
        img_array = np.array(gray)
        
        # Calcular densidade vertical (média de cada coluna X)
        # Pixels escuros = texto, Pixels claros = fundo
        # Invertemos para que texto = 1, fundo = 0
        inverted = 255 - img_array
        
        # Densidade de cada coluna (0 = vazio, 1 = cheio)
        density = np.mean(inverted > (255 - self.threshold), axis=0)
        
        return density
    
    def find_gaps(self, density):
        """
        Encontra gaps (regiões vazias) na densidade
        
        Args:
            density: Array com densidade de cada coluna X
            
        Returns:
            Lista de tuplas (start_x, end_x) dos gaps encontrados
        """
        import numpy as np
        
        # Calcular threshold dinâmico baseado na média
        # Regiões com densidade muito baixa comparada à média são gaps
        mean_density = np.mean(density)
        threshold = mean_density * 0.15  # 15% da densidade média
        
        gaps = []
        in_gap = False
        gap_start = 0
        
        for x, value in enumerate(density):
            # Se densidade baixa = espaço vazio
            if value < threshold:
                if not in_gap:
                    in_gap = True
                    gap_start = x
            else:
                # Saiu do gap
                if in_gap:
                    gap_width = x - gap_start
                    
                    # Só considera se for grande o suficiente
                    if gap_width >= self.min_gap_width:
                        gaps.append((gap_start, x))
                    
                    in_gap = False
        
        # Se terminou dentro de um gap
        if in_gap:
            gap_width = len(density) - gap_start
            if gap_width >= self.min_gap_width:
                gaps.append((gap_start, len(density)))
        
        return gaps
    
    def split_columns(self, image, gaps):
        """
        Divide imagem em colunas baseado nos gaps
        
        Args:
            image: PIL Image
            gaps: Lista de tuplas (start_x, end_x) dos gaps
            
        Returns:
            Lista de PIL Images (cada coluna)
        """
        columns = []
        
        if not gaps:
            # Sem gaps, retorna imagem inteira
            return [image]
        
        # Primeira coluna: do início até primeiro gap
        x_start = 0
        x_end = gaps[0][0]
        
        if x_end > x_start:
            col_img = image.crop((x_start, 0, x_end, image.height))
            columns.append(col_img)
        
        # Colunas intermediárias: entre gaps
        for i in range(len(gaps) - 1):
            x_start = gaps[i][1]
            x_end = gaps[i + 1][0]
            
            if x_end > x_start:
                col_img = image.crop((x_start, 0, x_end, image.height))
                columns.append(col_img)
        
        # Última coluna: do último gap até o fim
        x_start = gaps[-1][1]
        x_end = image.width
        
        if x_end > x_start:
            col_img = image.crop((x_start, 0, x_end, image.height))
            columns.append(col_img)
        
        return columns
    
    def detect_and_split(self, image, debug=False):
        """
        Detecta e divide colunas automaticamente
        
        Args:
            image: PIL Image da linha
            debug: Se True, imprime informações de debug
            
        Returns:
            Lista de PIL Images (cada coluna)
        """
        # Analisar densidade
        density = self.analyze_density(image)
        
        # Encontrar gaps
        gaps = self.find_gaps(density)
        
        if debug:
            print(f"  📊 Densidade analisada: {len(density)} pixels")
            print(f"  📏 Gaps encontrados: {len(gaps)}")
            for i, (start, end) in enumerate(gaps):
                print(f"     Gap {i+1}: x={start} até x={end} (largura={end-start}px)")
        
        # Dividir colunas
        columns = self.split_columns(image, gaps)
        
        if debug:
            print(f"  ✂️ Colunas detectadas: {len(columns)}")
            for i, col in enumerate(columns):
                print(f"     Coluna {i+1}: {col.size}")
        
        return columns, gaps
    
    def visualize_density(self, image, save_path=None):
        """
        Cria visualização da densidade para debug
        
        Args:
            image: PIL Image
            save_path: Caminho para salvar imagem (opcional)
        """
        import matplotlib.pyplot as plt
        
        density = self.analyze_density(image)
        gaps = self.find_gaps(density)
        
        plt.figure(figsize=(15, 4))
        
        # Plot densidade
        plt.subplot(2, 1, 1)
        plt.plot(density)
        plt.axhline(y=0.1, color='r', linestyle='--', label='Threshold (0.1)')
        plt.ylabel('Densidade')
        plt.title('Densidade Vertical de Pixels')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Marcar gaps
        for start, end in gaps:
            plt.axvspan(start, end, alpha=0.3, color='red')
        
        # Plot imagem
        plt.subplot(2, 1, 2)
        plt.imshow(image, cmap='gray', aspect='auto')
        plt.title('Imagem Original')
        
        # Marcar gaps na imagem
        for start, end in gaps:
            plt.axvline(x=start, color='red', linewidth=2)
            plt.axvline(x=end, color='red', linewidth=2)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  💾 Visualização salva: {save_path}")
        
        plt.close()
    
    def find_columns_by_gradient(self, image, debug=False):
        """
        Detecta colunas procurando QUEDAS BRUSCAS na densidade
        (transições de região com texto para região vazia)
        
        Args:
            image: PIL Image
            debug: Se True, imprime informações
            
        Returns:
            Lista de tuplas (start_x, end_x) das colunas
        """
        import numpy as np
        
        # Analisar densidade
        density = self.analyze_density(image)
        
        # Suavizar para remover ruído
        window_size = 5
        smoothed = np.convolve(density, np.ones(window_size)/window_size, mode='same')
        
        # Calcular gradiente (derivada)
        gradient = np.gradient(smoothed)
        
        # Encontrar pontos onde gradiente é muito negativo (queda brusca = fim de coluna)
        # e onde gradiente é muito positivo (subida brusca = início de coluna)
        threshold_grad = np.std(gradient) * 0.5
        
        starts = []
        ends = []
        
        for x in range(1, len(gradient) - 1):
            # Subida brusca = início de coluna
            if gradient[x] > threshold_grad and gradient[x-1] <= threshold_grad:
                starts.append(x)
            # Queda brusca = fim de coluna
            elif gradient[x] < -threshold_grad and gradient[x-1] >= -threshold_grad:
                ends.append(x)
        
        # Montar colunas
        columns = []
        
        # Se não encontrou transições claras, usar densidade direta
        if len(starts) == 0 and len(ends) == 0:
            # Método fallback: procurar grupos de alta densidade
            in_text = False
            col_start = 0
            
            for x in range(len(smoothed)):
                if smoothed[x] > 0.1 and not in_text:
                    # Início de texto
                    in_text = True
                    col_start = max(0, x - 10)
                elif smoothed[x] < 0.05 and in_text:
                    # Fim de texto (espaço grande)
                    in_text = False
                    col_end = min(len(smoothed), x + 10)
                    
                    if col_end - col_start >= 30:
                        columns.append((col_start, col_end))
            
            # Se ainda está em texto no final
            if in_text:
                col_end = len(smoothed)
                if col_end - col_start >= 30:
                    columns.append((col_start, col_end))
        else:
            # Usar transições detectadas
            # Combinar starts e ends
            if len(starts) > 0 and len(ends) > 0:
                # Primeira coluna pode começar no início
                if starts[0] > 20:
                    columns.append((0, starts[0]))
                
                # Colunas entre starts e ends
                for i in range(len(starts)):
                    start = starts[i]
                    # Procurar próximo end
                    next_ends = [e for e in ends if e > start]
                    if next_ends:
                        end = next_ends[0]
                        if end - start >= 30:
                            columns.append((start, end))
                
                # Última coluna pode ir até o fim
                if ends[-1] < len(smoothed) - 20:
                    columns.append((ends[-1], len(smoothed)))
        
        if debug:
            print(f"  📊 Gradiente: std={np.std(gradient):.3f}, threshold={threshold_grad:.3f}")
            print(f"  📍 Transições encontradas: {len(starts)} starts, {len(ends)} ends")
            print(f"  📦 Colunas detectadas: {len(columns)}")
            for i, (start, end) in enumerate(columns):
                print(f"     Coluna {i+1}: x={start} até x={end} (largura={end-start}px)")
        
        return columns
    
    def detect_and_split_v4(self, image, debug=False):
        """
        Versão 4: Detecção por gradiente (quedas bruscas)
        
        Args:
            image: PIL Image da linha
            debug: Se True, imprime informações
            
        Returns:
            Lista de PIL Images (cada coluna), lista de limites
        """
        # Detectar colunas
        column_bounds = self.find_columns_by_gradient(image, debug=debug)
        
        # Se não encontrou nenhuma coluna, retornar imagem inteira
        if not column_bounds:
            column_bounds = [(0, image.width)]
        
        # Converter bounds em imagens
        columns = []
        for start, end in column_bounds:
            if end > start:
                col_img = image.crop((start, 0, end, image.height))
                columns.append(col_img)
        
        return columns, column_bounds


def test_column_detector():
    """Testa o detector de colunas"""
    print("="*70)
    print("🧪 TESTE DO COLUMN DETECTOR")
    print("="*70)
    
    detector = ColumnDetector(min_gap_width=10)
    
    print("\n✅ Column Detector criado!")
    print(f"   Min gap width: {detector.min_gap_width}px")
    print(f"   Threshold: {detector.threshold}")
    
    print("\n📝 Como usar:")
    print("   1. Captura a linha toda")
    print("   2. detector.detect_and_split(line_img)")
    print("   3. Recebe lista de colunas automaticamente!")


if __name__ == "__main__":
    test_column_detector()
