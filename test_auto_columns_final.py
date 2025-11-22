"""
Script de Teste - Captura com Detecção AUTOMÁTICA de Colunas
Agora lê a linha TODA e detecta colunas por espaços em branco!
"""
import json
import pyautogui
from PIL import Image
import pandas as pd
from datetime import datetime
import time
import os
from ocr_engine import OCREngine
from column_detector_final import ColumnDetector


class MarketCaptureAuto:
    """Sistema de captura com detecção automática de colunas"""
    
    def __init__(self, config_path='market_elements.json', debug_mode=False):
        """
        Inicializa o sistema
        
        Args:
            config_path: Caminho para o arquivo JSON de configuração
            debug_mode: Se True, salva imagens de debug
        """
        # Carregar configuração
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.market_x = self.config.get('market_x', 0)
        self.market_y = self.config.get('market_y', 0)
        self.offset_x = self.config.get('offset_x', 0)
        self.offset_y = self.config.get('offset_y', 0)
        self.elements = self.config.get('elements', {})
        
        # Modo debug
        self.debug_mode = debug_mode
        if self.debug_mode:
            self.debug_folder = 'debug_captures'
            if not os.path.exists(self.debug_folder):
                os.makedirs(self.debug_folder)
            print(f"🐛 Modo DEBUG ativado! Salvando em: {self.debug_folder}")
        
        # Inicializar módulos
        print("\n🔄 Inicializando OCR...")
        self.ocr = OCREngine()
        
        print("🔄 Inicializando Column Detector...")
        self.column_detector = ColumnDetector(min_gap_width=15)
        
        # DataFrame para armazenar dados
        self.df = pd.DataFrame(columns=['Timestamp', 'Col1', 'Col2', 'Col3', 'Col4'])
        
        # Nomes das colunas esperadas (para depois mapear)
        self.column_names = ['Nome', 'Vendedor', 'Quantidade', 'Preco']
        
        print("✅ Sistema inicializado!")
        print(f"📍 Posição do mercado: ({self.market_x}, {self.market_y})")
        print(f"📦 Elementos cadastrados: {len(self.elements)}")
    
    def get_absolute_position(self, element_name):
        """Retorna posição absoluta na tela de um elemento"""
        if element_name not in self.elements:
            print(f"❌ Elemento '{element_name}' não encontrado!")
            return None
        
        elem = self.elements[element_name]
        
        abs_x = self.market_x + self.offset_x + elem['x']
        abs_y = self.market_y + self.offset_y + elem['y']
        
        return (abs_x, abs_y, elem['w'], elem['h'])
    
    def click_element(self, element_name, center=True):
        """Clica em um elemento"""
        pos = self.get_absolute_position(element_name)
        
        if not pos:
            return False
        
        x, y, w, h = pos
        
        if center:
            click_x = x + w // 2
            click_y = y + h // 2
        else:
            click_x = x
            click_y = y
        
        print(f"🖱️ Clicando em '{element_name}' na posição ({click_x}, {click_y})")
        pyautogui.click(click_x, click_y)
        
        return True
    
    def capture_element(self, element_name):
        """Captura screenshot de um elemento específico"""
        pos = self.get_absolute_position(element_name)
        
        if not pos:
            return None
        
        x, y, w, h = pos
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        
        return screenshot
    
    def get_line_elements(self):
        """Retorna lista de elementos de linha ordenados"""
        lines = []
        for key in self.elements.keys():
            if key.startswith('Linha'):
                lines.append(key)
        
        lines.sort()
        return lines
    
    def capture_table_data_auto(self):
        """
        Captura dados com DETECÇÃO AUTOMÁTICA de colunas!
        Lê a linha toda e detecta os espaços automaticamente
        
        Returns:
            Lista de dicionários com os dados
        """
        print("\n" + "="*70)
        print("📸 CAPTURA COM DETECÇÃO AUTOMÁTICA DE COLUNAS")
        print("="*70)
        
        # Pegar lista de linhas
        line_elements = self.get_line_elements()
        
        if not line_elements:
            print("❌ Nenhuma linha cadastrada no JSON!")
            return []
        
        print(f"✅ {len(line_elements)} linhas encontradas: {', '.join(line_elements)}")
        
        # Extrair dados de cada linha
        data_rows = []
        
        print(f"\n🔎 Processando linhas...")
        
        for i, line_name in enumerate(line_elements):
            print(f"\n{'='*70}")
            print(f"📋 {line_name}")
            print(f"{'='*70}")
            
            # Capturar imagem da linha TODA
            line_img = self.capture_element(line_name)
            
            if not line_img:
                print(f"❌ Erro ao capturar {line_name}")
                continue
            
            print(f"  📐 Tamanho da linha: {line_img.size}")
            
            # Detectar e dividir colunas AUTOMATICAMENTE
            columns, gaps = self.column_detector.detect_and_split(line_img, debug=True)
            
            # Salvar debug
            if self.debug_mode:
                # Salvar linha original
                line_img.save(f"{self.debug_folder}/{line_name}_full.png")
                
                # Salvar visualização da densidade
                self.column_detector.visualize_density(
                    line_img, 
                    f"{self.debug_folder}/{line_name}_density.png"
                )
                
                # Salvar cada coluna
                for j, col_img in enumerate(columns):
                    col_img.save(f"{self.debug_folder}/{line_name}_col{j+1}_original.png")
                    
                    # Processar e salvar
                    processed = self.ocr.preprocess_image(col_img)
                    processed.save(f"{self.debug_folder}/{line_name}_col{j+1}_processed.png")
            
            # Extrair texto de cada coluna
            row_data = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            print(f"\n  🔤 Extraindo texto das colunas:")
            
            for j, col_img in enumerate(columns):
                col_num = j + 1
                
                # Extrair texto
                text = self.ocr.extract_text(col_img)
                
                print(f"     Coluna {col_num}: '{text}'")
                
                # Armazenar
                row_data[f'Col{col_num}'] = text
            
            # Tentar mapear para campos conhecidos
            if len(columns) >= 4:
                # Se tem 4 ou mais colunas, mapear para Nome, Vendedor, Quantidade, Preço
                row_data['Nome'] = row_data.get('Col1', '')
                row_data['Vendedor'] = row_data.get('Col2', '')
                row_data['Quantidade'] = self.ocr.parse_quantity(row_data.get('Col3', ''))
                
                # Preço com formatação
                preco_text = row_data.get('Col4', '')
                row_data['Preco_Formatado'] = preco_text
                row_data['Preco'] = self.ocr.parse_price(preco_text)
                
                print(f"\n  📊 Dados mapeados:")
                print(f"     Nome: {row_data['Nome']}")
                print(f"     Vendedor: {row_data['Vendedor']}")
                print(f"     Quantidade: {row_data['Quantidade']}")
                print(f"     Preço: {row_data['Preco_Formatado']} → {row_data['Preco']:,}")
            
            # Só adiciona se tiver pelo menos 2 colunas com texto
            has_content = sum(1 for k, v in row_data.items() 
                            if k.startswith('Col') and v and v.strip())
            
            if has_content >= 2:
                data_rows.append(row_data)
                print(f"\n  ✅ Linha adicionada ao dataset!")
            else:
                print(f"\n  ⚠️ Linha vazia ou insuficiente, ignorada")
        
        return data_rows
    
    def add_to_dataframe(self, data_rows):
        """Adiciona dados ao DataFrame"""
        if not data_rows:
            print("\n⚠️ Nenhum dado para adicionar")
            return
        
        new_df = pd.DataFrame(data_rows)
        self.df = pd.concat([self.df, new_df], ignore_index=True)
        
        print(f"\n✅ {len(data_rows)} linhas adicionadas ao DataFrame!")
        print(f"📊 Total de linhas no dataset: {len(self.df)}")
    
    def auto_refresh_capture(self, interval=5, max_iterations=None):
        """Modo automático: clica em atualizar e captura dados"""
        print("\n" + "="*70)
        print("🔄 MODO AUTO-REFRESH ATIVADO")
        print("="*70)
        print(f"⏱️  Intervalo: {interval} segundos")
        print(f"🔢 Iterações: {'Infinito' if max_iterations is None else max_iterations}")
        print("\n⚠️  Pressione Ctrl+C para parar\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print("\n" + "🔄"*35)
                print(f"ITERAÇÃO #{iteration}")
                print("🔄"*35)
                
                # 1. Clicar em atualizar
                print("\n🖱️  Clicando em 'Atualizar'...")
                if not self.click_element('Atualizar', center=True):
                    print("❌ Erro ao clicar em atualizar!")
                    break
                
                # Aguardar carregar
                print("⏳ Aguardando carregar (2 segundos)...")
                time.sleep(2)
                
                # 2. Capturar dados COM DETECÇÃO AUTOMÁTICA
                data = self.capture_table_data_auto()
                
                # 3. Adicionar ao DataFrame
                self.add_to_dataframe(data)
                
                # 4. Mostrar estatísticas rápidas
                self.show_quick_stats()
                
                # Verificar se atingiu limite
                if max_iterations and iteration >= max_iterations:
                    print(f"\n✅ Limite de {max_iterations} iterações atingido!")
                    break
                
                # Aguardar próximo ciclo
                print(f"\n⏳ Aguardando {interval} segundos até próxima captura...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  INTERROMPIDO PELO USUÁRIO!")
            print(f"📊 Total de iterações realizadas: {iteration}")
    
    def show_quick_stats(self):
        """Mostra estatísticas rápidas do DataFrame"""
        if self.df.empty:
            print("\n⚠️  DataFrame vazio")
            return
        
        print("\n" + "─"*70)
        print("📊 ESTATÍSTICAS RÁPIDAS")
        print("─"*70)
        
        print(f"📦 Total de linhas capturadas: {len(self.df)}")
        
        if 'Nome' in self.df.columns:
            print(f"🏷️  Itens únicos: {self.df['Nome'].nunique()}")
        
        if 'Vendedor' in self.df.columns:
            print(f"👥 Vendedores únicos: {self.df['Vendedor'].nunique()}")
        
        if 'Preco' in self.df.columns:
            preco_validos = self.df[self.df['Preco'] > 0]
            if not preco_validos.empty:
                print(f"💰 Preço médio: {preco_validos['Preco'].mean():,.0f}")
                print(f"💎 Preço máximo: {preco_validos['Preco'].max():,.0f}")
                print(f"💵 Preço mínimo: {preco_validos['Preco'].min():,.0f}")
        
        if 'Quantidade' in self.df.columns:
            print(f"📦 Quantidade total: {self.df['Quantidade'].sum()}")
        
        print("─"*70)
    
    def show_dataframe(self):
        """Exibe o DataFrame"""
        print("\n" + "="*70)
        print("📊 DATAFRAME COMPLETO")
        print("="*70)
        
        if self.df.empty:
            print("⚠️ DataFrame vazio!")
            return
        
        # Selecionar colunas principais se existirem
        if 'Nome' in self.df.columns:
            cols = ['Timestamp', 'Nome', 'Vendedor', 'Quantidade', 'Preco_Formatado']
            cols = [c for c in cols if c in self.df.columns]
            print(self.df[cols].to_string(index=False))
        else:
            print(self.df.to_string(index=False))
        
        print(f"\nTotal de linhas: {len(self.df)}")
    
    def export_csv(self, filename=None):
        """Exporta DataFrame para CSV"""
        if self.df.empty:
            print("⚠️ Sem dados para exportar!")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'market_data_{timestamp}.csv'
        
        self.df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Dados exportados para: {filename}")


def main():
    """Função principal"""
    print("="*70)
    print("🤖 CAPTURA COM DETECÇÃO AUTOMÁTICA DE COLUNAS")
    print("="*70)
    print("\n✨ NOVIDADE:")
    print("   - Lê a linha TODA")
    print("   - Detecta colunas AUTOMATICAMENTE por espaços")
    print("   - Não precisa de posições fixas!")
    
    try:
        print("\n🎛️ MODO DE EXECUÇÃO:")
        print("1. Normal")
        print("2. Debug (salva imagens + visualizações) ⭐ RECOMENDADO")
        
        modo = input("\n👉 Escolha o modo: ").strip()
        debug_mode = (modo == '2')
        
        # Inicializar sistema
        market = MarketCaptureAuto('market_elements.json', debug_mode=debug_mode)
        
        # Verificar se tem linhas cadastradas
        lines = market.get_line_elements()
        print(f"\n✅ Linhas cadastradas: {len(lines)}")
        if lines:
            print(f"   {', '.join(lines)}")
        else:
            print("❌ ERRO: Nenhuma linha cadastrada no JSON!")
            print("   Execute o element_registrar.py e cadastre as linhas!")
            return
        
        print("\n📋 MENU:")
        print("1. Captura única (teste)")
        print("2. Auto-refresh (5 segundos) ⭐ RECOMENDADO")
        print("3. Auto-refresh (10 segundos)")
        print("4. Auto-refresh (30 segundos)")
        print("5. Auto-refresh customizado")
        print("6. Mostrar DataFrame")
        print("7. Exportar CSV")
        print("0. Sair")
        
        while True:
            escolha = input("\n👉 Escolha uma opção: ").strip()
            
            if escolha == '1':
                print("\n⏳ 3 segundos para posicionar...")
                time.sleep(3)
                
                data = market.capture_table_data_auto()
                market.add_to_dataframe(data)
                market.show_quick_stats()
                
            elif escolha == '2':
                print("\n⏳ 3 segundos para posicionar...")
                time.sleep(3)
                market.auto_refresh_capture(interval=5)
                
            elif escolha == '3':
                print("\n⏳ 3 segundos para posicionar...")
                time.sleep(3)
                market.auto_refresh_capture(interval=10)
                
            elif escolha == '4':
                print("\n⏳ 3 segundos para posicionar...")
                time.sleep(3)
                market.auto_refresh_capture(interval=30)
                
            elif escolha == '5':
                try:
                    interval = int(input("Intervalo em segundos: "))
                    max_iter = input("Número máximo de iterações (Enter = infinito): ").strip()
                    max_iter = int(max_iter) if max_iter else None
                    
                    print("\n⏳ 3 segundos para posicionar...")
                    time.sleep(3)
                    market.auto_refresh_capture(interval=interval, max_iterations=max_iter)
                except ValueError:
                    print("❌ Valor inválido!")
                
            elif escolha == '6':
                market.show_dataframe()
                
            elif escolha == '7':
                market.export_csv()
                
            elif escolha == '0':
                print("\n👋 Até logo!")
                
                # Perguntar se quer salvar antes de sair
                if not market.df.empty:
                    salvar = input("Deseja salvar os dados antes de sair? (s/n): ").strip().lower()
                    if salvar == 's':
                        market.export_csv()
                        print("✅ Dados salvos!")
                
                break
            
            else:
                print("❌ Opção inválida!")
    
    except FileNotFoundError:
        print("\n❌ Arquivo 'market_elements.json' não encontrado!")
        print("Execute o element_registrar.py primeiro!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
