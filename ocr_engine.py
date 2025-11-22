"""
OCR Engine usando EasyOCR (não precisa de Tesseract!)
Instalar: pip install easyocr
"""
from PIL import Image, ImageEnhance, ImageOps
import re
import numpy as np


class OCREngine:
    """Motor de OCR usando EasyOCR"""
    
    def __init__(self):
        """Inicializa o EasyOCR"""
        self.reader = None
        self.initialized = False
        
    def _init_reader(self):
        """Inicializa o reader EasyOCR (lazy loading)"""
        if not self.initialized:
            print("🔄 Inicializando EasyOCR... (pode demorar na primeira vez)")
            try:
                import easyocr
                self.reader = easyocr.Reader(['en', 'pt'], gpu=False)
                self.initialized = True
                print("✅ EasyOCR inicializado!")
            except ImportError:
                print("\n❌ EasyOCR não está instalado!")
                print("   Instale com: pip install easyocr")
                raise
    
    def preprocess_image(self, image):
        """
        Pré-processa imagem para melhorar OCR
        - Inverte cores (texto branco -> preto)
        - Aumenta contraste
        """
        # Converter para RGB se necessário
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Converter para escala de cinza
        gray = ImageOps.grayscale(image)
        
        # Inverter cores (branco vira preto)
        inverted = ImageOps.invert(gray)
        
        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(2.5)
        
        # Converter de volta para RGB (EasyOCR precisa RGB)
        return contrasted.convert('RGB')
    
    def extract_text(self, image, preprocess=True):
        """
        Extrai texto da imagem usando EasyOCR
        
        Args:
            image: PIL Image
            preprocess: Se True, aplica pré-processamento
        """
        try:
            # Inicializar reader se necessário
            if not self.initialized:
                self._init_reader()
            
            # Pré-processar se solicitado
            if preprocess:
                processed = self.preprocess_image(image)
            else:
                processed = image
            
            # Converter PIL para numpy array
            img_array = np.array(processed)
            
            # Executar OCR
            results = self.reader.readtext(img_array, detail=0)
            
            # Juntar todos os textos
            text = ' '.join(results)
            
            return text.strip()
            
        except Exception as e:
            print(f"    ⚠️ Erro OCR: {e}")
            return ""
    
    def extract_cell_data(self, image, data_type='text'):
        """Extrai dados de uma célula"""
        return self.extract_text(image, preprocess=True)
    
    def parse_price(self, text):
        """
        Converte texto de preço para número
        Suporta: 7K, 1.5M, 100, etc
        
        Exemplos:
            "7K" -> 7000
            "1.5M" -> 1500000
            "10M" -> 10000000
            "500" -> 500
        """
        if not text:
            return 0
        
        text = text.upper().strip()
        
        # Verificar se tem K (mil)
        if 'K' in text:
            match = re.search(r'([\d.]+)\s*K', text)
            if match:
                try:
                    number = float(match.group(1))
                    return int(number * 1000)
                except:
                    pass
        
        # Verificar se tem M (milhão)
        if 'M' in text:
            match = re.search(r'([\d.]+)\s*M', text)
            if match:
                try:
                    number = float(match.group(1))
                    return int(number * 1000000)
                except:
                    pass
        
        # Apenas números
        numbers = ''.join(filter(lambda x: x.isdigit() or x == '.', text))
        
        try:
            return int(float(numbers)) if numbers else 0
        except:
            return 0
    
    def parse_quantity(self, text):
        """Converte texto de quantidade para número"""
        if not text:
            return 0
        
        numbers = ''.join(filter(str.isdigit, text))
        
        try:
            return int(numbers) if numbers else 0
        except:
            return 0


def test_easyocr():
    """Testa o EasyOCR"""
    print("="*70)
    print("🧪 TESTE DE EASYOCR")
    print("="*70)
    
    try:
        ocr = OCREngine()
        
        # Testar parse de preços
        print("\n💰 TESTANDO PARSE DE PREÇOS:")
        test_cases = [
            "7K", "7k", "10M", "1.5M", "500", "1500K", "2.3M",
            "100", "50K", "999", "7 K", "10 M"
        ]
        
        for test in test_cases:
            result = ocr.parse_price(test)
            print(f"  '{test}' -> {result:,}")
        
        print("\n✅ OCR Engine criado com sucesso!")
        print("   Usando: EasyOCR")
        print("   Suporta:")
        print("   - Texto branco em fundo escuro")
        print("   - Formatações K (mil) e M (milhão)")
        print("   - Pré-processamento automático")
        
    except ImportError:
        print("\n❌ EasyOCR não instalado!")
        print("   Instale com: pip install easyocr")


if __name__ == "__main__":
    test_easyocr()
