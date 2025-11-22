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
import random


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
    
    def varrer_tudo(self):
        """Varre TODAS as páginas até o fim"""
        import random
        
        print("\n🔄 VARRENDO TODAS AS PÁGINAS")
        print("⚠️ Detecção automática de fim\n")
        
        pagina = 0
        linhas_anteriores = set()
        paginas_repetidas = 0
        
        try:
            while True:
                pagina += 1
                print(f"\n{'='*60}")
                print(f"📄 PÁGINA {pagina}")
                print(f"{'='*60}")
                
                # Capturar
                data = self.capturar()
                
                if not data:
                    print("⚠️ Página vazia!")
                    break
                
                # Verificar se repetiu (chegou no fim)
                linhas_atuais = set()
                for item in data:
                    # Criar ID único: nome + vendedor + preço
                    id_item = f"{item['Nome']}_{item['Vendedor']}_{item['Preco']}"
                    linhas_atuais.add(id_item)
                
                # Se todas as linhas são repetidas = fim!
                if linhas_anteriores and linhas_atuais.issubset(linhas_anteriores):
                    paginas_repetidas += 1
                    print(f"\n⚠️ Página repetida! ({paginas_repetidas}/2)")
                    
                    if paginas_repetidas >= 2:
                        print("\n✅ FIM DAS PÁGINAS DETECTADO!")
                        break
                else:
                    paginas_repetidas = 0
                    linhas_anteriores = linhas_atuais
                
                # Adicionar ao DataFrame
                self.add(data)
                
                # Clicar Próxima Página
                print("\n🖱️ Clicando em Próxima Página...")
                self.click('Próxima Página')
                
                # Delay aleatório
                delay = random.uniform(2, 5)
                print(f"⏳ Aguardando {delay:.1f}s...")
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️ PARADO - {pagina} páginas")
        
        # RELATÓRIO FINAL
        self.gerar_relatorio()
    
    def gerar_relatorio(self):
        """Gera relatório completo dos dados"""
        if self.df.empty:
            print("\n⚠️ Sem dados para relatório")
            return
        
        print("\n" + "="*70)
        print("📊 RELATÓRIO FINAL - MERCADO PXG")
        print("="*70)
        
        # Estatísticas gerais
        print(f"\n📦 GERAL:")
        print(f"   Total de itens: {len(self.df)}")
        print(f"   Itens únicos: {self.df['Nome'].nunique()}")
        print(f"   Vendedores únicos: {self.df['Vendedor'].nunique()}")
        
        # TOP 10 MAIS CAROS
        print(f"\n💎 TOP 10 MAIS CAROS:")
        top_caros = self.df.nlargest(10, 'Preco')
        for i, row in enumerate(top_caros.itertuples(), 1):
            print(f"   {i}. {row.Nome} - {row.Preco:,} (Vendedor: {row.Vendedor})")
        
        # TOP 10 MAIS BARATOS (excluindo preço 0)
        print(f"\n💵 TOP 10 MAIS BARATOS:")
        df_com_preco = self.df[self.df['Preco'] > 0]
        if not df_com_preco.empty:
            top_baratos = df_com_preco.nsmallest(10, 'Preco')
            for i, row in enumerate(top_baratos.itertuples(), 1):
                print(f"   {i}. {row.Nome} - {row.Preco:,} (Vendedor: {row.Vendedor})")
        
        # PREÇOS
        if not df_com_preco.empty:
            print(f"\n💰 ANÁLISE DE PREÇOS:")
            print(f"   Preço médio: {df_com_preco['Preco'].mean():,.0f}")
            print(f"   Preço mediano: {df_com_preco['Preco'].median():,.0f}")
            print(f"   Preço máximo: {df_com_preco['Preco'].max():,}")
            print(f"   Preço mínimo: {df_com_preco['Preco'].min():,}")
        
        # TOP VENDEDORES (mais itens)
        print(f"\n👥 TOP 5 VENDEDORES (mais itens):")
        top_vendedores = self.df['Vendedor'].value_counts().head(5)
        for i, (vendedor, qtd) in enumerate(top_vendedores.items(), 1):
            print(f"   {i}. {vendedor} - {qtd} itens")
        
        # ITENS MAIS COMUNS
        print(f"\n📊 TOP 5 ITENS MAIS VENDIDOS:")
        top_itens = self.df['Nome'].value_counts().head(5)
        for i, (item, qtd) in enumerate(top_itens.items(), 1):
            print(f"   {i}. {item} - {qtd}x")
        
        print("\n" + "="*70)
    
    def salvar(self):
        if not self.df.empty:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fn = f'market_{ts}.csv'
            self.df.to_csv(fn, index=False, encoding='utf-8-sig')
            print(f"✅ {fn}")


def main():
    m = Market()
    
    print("\n1. Captura única")
    print("2. Varrer TODAS as páginas (automático)")
    print("3. Salvar CSV")
    print("4. Ver relatório")
    print("0. Sair")
    
    while True:
        op = input("\n👉 ")
        
        if op == '1':
            time.sleep(3)
            d = m.capturar()
            m.add(d)
        elif op == '2':
            print("\n⏳ 3 segundos para posicionar...")
            time.sleep(3)
            m.varrer_tudo()
        elif op == '3':
            m.salvar()
        elif op == '4':
            m.gerar_relatorio()
        elif op == '0':
            if not m.df.empty and input("Salvar? (s/n): ") == 's':
                m.salvar()
            break


if __name__ == "__main__":
    main()
