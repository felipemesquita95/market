"""
VERSÃO CORRETA - Usa as máscaras dos FILTROS para saber onde cortar!
"""
import json
import pyautogui
from PIL import Image, ImageEnhance, ImageOps
import pandas as pd
from datetime import datetime
import time
import os
import re
import numpy as np


class OCREngine:
    """OCR Engine"""
    
    def __init__(self):
        self.reader = None
        self.initialized = False
        
    def _init_reader(self):
        if not self.initialized:
            print("🔄 Inicializando EasyOCR...")
            try:
                import easyocr
                self.reader = easyocr.Reader(['en', 'pt'], gpu=False)
                self.initialized = True
                print("✅ EasyOCR pronto!")
            except ImportError:
                print("❌ pip install easyocr")
                raise
    
    def preprocess(self, image):
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(2.5)
        
        return contrasted.convert('RGB')
    
    def extract_text(self, image):
        if not self.initialized:
            self._init_reader()
        
        processed = self.preprocess(image)
        img_array = np.array(processed)
        
        results = self.reader.readtext(img_array, detail=0)
        return ' '.join(results).strip()
    
    def parse_preco(self, texto):
        if not texto or texto == '-':
            return 0
        
        texto = texto.upper().strip()
        
        if 'K' in texto:
            match = re.search(r'([\d.]+)\s*K', texto)
            if match:
                return int(float(match.group(1)) * 1000)
        
        if 'M' in texto:
            match = re.search(r'([\d.]+)\s*M', texto)
            if match:
                return int(float(match.group(1)) * 1000000)
        
        numbers = ''.join(filter(lambda x: x.isdigit() or x == '.', texto))
        try:
            return int(float(numbers)) if numbers else 0
        except:
            return 0
    
    def parse_quantidade(self, texto):
        numbers = ''.join(filter(str.isdigit, texto))
        try:
            return int(numbers) if numbers else 0
        except:
            return 0


class MarketCapture:
    """Sistema usando máscaras dos FILTROS"""
    
    def __init__(self, config_path='market_elements.json', debug=False):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.market_x = self.config.get('market_x', 0)
        self.market_y = self.config.get('market_y', 0)
        self.offset_x = self.config.get('offset_x', 0)
        self.offset_y = self.config.get('offset_y', 0)
        self.elements = self.config.get('elements', {})
        
        self.debug = debug
        if self.debug:
            self.debug_folder = 'debug_captures'
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
        
        self.ocr = OCREngine()
        self.df = pd.DataFrame(columns=['Timestamp', 'Nome', 'Vendedor', 'Quantidade', 'Preco', 'Preco_Formatado'])
        
        print("✅ Sistema inicializado!")
        print(f"📍 Mercado: ({self.market_x}, {self.market_y})")
        
        # Calcular posições das colunas BASEADO NAS MÁSCARAS DOS FILTROS
        self.calcular_colunas()
    
    def calcular_colunas(self):
        """Calcula onde dividir baseado nas máscaras dos filtros"""
        
        # Pegar referência da Linha01
        linha_ref_x = self.elements['Linha01']['x']
        
        # Posições dos filtros (relativo à linha)
        self.colunas = {
            'Nome': {
                'x_start': 0,  # Começa no início
                'x_end': self.elements['Vendedor']['x'] - linha_ref_x
            },
            'Vendedor': {
                'x_start': self.elements['Vendedor']['x'] - linha_ref_x,
                'x_end': self.elements['Quantidade']['x'] - linha_ref_x
            },
            'Quantidade': {
                'x_start': self.elements['Quantidade']['x'] - linha_ref_x,
                'x_end': self.elements['Preço Unitário']['x'] - linha_ref_x
            },
            'Preco': {
                'x_start': self.elements['Preço Unitário']['x'] - linha_ref_x,
                'x_end': self.elements['Linha01']['w']  # Até o fim da linha
            }
        }
        
        print("\n📋 Colunas calculadas (baseado nos FILTROS):")
        for nome, pos in self.colunas.items():
            print(f"   {nome}: x={pos['x_start']} até x={pos['x_end']} (largura={pos['x_end']-pos['x_start']}px)")
    
    def get_absolute_position(self, element_name):
        if element_name not in self.elements:
            return None
        
        elem = self.elements[element_name]
        abs_x = self.market_x + self.offset_x + elem['x']
        abs_y = self.market_y + self.offset_y + elem['y']
        
        return (abs_x, abs_y, elem['w'], elem['h'])
    
    def click_element(self, element_name):
        pos = self.get_absolute_position(element_name)
        if not pos:
            return False
        
        x, y, w, h = pos
        pyautogui.click(x + w // 2, y + h // 2)
        return True
    
    def get_line_elements(self):
        lines = [k for k in self.elements.keys() if k.startswith('Linha')]
        return sorted(lines)
    
    def capturar_dados(self):
        """Captura usando posições das MÁSCARAS"""
        print("\n" + "="*70)
        print("📸 CAPTURANDO (usando máscaras dos FILTROS)")
        print("="*70)
        
        lines = self.get_line_elements()
        data_rows = []
        
        for line_name in lines:
            print(f"\n--- {line_name} ---")
            
            # Capturar LINHA COMPLETA
            pos = self.get_absolute_position(line_name)
            if not pos:
                continue
            
            x, y, w, h = pos
            line_img = pyautogui.screenshot(region=(x, y, w, h))
            
            print(f"  📐 Linha: {line_img.size}")
            
            # Salvar debug
            if self.debug:
                line_img.save(f"{self.debug_folder}/{line_name}_LINHA_COMPLETA.png")
            
            # Extrair cada coluna
            row_data = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            for col_name, col_pos in self.colunas.items():
                # Cortar coluna da linha
                col_img = line_img.crop((
                    col_pos['x_start'],
                    0,
                    col_pos['x_end'],
                    line_img.height
                ))
                
                # Salvar debug
                if self.debug:
                    col_img.save(f"{self.debug_folder}/{line_name}_{col_name}.png")
                    
                    # Salvar processada
                    processed = self.ocr.preprocess(col_img)
                    processed.save(f"{self.debug_folder}/{line_name}_{col_name}_processed.png")
                
                # OCR
                texto = self.ocr.extract_text(col_img)
                
                # Processar baseado na coluna
                if col_name == 'Preco':
                    row_data['Preco_Formatado'] = texto
                    row_data['Preco'] = self.ocr.parse_preco(texto)
                    print(f"  {col_name}: '{texto}' → {row_data['Preco']:,}")
                elif col_name == 'Quantidade':
                    row_data['Quantidade'] = self.ocr.parse_quantidade(texto)
                    print(f"  {col_name}: '{texto}' → {row_data['Quantidade']}")
                else:
                    row_data[col_name] = texto
                    print(f"  {col_name}: '{texto}'")
            
            # Adicionar se tiver nome
            if row_data.get('Nome') and row_data['Nome'].strip():
                data_rows.append(row_data)
                print(f"  ✅ Adicionada!")
            else:
                print(f"  ⚠️ Vazia")
        
        return data_rows
    
    def add_to_df(self, data_rows):
        if not data_rows:
            print("\n⚠️ Nenhum dado")
            return
        
        new_df = pd.DataFrame(data_rows)
        self.df = pd.concat([self.df, new_df], ignore_index=True)
        
        print(f"\n✅ {len(data_rows)} linhas adicionadas!")
        print(f"📊 Total: {len(self.df)}")
    
    def show_stats(self):
        if self.df.empty:
            print("\n⚠️ DataFrame vazio")
            return
        
        print("\n" + "─"*70)
        print("📊 ESTATÍSTICAS")
        print("─"*70)
        print(f"📦 Total: {len(self.df)}")
        
        if 'Nome' in self.df.columns:
            print(f"🏷️ Itens únicos: {self.df['Nome'].nunique()}")
        
        if 'Vendedor' in self.df.columns:
            print(f"👥 Vendedores: {self.df['Vendedor'].nunique()}")
        
        if 'Preco' in self.df.columns:
            valid = self.df[self.df['Preco'] > 0]
            if not valid.empty:
                print(f"💰 Preço médio: {valid['Preco'].mean():,.0f}")
                print(f"💎 Preço max: {valid['Preco'].max():,.0f}")
                print(f"💵 Preço min: {valid['Preco'].min():,.0f}")
        
        print("─"*70)
    
    def auto_refresh(self, interval=5, max_iter=None):
        print(f"\n🔄 AUTO-REFRESH (cada {interval}s)")
        print("⚠️ Ctrl+C para parar\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n{'🔄'*35}")
                print(f"ITERAÇÃO #{iteration}")
                print(f"{'🔄'*35}")
                
                print("🖱️ Clicando Atualizar...")
                self.click_element('Atualizar')
                time.sleep(2)
                
                data = self.capturar_dados()
                self.add_to_df(data)
                self.show_stats()
                
                if max_iter and iteration >= max_iter:
                    break
                
                print(f"\n⏳ Aguardando {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️ PARADO! {iteration} iterações")
    
    def export_csv(self):
        if self.df.empty:
            print("⚠️ Sem dados")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'market_data_{timestamp}.csv'
        
        self.df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Salvo: {filename}")
    
    def show_df(self):
        if self.df.empty:
            print("\n⚠️ DataFrame vazio")
            return
        
        print("\n" + "="*70)
        print("📊 DATAFRAME")
        print("="*70)
        print(self.df.to_string(index=False))


def main():
    print("="*70)
    print("🎮 SISTEMA MARKET PXG")
    print("="*70)
    
    debug = input("\nModo Debug? (s/n): ").lower() == 's'
    
    market = MarketCapture('market_elements.json', debug=debug)
    
    print("\n1. Captura única")
    print("2. Auto-refresh 5s")
    print("3. Auto-refresh 10s")
    print("4. Mostrar DataFrame")
    print("5. Exportar CSV")
    print("0. Sair")
    
    while True:
        escolha = input("\n👉 Opção: ")
        
        if escolha == '1':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            data = market.capturar_dados()
            market.add_to_df(data)
            market.show_stats()
            
        elif escolha == '2':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            market.auto_refresh(5)
            
        elif escolha == '3':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            market.auto_refresh(10)
            
        elif escolha == '4':
            market.show_df()
            
        elif escolha == '5':
            market.export_csv()
            
        elif escolha == '0':
            if not market.df.empty:
                if input("Salvar? (s/n): ").lower() == 's':
                    market.export_csv()
            break


if __name__ == "__main__":
    main()
