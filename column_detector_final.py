"""
Column Detector FINAL - Detecta colunas por MÍNIMOS LOCAIS (quedas na densidade)
"""
from PIL import Image, ImageOps
import numpy as np


class ColumnDetector:
    """Detecta colunas automaticamente analisando QUEDAS na densidade"""
    
    def __init__(self, min_gap_width=10, min_column_width=30):
        """
        Args:
            min_gap_width: Largura mínima de um gap (espaço vazio) em pixels
            min_column_width: Largura mínima de uma coluna em pixels
        """
        self.min_gap_width = min_gap_width
        self.min_column_width = min_column_width
    
    def analyze_density(self, image):
        """
        Analisa densidade vertical de pixels
        
        Args:
            image: PIL Image
            
        Returns:
            Array com densidade de cada coluna X (0-1)
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
        density = np.mean(inverted > 100, axis=0)
        
        return density
    
    def find_valleys(self, density, prominence=0.2):
        """
        Encontra VALES (mínimos locais) na densidade
        Esses vales são os ESPAÇOS entre as colunas
        
        Args:
            density: Array com densidade
            prominence: Quão "profundo" o vale precisa ser (0-1)
            
        Returns:
            Lista de posições X dos vales (espaços entre colunas)
        """
        from scipy.signal import find_peaks
        
        # Suavizar para remover ruído
        window_size = 5
        smoothed = np.convolve(density, np.ones(window_size)/window_size, mode='same')
        
        # Encontrar MÍNIMOS (vales) invertendo o sinal
        inverted = -smoothed
        
        # Encontrar picos no sinal invertido = vales no original
        peaks, properties = find_peaks(
            inverted, 
            prominence=prominence,  # Quão profundo o vale precisa ser
            distance=self.min_gap_width  # Distância mínima entre vales
        )
        
        return peaks.tolist()
    
    def split_by_valleys(self, image, valleys, debug=False):
        """
        Divide imagem em colunas usando os vales como separadores
        
        Args:
            image: PIL Image
            valleys: Lista de posições X dos vales
            debug: Se True, imprime informações
            
        Returns:
            Lista de tuplas (start_x, end_x) das colunas
        """
        columns = []
        
        if not valleys:
            # Sem vales, retorna imagem inteira
            return [(0, image.width)]
        
        # Adicionar margens
        margin = 5
        
        # Primeira coluna: início até primeiro vale
        start = 0
        end = valleys[0]
        if end - start >= self.min_column_width:
            columns.append((start, end))
        
        # Colunas intermediárias: entre vales
        for i in range(len(valleys) - 1):
            start = valleys[i]
            end = valleys[i + 1]
            
            if end - start >= self.min_column_width:
                columns.append((start, end))
        
        # Última coluna: último vale até o fim
        start = valleys[-1]
        end = image.width
        if end - start >= self.min_column_width:
            columns.append((start, end))
        
        if debug:
            print(f"  📍 Vales encontrados: {len(valleys)} posições")
            for i, valley in enumerate(valleys):
                print(f"     Vale {i+1}: x={valley}")
            print(f"  📦 Colunas criadas: {len(columns)}")
            for i, (start, end) in enumerate(columns):
                print(f"     Coluna {i+1}: x={start} até x={end} (largura={end-start}px)")
        
        return columns
    
    def detect_columns(self, image, debug=False):
        """
        Detecta colunas automaticamente encontrando VALES (quedas) na densidade
        
        Args:
            image: PIL Image da linha
            debug: Se True, imprime informações e salva visualização
            
        Returns:
            Lista de tuplas (start_x, end_x) das colunas
        """
        if debug:
            print(f"  📐 Analisando imagem: {image.size}")
        
        # Analisar densidade
        density = self.analyze_density(image)
        
        # Encontrar vales (espaços entre colunas)
        valleys = self.find_valleys(density, prominence=0.15)
        
        # Dividir em colunas
        columns = self.split_by_valleys(image, valleys, debug=debug)
        
        return columns
    
    def detect_and_split(self, image, debug=False):
        """
        Detecta e divide colunas automaticamente
        
        Args:
            image: PIL Image da linha
            debug: Se True, imprime informações
            
        Returns:
            Lista de PIL Images (cada coluna), lista de bounds
        """
        # Detectar colunas
        column_bounds = self.detect_columns(image, debug=debug)
        
        # Converter bounds em imagens
        columns = []
        for start, end in column_bounds:
            col_img = image.crop((start, 0, end, image.height))
            columns.append(col_img)
        
        return columns, column_bounds
    
    def visualize_density(self, image, save_path=None):
        """
        Cria visualização da densidade com os vales marcados
        
        Args:
            image: PIL Image
            save_path: Caminho para salvar imagem (opcional)
        """
        import matplotlib.pyplot as plt
        
        density = self.analyze_density(image)
        valleys = self.find_valleys(density, prominence=0.15)
        
        # Suavizar para visualização
        window_size = 5
        smoothed = np.convolve(density, np.ones(window_size)/window_size, mode='same')
        
        plt.figure(figsize=(15, 5))
        
        # Plot densidade
        plt.subplot(2, 1, 1)
        plt.plot(density, alpha=0.5, label='Original')
        plt.plot(smoothed, linewidth=2, label='Suavizada')
        plt.ylabel('Densidade')
        plt.title('Densidade Vertical de Pixels')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Marcar vales (espaços entre colunas)
        for valley in valleys:
            plt.axvline(x=valley, color='red', linewidth=2, linestyle='--', label='Vale' if valley == valleys[0] else '')
        
        if valleys:
            plt.legend()
        
        # Plot imagem
        plt.subplot(2, 1, 2)
        plt.imshow(image, cmap='gray', aspect='auto')
        plt.title('Imagem Original')
        
        # Marcar vales na imagem
        for valley in valleys:
            plt.axvline(x=valley, color='red', linewidth=3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  💾 Visualização salva: {save_path}")
        
        plt.close()


def test_column_detector():
    """Testa o detector de colunas"""
    print("="*70)
    print("🧪 COLUMN DETECTOR FINAL - Detecção por Vales")
    print("="*70)
    
    detector = ColumnDetector(min_gap_width=10, min_column_width=30)
    
    print("\n✅ Configuração:")
    print(f"   Min gap width: {detector.min_gap_width}px")
    print(f"   Min column width: {detector.min_column_width}px")
    
    print("\n🎯 Como funciona:")
    print("   1. Analisa densidade de pixels verticalmente")
    print("   2. Encontra VALES (mínimos locais = espaços)")
    print("   3. Divide a linha nesses vales")
    print("   4. Retorna cada coluna separada")


if __name__ == "__main__":
    test_column_detector()
