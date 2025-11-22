"""
VERSÃO MELHORADA - Parsing inteligente que não depende de espaços duplos
"""
import json
import pyautogui
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import pandas as pd
from datetime import datetime
import time
import re
import numpy as np


class OCRImproved:
    """OCR com parsing inteligente"""

    def __init__(self):
        self.reader = None

    def init(self):
        if not self.reader:
            print("🔄 Inicializando EasyOCR...")
            import easyocr
            self.reader = easyocr.Reader(['en', 'pt'], gpu=False)
            print("✅ EasyOCR pronto!")

    def preprocess(self, image, scale=2):
        """Pré-processamento melhorado"""
        # Converter para RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Aumentar resolução (ajuda muito o OCR)
        if scale > 1:
            new_size = (image.width * scale, image.height * scale)
            image = image.resize(new_size, Image.LANCZOS)

        # Converter para escala de cinza
        gray = ImageOps.grayscale(image)

        # Inverter (texto branco -> preto)
        inverted = ImageOps.invert(gray)

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(2.5)

        # Sharpness (nitidez)
        enhancer2 = ImageEnhance.Sharpness(contrasted)
        sharpened = enhancer2.enhance(2.0)

        return sharpened.convert('RGB')

    def corrigir_ocr(self, texto):
        """Corrige erros comuns de OCR"""
        if not texto:
            return texto

        # Corrigir O -> 0 em contextos numéricos (preços)
        # Padrão: número + O + K/M ou número + OO + K
        texto = re.sub(r'(\d)O(\d)', r'\g<1>0\2', texto)  # 1O0 -> 100
        texto = re.sub(r'(\d)O([KMkm])', r'\g<1>0\2', texto)  # 15OK -> 150K
        texto = re.sub(r'(\d)OO([KMkm])', r'\g<1>00\2', texto)  # 2OOK -> 200K
        texto = re.sub(r'(\d)OOO([KMkm])', r'\g<1>000\2', texto)  # 2OOOK -> 2000K

        # l -> 1 em contextos numéricos
        texto = re.sub(r'(\d)l(\d)', r'\g<1>1\2', texto)
        texto = re.sub(r'(\d)l([KMkm])', r'\g<1>1\2', texto)

        # I -> 1 em contextos numéricos
        texto = re.sub(r'(\d)I(\d)', r'\g<1>1\2', texto)
        texto = re.sub(r'(\d)I([KMkm])', r'\g<1>1\2', texto)

        # S -> 5 em contextos numéricos
        texto = re.sub(r'(\d)S(\d)', r'\g<1>5\2', texto)

        # B -> 8 em contextos numéricos
        texto = re.sub(r'(\d)B(\d)', r'\g<1>8\2', texto)

        return texto

    def ler(self, image, scale=2):
        """Lê a imagem e retorna o texto"""
        self.init()

        # Preprocessar
        processed = self.preprocess(image, scale=scale)

        # OCR
        img_array = np.array(processed)
        results = self.reader.readtext(img_array, detail=0)
        texto = ' '.join(results)

        # Corrigir erros comuns
        texto = self.corrigir_ocr(texto)

        return texto.strip()

    def parse_preco(self, texto):
        """Converte texto de preço para número"""
        if not texto:
            return 0

        texto = texto.upper().strip()
        texto = self.corrigir_ocr(texto)

        # KK = milhão (comum em jogos)
        if 'KK' in texto:
            match = re.search(r'([\d.]+)\s*KK', texto)
            if match:
                return int(float(match.group(1)) * 1000000)

        # M = milhão
        if 'M' in texto:
            match = re.search(r'([\d.]+)\s*M', texto)
            if match:
                return int(float(match.group(1)) * 1000000)

        # K = mil
        if 'K' in texto:
            match = re.search(r'([\d.]+)\s*K', texto)
            if match:
                return int(float(match.group(1)) * 1000)

        # Apenas números
        nums = ''.join(filter(lambda x: x.isdigit() or x == '.', texto))
        return int(float(nums)) if nums else 0

    def extrair_preco_do_texto(self, texto):
        """Extrai o preço do final do texto"""
        if not texto:
            return None, texto

        # Padrões de preço (no final do texto)
        # Exemplos: 1.8KK, 17K, 150K, 7KK, 194K, 200K, 1.5M
        padrao = r'([\d.]+\s*(?:KK|K|M|kk|k|m))\s*$'

        match = re.search(padrao, texto)
        if match:
            preco_str = match.group(1)
            resto = texto[:match.start()].strip()
            return preco_str, resto

        # Tentar número puro no final
        padrao_num = r'(\d+)\s*$'
        match = re.search(padrao_num, texto)
        if match:
            preco_str = match.group(1)
            resto = texto[:match.start()].strip()
            return preco_str, resto

        return None, texto

    def extrair_quantidade_do_texto(self, texto):
        """Extrai quantidade (número isolado) do texto"""
        if not texto:
            return None, texto

        # Quantidade geralmente é um número no final (após o vendedor)
        # Padrão: "nome vendedor 123" ou "nome vendedor x123"
        padrao = r'\s+[x]?(\d+)\s*$'

        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            qtd = int(match.group(1))
            resto = texto[:match.start()].strip()
            return qtd, resto

        return None, texto

    def separar_inteligente(self, texto):
        """
        Separa o texto de forma inteligente:
        1. Extrai preço do final (padrão K/M/KK)
        2. Extrai quantidade (número antes do preço)
        3. Divide o resto em Nome e Vendedor
        """
        if not texto:
            return None

        texto_original = texto
        texto = self.corrigir_ocr(texto)

        dados = {
            'Nome': '',
            'Vendedor': '',
            'Quantidade': 0,
            'Preco': 0,
            'Preco_Formatado': '',
            'Texto_Raw': texto_original
        }

        # 1. Extrair PREÇO do final
        preco_str, texto = self.extrair_preco_do_texto(texto)
        if preco_str:
            dados['Preco_Formatado'] = preco_str
            dados['Preco'] = self.parse_preco(preco_str)

        # 2. Extrair QUANTIDADE (número isolado no final)
        qtd, texto = self.extrair_quantidade_do_texto(texto)
        if qtd:
            dados['Quantidade'] = qtd

        # 3. Dividir NOME e VENDEDOR
        # Estratégia: última "palavra" ou grupo é o vendedor
        partes = texto.split()

        if len(partes) >= 2:
            # Tentar identificar padrão de nome de jogador (geralmente 1 palavra no final)
            # ou nome com caracteres especiais

            # Heurística: vendedor é a última palavra que parece nome de player
            # (começa com maiúscula, sem números)

            vendedor_idx = len(partes) - 1

            # Procurar de trás pra frente por um nome de vendedor válido
            for i in range(len(partes) - 1, 0, -1):
                palavra = partes[i]
                # Se parece nome de player (começa com letra, sem K/M no final)
                if palavra and palavra[0].isalpha() and not re.search(r'\d+[KMkm]', palavra):
                    vendedor_idx = i
                    break

            dados['Nome'] = ' '.join(partes[:vendedor_idx])
            dados['Vendedor'] = ' '.join(partes[vendedor_idx:])
        elif len(partes) == 1:
            dados['Nome'] = partes[0]

        return dados


class MarketImproved:
    """Market com OCR melhorado"""

    def __init__(self):
        with open('market_elements.json', 'r') as f:
            cfg = json.load(f)

        self.mx = cfg['market_x']
        self.my = cfg['market_y']
        self.ox = cfg['offset_x']
        self.oy = cfg['offset_y']
        self.els = cfg['elements']

        self.ocr = OCRImproved()
        self.df = pd.DataFrame()

        print("✅ Market Improved carregado!")
        print(f"📍 Posição: ({self.mx}, {self.my})")

    def pos(self, nome):
        el = self.els[nome]
        x = self.mx + self.ox + el['x']
        y = self.my + self.oy + el['y']
        return (x, y, el['w'], el['h'])

    def click(self, nome):
        x, y, w, h = self.pos(nome)
        pyautogui.click(x + w//2, y + h//2)

    def capturar(self, salvar_debug=True):
        """Captura as 8 linhas com OCR melhorado"""
        print("\n" + "="*70)
        print("📸 CAPTURANDO COM OCR MELHORADO")
        print("="*70)

        data = []

        for i in range(1, 9):
            linha_nome = f'Linha{i:02d}'
            print(f"\n{linha_nome}:")

            # Capturar linha
            x, y, w, h = self.pos(linha_nome)
            img = pyautogui.screenshot(region=(x, y, w, h))

            # Salvar debug
            if salvar_debug:
                img.save(f'debug_{linha_nome}.png')

            # OCR
            texto = self.ocr.ler(img, scale=2)
            print(f"  📝 Raw: '{texto}'")

            if not texto:
                print(f"  ⚠️ Vazio")
                continue

            # Separar inteligentemente
            dados = self.ocr.separar_inteligente(texto)

            if dados and dados['Nome']:
                dados['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data.append(dados)
                print(f"  ✅ Nome: {dados['Nome']}")
                print(f"     Vendedor: {dados['Vendedor']}")
                print(f"     Quantidade: {dados['Quantidade']}")
                print(f"     Preço: {dados['Preco']:,} ({dados['Preco_Formatado']})")
            else:
                print(f"  ⚠️ Não conseguiu extrair nome")

        return data

    def add(self, data):
        if data:
            self.df = pd.concat([self.df, pd.DataFrame(data)], ignore_index=True)
            print(f"\n✅ {len(data)} linhas | Total: {len(self.df)}")

    def varrer_paginas(self, max_paginas=None):
        """Varre múltiplas páginas"""
        print("\n🔄 VARRENDO PÁGINAS")

        pagina = 0
        itens_anteriores = set()
        paginas_repetidas = 0

        try:
            while True:
                pagina += 1
                print(f"\n{'='*60}")
                print(f"📄 PÁGINA {pagina}")
                print(f"{'='*60}")

                data = self.capturar(salvar_debug=False)

                if not data:
                    print("⚠️ Página vazia!")
                    break

                # Verificar repetição
                itens_atuais = set()
                for item in data:
                    id_item = f"{item['Nome']}_{item['Vendedor']}_{item['Preco']}"
                    itens_atuais.add(id_item)

                if itens_anteriores and itens_atuais.issubset(itens_anteriores):
                    paginas_repetidas += 1
                    print(f"\n⚠️ Repetida! ({paginas_repetidas}/2)")
                    if paginas_repetidas >= 2:
                        print("\n✅ FIM!")
                        break
                else:
                    paginas_repetidas = 0
                    itens_anteriores.update(itens_atuais)

                self.add(data)

                if max_paginas and pagina >= max_paginas:
                    print(f"\n✅ Limite de {max_paginas} páginas atingido")
                    break

                # Próxima página
                print("\n🖱️ Próxima página...")
                self.click('Próxima Página')
                time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n⚠️ Parado na página {pagina}")

        self.relatorio()

    def relatorio(self):
        """Gera relatório"""
        if self.df.empty:
            print("\n⚠️ Sem dados")
            return

        print("\n" + "="*70)
        print("📊 RELATÓRIO")
        print("="*70)

        print(f"\n📦 Total: {len(self.df)} itens")
        print(f"🏷️ Únicos: {self.df['Nome'].nunique()}")
        print(f"👥 Vendedores: {self.df['Vendedor'].nunique()}")

        df_preco = self.df[self.df['Preco'] > 0]
        if not df_preco.empty:
            print(f"\n💰 Preço médio: {df_preco['Preco'].mean():,.0f}")
            print(f"💎 Mais caro: {df_preco['Preco'].max():,}")
            print(f"💵 Mais barato: {df_preco['Preco'].min():,}")

            print(f"\n🏆 TOP 5 MAIS CAROS:")
            for i, row in df_preco.nlargest(5, 'Preco').iterrows():
                print(f"   {row['Nome']} - {row['Preco']:,} ({row['Vendedor']})")

    def salvar(self):
        if self.df.empty:
            print("⚠️ Sem dados")
            return

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        fn = f'market_{ts}.csv'
        self.df.to_csv(fn, index=False, encoding='utf-8-sig')
        print(f"✅ Salvo: {fn}")

    def mostrar(self):
        """Mostra DataFrame"""
        if self.df.empty:
            print("\n⚠️ Vazio")
            return

        print("\n" + "="*70)
        print("📋 DADOS CAPTURADOS")
        print("="*70)

        # Mostrar colunas relevantes
        cols = ['Nome', 'Vendedor', 'Quantidade', 'Preco_Formatado', 'Preco']
        cols_existentes = [c for c in cols if c in self.df.columns]
        print(self.df[cols_existentes].to_string(index=False))


def main():
    print("="*70)
    print("🎮 MARKET IMPROVED - OCR Inteligente")
    print("="*70)

    m = MarketImproved()

    print("\n📋 MENU:")
    print("1. Captura única (com debug)")
    print("2. Varrer todas as páginas")
    print("3. Varrer N páginas")
    print("4. Mostrar dados")
    print("5. Salvar CSV")
    print("6. Relatório")
    print("0. Sair")

    while True:
        op = input("\n👉 ")

        if op == '1':
            print("\n⏳ 3 segundos para posicionar...")
            time.sleep(3)
            d = m.capturar(salvar_debug=True)
            m.add(d)

        elif op == '2':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            m.varrer_paginas()

        elif op == '3':
            n = int(input("Quantas páginas? "))
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            m.varrer_paginas(max_paginas=n)

        elif op == '4':
            m.mostrar()

        elif op == '5':
            m.salvar()

        elif op == '6':
            m.relatorio()

        elif op == '0':
            if not m.df.empty and input("Salvar antes? (s/n): ").lower() == 's':
                m.salvar()
            break


if __name__ == "__main__":
    main()
