"""
Módulo para detectar linhas horizontais da tabela do mercado
"""
import cv2
import numpy as np
from PIL import Image


class LineDetector:
    def __init__(self, min_line_height=20, max_line_height=50):
        """
        Inicializa o detector de linhas
        
        Args:
            min_line_height: Altura mínima de uma linha válida (pixels)
            max_line_height: Altura máxima de uma linha válida (pixels)
        """
        self.min_line_height = min_line_height
        self.max_line_height = max_line_height
    
    def detect_horizontal_lines(self, image):
        """
        Detecta linhas horizontais em uma imagem
        
        Args:
            image: PIL Image ou numpy array
            
        Returns:
            Lista de posições Y das linhas detectadas
        """
        # Converter para numpy array se necessário
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
        
        # Converter para escala de cinza
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Aplicar threshold para binarizar
        _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        
        # Detectar bordas
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        
        # Detectar linhas usando Hough Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=100, maxLineGap=10)
        
        horizontal_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Verificar se é linha horizontal (diferença Y pequena)
                if abs(y2 - y1) < 5:
                    y_pos = (y1 + y2) // 2
                    horizontal_lines.append(y_pos)
        
        # Remover duplicatas (linhas muito próximas)
        horizontal_lines = self._merge_close_lines(horizontal_lines, threshold=5)
        
        return sorted(horizontal_lines)
    
    def _merge_close_lines(self, lines, threshold=5):
        """Mescla linhas que estão muito próximas"""
        if not lines:
            return []
        
        lines = sorted(lines)
        merged = [lines[0]]
        
        for line in lines[1:]:
            if line - merged[-1] > threshold:
                merged.append(line)
        
        return merged
    
    def find_row_positions(self, image):
        """
        Encontra as posições Y de cada linha da tabela
        
        Args:
            image: PIL Image da área da tabela
            
        Returns:
            Lista de tuplas (y_inicio, y_fim) para cada linha
        """
        lines = self.detect_horizontal_lines(image)
        
        if len(lines) < 2:
            # Se não detectou linhas, divide igualmente
            height = image.height if isinstance(image, Image.Image) else image.shape[0]
            num_rows = max(1, height // 35)  # Estimativa: ~35px por linha
            row_height = height // num_rows
            
            rows = []
            for i in range(num_rows):
                y_start = i * row_height
                y_end = (i + 1) * row_height
                rows.append((y_start, y_end))
            
            return rows
        
        # Criar pares de linhas (início e fim de cada row)
        rows = []
        for i in range(len(lines) - 1):
            y_start = lines[i]
            y_end = lines[i + 1]
            height = y_end - y_start
            
            # Filtrar linhas com altura válida
            if self.min_line_height <= height <= self.max_line_height:
                rows.append((y_start, y_end))
        
        return rows
    
    def visualize_lines(self, image, save_path='detected_lines.png'):
        """
        Visualiza as linhas detectadas (para debug)
        
        Args:
            image: PIL Image
            save_path: Caminho para salvar a imagem
        """
        img_array = np.array(image)
        lines = self.detect_horizontal_lines(image)
        
        # Desenhar linhas detectadas
        for y in lines:
            cv2.line(img_array, (0, y), (img_array.shape[1], y), (0, 255, 0), 2)
        
        # Salvar
        result = Image.fromarray(img_array)
        result.save(save_path)
        print(f"✅ Visualização salva em: {save_path}")
        
        return result
