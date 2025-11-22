"""
SIMPLES - 8 fotos das 8 linhas, OCR lê, pronto
"""
import json
import pyautogui
from PIL import Image, ImageEnhance, ImageOps
import pandas as pd
from datetime import datetime
import time
import re
import numpy as np


class OCR:
    
    def __init__(self):
        self.reader = None
        
    def init(self):
        if not self.reader:
            import easyocr
            self.reader = easyocr.Reader(['en', 'pt'], gpu=False)
    
    def ler(self, image):
        """Lê a imagem e retorna o texto"""
        self.init()
        
        # Preprocessar
        if image.mode != 'RGB':
            image = image.convert('RGB')
        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(2.5)
        rgb = contrasted.convert('RGB')
        
        # OCR
        img_array = np.array(rgb)
        results = self.reader.readtext(img_array, detail=0)
        texto = ' '.join(results)
        
        return texto.strip()
    
    def separar(self, texto):
        """Separa o texto em partes"""
        if not texto:
            return None
        
        # Dividir por espaços múltiplos
        partes = re.split(r'\s{2,}', texto)
        partes = [p.strip() for p in partes if p.strip()]
        
        dados = {
            'Nome': '',
            'Vendedor': '',
            'Quantidade': 0,
            'Preco': 0,
            'Texto': texto
        }
        
        if len(partes) >= 4:
            dados['Nome'] = partes[0]
            dados['Vendedor'] = partes[1]
            dados['Quantidade'] = int(''.join(filter(str.isdigit, partes[2])) or '0')
            dados['Preco'] = self.parse_preco(partes[3])
        elif len(partes) >= 2:
            dados['Nome'] = partes[0]
            dados['Vendedor'] = partes[1] if len(partes) > 1 else ''
        
        return dados
    
    def parse_preco(self, texto):
        if not texto or texto == '-':
            return 0
        
        texto = texto.upper()
        
        if 'K' in texto:
            match = re.search(r'([\d.]+)K', texto)
            if match:
                return int(float(match.group(1)) * 1000)
        
        if 'M' in texto:
            match = re.search(r'([\d.]+)M', texto)
            if match:
                return int(float(match.group(1)) * 1000000)
        
        nums = ''.join(filter(lambda x: x.isdigit() or x == '.', texto))
        return int(float(nums)) if nums else 0


class Market:
    
    def __init__(self):
        with open('market_elements.json', 'r') as f:
            cfg = json.load(f)
        
        self.mx = cfg['market_x']
        self.my = cfg['market_y']
        self.ox = cfg['offset_x']
        self.oy = cfg['offset_y']
        self.els = cfg['elements']
        
        self.ocr = OCR()
        self.df = pd.DataFrame()
        
        print("✅ Pronto")
    
    def pos(self, nome):
        el = self.els[nome]
        x = self.mx + self.ox + el['x']
        y = self.my + self.oy + el['y']
        return (x, y, el['w'], el['h'])
    
    def click(self, nome):
        x, y, w, h = self.pos(nome)
        pyautogui.click(x + w//2, y + h//2)
    
    def capturar(self):
        """Captura as 8 linhas - UMA FOTO POR LINHA"""
        print("\n📸 CAPTURANDO 8 LINHAS")
        
        data = []
        
        for i in range(1, 9):
            linha_nome = f'Linha{i:02d}'
            print(f"\n{linha_nome}:")
            
            # TIRAR **UMA** FOTO DA LINHA INTEIRA
            x, y, w, h = self.pos(linha_nome)
            print(f"  📍 Tirando foto em: x={x}, y={y}, tamanho={w}x{h}")
            
            img = pyautogui.screenshot(region=(x, y, w, h))
            print(f"  📸 Foto tirada: {img.size}")
            
            # Salvar pra debug
            img.save(f'debug_{linha_nome}.png')
            print(f"  💾 Salva: debug_{linha_nome}.png")
            
            # OCR LÊ A FOTO INTEIRA
            texto = self.ocr.ler(img)
            print(f"  📝 OCR leu: '{texto}'")
            
            if not texto:
                print(f"  ⚠️ Vazio")
                continue
            
            # SEPARAR o texto
            dados = self.ocr.separar(texto)
            if dados and dados['Nome']:
                dados['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data.append(dados)
                print(f"  ✅ Nome={dados['Nome']} | Vendedor={dados['Vendedor']} | Qtd={dados['Quantidade']} | Preço={dados['Preco']:,}")
            else:
                print(f"  ⚠️ Não conseguiu separar")
        
        return data
    
    def add(self, data):
        if data:
            self.df = pd.concat([self.df, pd.DataFrame(data)], ignore_index=True)
            print(f"\n✅ {len(data)} linhas | Total: {len(self.df)}")
    
    def auto(self, intervalo=5):
        print(f"\n🔄 AUTO ({intervalo}s)")
        i = 0
        
        try:
            while True:
                i += 1
                print(f"\n{'='*50}\nITERAÇÃO #{i}\n{'='*50}")
                
                self.click('Atualizar')
                time.sleep(2)
                
                data = self.capturar()
                self.add(data)
                
                time.sleep(intervalo)
                
        except KeyboardInterrupt:
            print(f"\n⚠️ PARADO - {i} iterações")
    
    def salvar(self):
        if not self.df.empty:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fn = f'market_{ts}.csv'
            self.df.to_csv(fn, index=False, encoding='utf-8-sig')
            print(f"✅ {fn}")


def main():
    m = Market()
    
    print("\n1. Captura")
    print("2. Auto 5s")
    print("3. Auto 10s")
    print("4. Salvar")
    print("0. Sair")
    
    while True:
        op = input("\n👉 ")
        
        if op == '1':
            time.sleep(3)
            d = m.capturar()
            m.add(d)
        elif op == '2':
            time.sleep(3)
            m.auto(5)
        elif op == '3':
            time.sleep(3)
            m.auto(10)
        elif op == '4':
            m.salvar()
        elif op == '0':
            if not m.df.empty and input("Salvar? (s/n): ") == 's':
                m.salvar()
            break


if __name__ == "__main__":
    main()