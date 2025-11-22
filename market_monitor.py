"""
MARKET MONITOR - Coleta completa com scroll + gráficos
"""
import json
import pyautogui
from PIL import Image, ImageEnhance, ImageOps
import pandas as pd
from datetime import datetime
import time
import re
import numpy as np
import os
import winsound  # Para alerta sonoro no Windows


class OCREngine:
    """OCR com correções automáticas"""

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
        if image.mode != 'RGB':
            image = image.convert('RGB')

        if scale > 1:
            new_size = (image.width * scale, image.height * scale)
            image = image.resize(new_size, Image.LANCZOS)

        gray = ImageOps.grayscale(image)
        inverted = ImageOps.invert(gray)
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(2.5)
        enhancer2 = ImageEnhance.Sharpness(contrasted)
        sharpened = enhancer2.enhance(2.0)

        return sharpened.convert('RGB')

    def corrigir_ocr(self, texto):
        """Corrige erros comuns de OCR"""
        if not texto:
            return texto

        texto = re.sub(r'(\d)O(\d)', r'\g<1>0\2', texto)
        texto = re.sub(r'(\d)O([KMkm])', r'\g<1>0\2', texto)
        texto = re.sub(r'(\d)OO([KMkm])', r'\g<1>00\2', texto)
        texto = re.sub(r'(\d)OOO([KMkm])', r'\g<1>000\2', texto)
        texto = re.sub(r'(\d)l(\d)', r'\g<1>1\2', texto)
        texto = re.sub(r'(\d)l([KMkm])', r'\g<1>1\2', texto)
        texto = re.sub(r'(\d)I(\d)', r'\g<1>1\2', texto)
        texto = re.sub(r'(\d)I([KMkm])', r'\g<1>1\2', texto)

        return texto

    def ler(self, image, scale=2):
        """Lê a imagem e retorna o texto"""
        self.init()
        processed = self.preprocess(image, scale=scale)
        img_array = np.array(processed)
        results = self.reader.readtext(img_array, detail=0)
        texto = ' '.join(results)
        texto = self.corrigir_ocr(texto)
        return texto.strip()

    def parse_preco(self, texto):
        """Converte texto de preço para número"""
        if not texto:
            return 0

        texto = texto.upper().strip()
        texto = self.corrigir_ocr(texto)

        if 'KK' in texto:
            match = re.search(r'([\d.]+)\s*KK', texto)
            if match:
                return int(float(match.group(1)) * 1000000)

        if 'M' in texto:
            match = re.search(r'([\d.]+)\s*M', texto)
            if match:
                return int(float(match.group(1)) * 1000000)

        if 'K' in texto:
            match = re.search(r'([\d.]+)\s*K', texto)
            if match:
                return int(float(match.group(1)) * 1000)

        nums = ''.join(filter(lambda x: x.isdigit() or x == '.', texto))
        return int(float(nums)) if nums else 0

    def extrair_preco_do_texto(self, texto):
        """Extrai o preço do final do texto"""
        if not texto:
            return None, texto

        padrao = r'([\d.]+\s*(?:KK|K|M|kk|k|m))\s*$'
        match = re.search(padrao, texto)
        if match:
            preco_str = match.group(1)
            resto = texto[:match.start()].strip()
            return preco_str, resto

        padrao_num = r'(\d+)\s*$'
        match = re.search(padrao_num, texto)
        if match:
            preco_str = match.group(1)
            resto = texto[:match.start()].strip()
            return preco_str, resto

        return None, texto

    def extrair_quantidade_do_texto(self, texto):
        """Extrai quantidade do texto"""
        if not texto:
            return None, texto

        padrao = r'\s+[x]?(\d+)\s*$'
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            qtd = int(match.group(1))
            resto = texto[:match.start()].strip()
            return qtd, resto

        return None, texto

    def separar_inteligente(self, texto):
        """Separa o texto de forma inteligente"""
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

        preco_str, texto = self.extrair_preco_do_texto(texto)
        if preco_str:
            dados['Preco_Formatado'] = preco_str
            dados['Preco'] = self.parse_preco(preco_str)

        qtd, texto = self.extrair_quantidade_do_texto(texto)
        if qtd:
            dados['Quantidade'] = qtd

        partes = texto.split()

        if len(partes) >= 2:
            vendedor_idx = len(partes) - 1
            for i in range(len(partes) - 1, 0, -1):
                palavra = partes[i]
                if palavra and palavra[0].isalpha() and not re.search(r'\d+[KMkm]', palavra):
                    vendedor_idx = i
                    break

            dados['Nome'] = ' '.join(partes[:vendedor_idx])
            dados['Vendedor'] = ' '.join(partes[vendedor_idx:])
        elif len(partes) == 1:
            dados['Nome'] = partes[0]

        return dados


class MarketMonitor:
    """Monitor de mercado com scroll e gráficos"""

    def __init__(self, config_path='market_elements.json'):
        with open(config_path, 'r') as f:
            cfg = json.load(f)

        self.mx = cfg['market_x']
        self.my = cfg['market_y']
        self.ox = cfg['offset_x']
        self.oy = cfg['offset_y']
        self.els = cfg['elements']

        self.ocr = OCREngine()

        # DataFrame principal (dados atuais)
        self.df = pd.DataFrame()

        # Histórico de preços (para gráficos)
        self.historico = pd.DataFrame()

        # Configurações de scroll
        self.linha_altura = 28  # pixels por linha
        self.linhas_visiveis = 8
        self.itens_por_pagina = 50
        self.scroll_clicks = -100  # quantidade de "clicks" de scroll (negativo = para baixo)
        self.scroll_method = 'down'  # 'mouse', 'pagedown', 'down', ou 'drag'
        self.drag_distance = 200  # pixels para arrastar
        self.setas_por_scroll = 8  # quantas vezes apertar seta ↓

        # Posição segura do mouse (usuário define)
        self.mouse_pos_segura = None

        print("✅ Market Monitor iniciado!")
        print(f"📍 Posição: ({self.mx}, {self.my})")
        print(f"📜 Config: {self.linhas_visiveis} linhas visíveis, {self.itens_por_pagina} por página")

    def _calcular_area_scroll(self):
        """Calcula a área central para fazer scroll"""
        linha1 = self.els.get('Linha01', {})
        linha8 = self.els.get('Linha08', {})

        x = self.mx + self.ox + linha1.get('x', 0) + linha1.get('w', 600) // 2
        y_start = self.my + self.oy + linha1.get('y', 0)
        y_end = self.my + self.oy + linha8.get('y', 0) + linha8.get('h', 28)
        y = (y_start + y_end) // 2

        return (x, y)

    def pos(self, nome):
        el = self.els[nome]
        x = self.mx + self.ox + el['x']
        y = self.my + self.oy + el['y']
        return (x, y, el['w'], el['h'])

    def click(self, nome):
        x, y, w, h = self.pos(nome)
        pyautogui.click(x + w//2, y + h//2)
        time.sleep(0.3)

    def alerta_sonoro(self, tipo='sucesso'):
        """Toca alerta sonoro"""
        try:
            if tipo == 'sucesso':
                # 3 beeps de sucesso
                for _ in range(3):
                    winsound.Beep(1000, 200)  # frequência 1000Hz, 200ms
                    time.sleep(0.1)
            elif tipo == 'erro':
                # 1 beep grave de erro
                winsound.Beep(400, 500)
            elif tipo == 'atencao':
                # 2 beeps de atenção
                winsound.Beep(800, 300)
                time.sleep(0.1)
                winsound.Beep(800, 300)
        except:
            # Se não conseguir tocar som, imprime mensagem
            print("🔔 ALERTA!")

    def salvar_posicao_mouse(self):
        """Salva a posição atual do mouse como posição segura"""
        self.mouse_pos_segura = pyautogui.position()
        print(f"📍 Posição do mouse salva: {self.mouse_pos_segura}")

    def restaurar_posicao_mouse(self):
        """Move o mouse de volta para a posição segura"""
        if self.mouse_pos_segura:
            pyautogui.moveTo(self.mouse_pos_segura[0], self.mouse_pos_segura[1])
            time.sleep(0.2)

    def scroll_down(self, linhas=8):
        """Faz scroll para baixo usando setas"""
        # Usa seta para baixo N vezes
        for _ in range(self.setas_por_scroll):
            pyautogui.press('down')
            time.sleep(0.05)
        time.sleep(0.3)  # Aguardar animação

    def scroll_to_top(self):
        """Volta ao topo da lista usando setas para cima"""
        # Aperta seta pra cima muitas vezes pra garantir que está no topo
        for _ in range(60):  # 60 vezes pra garantir
            pyautogui.press('up')
            time.sleep(0.02)
        time.sleep(0.3)

    def capturar_linhas_visiveis(self, debug=False):
        """Captura as 8 linhas atualmente visíveis"""
        data = []

        for i in range(1, 9):
            linha_nome = f'Linha{i:02d}'

            try:
                x, y, w, h = self.pos(linha_nome)
                img = pyautogui.screenshot(region=(x, y, w, h))

                if debug:
                    img.save(f'debug_{linha_nome}.png')

                texto = self.ocr.ler(img, scale=2)

                if not texto:
                    continue

                dados = self.ocr.separar_inteligente(texto)

                if dados and dados['Nome']:
                    dados['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Criar ID único para detectar duplicatas
                    dados['ID'] = f"{dados['Nome']}_{dados['Vendedor']}_{dados['Preco']}"
                    data.append(dados)

            except Exception as e:
                if debug:
                    print(f"  ⚠️ Erro {linha_nome}: {e}")

        return data

    def coletar_pagina_completa(self, debug=False):
        """Coleta todos os ~50 itens de uma página: captura 8, seta 8x, repete"""
        print("\n📄 Coletando página completa...")

        todos_itens = []
        ids_vistos = set()
        scrolls_sem_novos = 0
        max_scrolls = 8  # ~50 itens / 8 por vez = ~7 scrolls

        # PRIMEIRO: Voltar ao topo
        print("  ⬆️ Voltando ao topo...")
        self.scroll_to_top()
        time.sleep(0.3)

        # SEGUNDO: Apertar seta ↓ 8x para posicionar cursor na linha 8
        print(f"  ⬇️ Posicionando cursor (seta x{self.setas_por_scroll})...")
        self.scroll_down()
        time.sleep(0.3)

        for scroll_num in range(max_scrolls):
            print(f"\n  📸 Bloco {scroll_num + 1}/{max_scrolls}...")

            # Capturar linhas visíveis
            itens = self.capturar_linhas_visiveis(debug=debug)

            novos = 0
            duplicados = 0
            for item in itens:
                if item['ID'] not in ids_vistos:
                    ids_vistos.add(item['ID'])
                    todos_itens.append(item)
                    novos += 1
                else:
                    duplicados += 1

            print(f"     ✅ {novos} novos | ⚠️ {duplicados} duplicados | Total: {len(todos_itens)}")

            # Se não tem novos, provavelmente chegou no fim
            if novos == 0:
                scrolls_sem_novos += 1
                if scrolls_sem_novos >= 2:
                    print("  🏁 Fim da página!")
                    break
            else:
                scrolls_sem_novos = 0

            # Se já tem ~50 itens, para
            if len(todos_itens) >= self.itens_por_pagina:
                print(f"  🏁 {self.itens_por_pagina} itens coletados!")
                break

            # Seta ↓ para próximas 8 linhas (as antigas sobem, novas aparecem)
            print(f"     ⬇️ Seta x{self.setas_por_scroll}...")
            self.scroll_down()

        return todos_itens

    def coletar_todas_paginas(self, max_paginas=None, debug=False):
        """Coleta todas as páginas do mercado"""
        print("\n" + "="*70)
        print("🔄 COLETANDO TODAS AS PÁGINAS")
        print("="*70)

        # Salvar posição do mouse
        self.salvar_posicao_mouse()

        todos_itens = []
        ids_globais = set()
        pagina = 0
        paginas_repetidas = 0

        try:
            while True:
                pagina += 1
                print(f"\n{'─'*60}")
                print(f"📄 PÁGINA {pagina}")
                print(f"{'─'*60}")

                # Coletar página completa (captura 8, seta 8x, repete)
                itens_pagina = self.coletar_pagina_completa(debug=debug)

                if not itens_pagina:
                    print("⚠️ Página vazia!")
                    break

                # Verificar duplicatas globais
                novos_itens = []
                for item in itens_pagina:
                    if item['ID'] not in ids_globais:
                        ids_globais.add(item['ID'])
                        novos_itens.append(item)

                if not novos_itens:
                    paginas_repetidas += 1
                    print(f"⚠️ Todos itens já vistos! ({paginas_repetidas}/2)")
                    if paginas_repetidas >= 2:
                        print("\n✅ FIM DO MERCADO!")
                        break
                else:
                    paginas_repetidas = 0
                    todos_itens.extend(novos_itens)
                    print(f"✅ {len(novos_itens)} novos | Total geral: {len(todos_itens)}")

                if max_paginas and pagina >= max_paginas:
                    print(f"\n✅ Limite de {max_paginas} páginas atingido")
                    break

                # Clicar Próxima Página
                print("\n🖱️ Clicando Próxima Página...")
                self.click('Próxima Página')
                time.sleep(1)

                # Restaurar posição do mouse para a posição segura
                print("🖱️ Restaurando posição do mouse...")
                self.restaurar_posicao_mouse()
                time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n⚠️ Interrompido na página {pagina}")

        # Adicionar ao DataFrame
        if todos_itens:
            self.df = pd.DataFrame(todos_itens)
            print(f"\n✅ Total coletado: {len(self.df)} itens")
            # Alerta sonoro de sucesso
            self.alerta_sonoro('sucesso')

        return todos_itens

    def adicionar_ao_historico(self):
        """Adiciona dados atuais ao histórico para gráficos"""
        if self.df.empty:
            return

        # Adicionar timestamp de coleta
        df_temp = self.df.copy()
        df_temp['Coleta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.historico = pd.concat([self.historico, df_temp], ignore_index=True)
        print(f"📊 Histórico: {len(self.historico)} registros")

    def gerar_graficos(self, itens_filtro=None, salvar=True):
        """Gera gráficos de preços"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print("❌ matplotlib não instalado!")
            print("   pip install matplotlib")
            return

        if self.historico.empty:
            print("⚠️ Sem histórico para gráficos")
            print("   Execute coletas múltiplas para gerar histórico")
            return

        print("\n📊 Gerando gráficos...")

        # Se não especificou filtro, pegar top 10 mais caros
        if itens_filtro is None:
            top_itens = self.df.nlargest(10, 'Preco')['Nome'].unique()
            itens_filtro = list(top_itens)

        # Criar figura
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # Gráfico 1: Distribuição de preços atual
        ax1 = axes[0]
        df_preco = self.df[self.df['Preco'] > 0].nlargest(20, 'Preco')

        if not df_preco.empty:
            bars = ax1.barh(df_preco['Nome'], df_preco['Preco'], color='steelblue')
            ax1.set_xlabel('Preço')
            ax1.set_title('TOP 20 Itens Mais Caros (Atual)')
            ax1.invert_yaxis()

            # Adicionar valores nas barras
            for bar, preco in zip(bars, df_preco['Preco']):
                ax1.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                        f' {preco:,.0f}', va='center', fontsize=8)

        # Gráfico 2: Histórico de preços (se houver múltiplas coletas)
        ax2 = axes[1]

        coletas_unicas = self.historico['Coleta'].nunique()
        if coletas_unicas > 1:
            for item in itens_filtro[:5]:  # Top 5 para não poluir
                df_item = self.historico[self.historico['Nome'] == item]
                if not df_item.empty:
                    ax2.plot(pd.to_datetime(df_item['Coleta']),
                            df_item['Preco'],
                            marker='o',
                            label=item[:20])

            ax2.set_xlabel('Data/Hora')
            ax2.set_ylabel('Preço')
            ax2.set_title('Variação de Preço ao Longo do Tempo')
            ax2.legend(loc='upper left', fontsize=8)
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        else:
            ax2.text(0.5, 0.5, 'Histórico insuficiente\n(Execute mais coletas)',
                    ha='center', va='center', fontsize=14, color='gray')
            ax2.set_title('Variação de Preço ao Longo do Tempo')

        plt.tight_layout()

        if salvar:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'grafico_market_{timestamp}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"✅ Gráfico salvo: {filename}")

        plt.show()

    def monitorar(self, intervalo_minutos=5, max_coletas=None):
        """Modo monitor contínuo"""
        print("\n" + "="*70)
        print("👁️ MODO MONITOR ATIVADO")
        print(f"⏱️ Intervalo: {intervalo_minutos} minutos")
        print("⚠️ Ctrl+C para parar")
        print("="*70)

        coleta_num = 0

        try:
            while True:
                coleta_num += 1
                print(f"\n{'🔄'*30}")
                print(f"COLETA #{coleta_num} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'🔄'*30}")

                # Coletar tudo
                self.coletar_todas_paginas(debug=False)

                # Adicionar ao histórico
                self.adicionar_ao_historico()

                # Mostrar resumo
                self.resumo()

                if max_coletas and coleta_num >= max_coletas:
                    print(f"\n✅ {max_coletas} coletas concluídas!")
                    break

                # Aguardar
                print(f"\n⏳ Próxima coleta em {intervalo_minutos} minutos...")
                time.sleep(intervalo_minutos * 60)

        except KeyboardInterrupt:
            print(f"\n\n⚠️ Monitor parado após {coleta_num} coletas")

        # Gerar gráficos no final
        if coleta_num > 1:
            self.gerar_graficos()

    def resumo(self):
        """Mostra resumo dos dados"""
        if self.df.empty:
            print("\n⚠️ Sem dados")
            return

        print("\n" + "─"*60)
        print("📊 RESUMO")
        print("─"*60)
        print(f"📦 Total: {len(self.df)} itens")
        print(f"🏷️ Únicos: {self.df['Nome'].nunique()}")
        print(f"👥 Vendedores: {self.df['Vendedor'].nunique()}")

        df_preco = self.df[self.df['Preco'] > 0]
        if not df_preco.empty:
            print(f"\n💰 Preço médio: {df_preco['Preco'].mean():,.0f}")
            print(f"💎 Mais caro: {df_preco['Preco'].max():,}")
            print(f"💵 Mais barato: {df_preco['Preco'].min():,}")

            print(f"\n🏆 TOP 5 MAIS CAROS:")
            for i, row in df_preco.nlargest(5, 'Preco').iterrows():
                print(f"   {row['Nome'][:30]} - {row['Preco']:,} ({row['Vendedor']})")

    def salvar(self, filename=None):
        """Salva dados em CSV"""
        if self.df.empty:
            print("⚠️ Sem dados")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'market_data_{timestamp}.csv'

        self.df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Dados salvos: {filename}")

        # Salvar histórico também
        if not self.historico.empty:
            hist_filename = filename.replace('.csv', '_historico.csv')
            self.historico.to_csv(hist_filename, index=False, encoding='utf-8-sig')
            print(f"✅ Histórico salvo: {hist_filename}")

    def calibrar_scroll(self):
        """Modo de calibração - testa seta para baixo"""
        print("\n" + "="*70)
        print("🔧 CALIBRAÇÃO DE SCROLL (Seta ↓)")
        print("="*70)
        print(f"\n📜 Configuração atual: {self.setas_por_scroll} setas por scroll")

        input("\nPressione ENTER, posicione o MOUSE na lista do mercado...")

        # Countdown
        for i in range(5, 0, -1):
            print(f"⏳ {i}s - posicione o MOUSE na lista...")
            time.sleep(1)

        # Salvar posição
        self.salvar_posicao_mouse()

        print(f"\n⬇️ Apertando seta ↓ {self.setas_por_scroll} vezes...")
        self.scroll_down()

        time.sleep(0.5)
        ok = input("\nDesceu ~8 itens corretamente? (s/n): ").lower()

        if ok != 's':
            print("\n🔧 Ajustar quantidade de setas:")
            print("   1. Aumentar (desceu pouco)")
            print("   2. Diminuir (desceu demais)")
            print("   3. Definir valor manual")
            print(f"\n   Atual: {self.setas_por_scroll} setas")

            ajuste = input("\nEscolha (1/2/3): ")

            if ajuste == '1':
                self.setas_por_scroll += 2
                print(f"✅ Aumentado para {self.setas_por_scroll}")
            elif ajuste == '2':
                self.setas_por_scroll = max(1, self.setas_por_scroll - 2)
                print(f"✅ Diminuído para {self.setas_por_scroll}")
            elif ajuste == '3':
                novo = input("Quantas setas por scroll? ")
                if novo.isdigit():
                    self.setas_por_scroll = int(novo)
                    print(f"✅ Definido: {self.setas_por_scroll}")

            if input("\nTestar novamente? (s/n): ").lower() == 's':
                self.calibrar_scroll()
        else:
            print("✅ Calibração OK!")


def main():
    print("="*70)
    print("👁️ MARKET MONITOR - Coleta Completa + Gráficos")
    print("="*70)

    m = MarketMonitor()

    print("\n📋 MENU:")
    print("1. Captura rápida (8 linhas visíveis)")
    print("2. Coletar página completa (com scroll)")
    print("3. Coletar TODAS as páginas")
    print("4. Modo MONITOR (coleta contínua)")
    print("5. Gerar gráficos")
    print("6. Ver resumo")
    print("7. Salvar CSV")
    print("8. Calibrar scroll")
    print("0. Sair")

    while True:
        op = input("\n👉 ")

        if op == '1':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            data = m.capturar_linhas_visiveis(debug=True)
            if data:
                m.df = pd.DataFrame(data)
                print(f"\n✅ {len(data)} itens capturados")
                for d in data:
                    print(f"   {d['Nome']} - {d['Preco']:,}")

        elif op == '2':
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            m.coletar_pagina_completa(debug=True)
            m.resumo()

        elif op == '3':
            n = input("Máximo de páginas (vazio = todas): ")
            max_pag = int(n) if n.isdigit() else None
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            m.coletar_todas_paginas(max_paginas=max_pag, debug=False)
            m.adicionar_ao_historico()
            m.resumo()

        elif op == '4':
            intervalo = input("Intervalo em minutos (padrão=5): ")
            intervalo = int(intervalo) if intervalo.isdigit() else 5
            print("\n⏳ 3 segundos...")
            time.sleep(3)
            m.monitorar(intervalo_minutos=intervalo)

        elif op == '5':
            m.gerar_graficos()

        elif op == '6':
            m.resumo()

        elif op == '7':
            m.salvar()

        elif op == '8':
            m.calibrar_scroll()

        elif op == '0':
            if not m.df.empty:
                if input("Salvar antes? (s/n): ").lower() == 's':
                    m.salvar()
            break


if __name__ == "__main__":
    main()
