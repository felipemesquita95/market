import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyautogui
import json
import os


class ElementRegistrar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📐 PXG Market - Cadastro de Elementos")
        self.root.attributes('-topmost', True)
        
        # Configurações
        self.market_x = 0
        self.market_y = 0
        self.offset_x = 0
        self.offset_y = 0
        
        # Elementos cadastrados
        self.elements = {}
        
        # Elemento atual sendo editado
        self.current_element = None
        
        # Overlay
        self.overlay_window = None
        
        # Cores para elementos
        self.colors = ['red', 'lime', 'cyan', 'yellow', 'magenta', 'orange', 
                      'pink', 'lightblue', 'lightgreen', 'gold']
        self.color_index = 0
        
        # Carregar configuração se existir
        self.load_config()
        
        self.setup_ui()
        
    def load_config(self):
        """Carrega configuração salva"""
        try:
            if os.path.exists('market_elements.json'):
                with open('market_elements.json', 'r') as f:
                    config = json.load(f)
                    self.market_x = config.get('market_x', 0)
                    self.market_y = config.get('market_y', 0)
                    self.offset_x = config.get('offset_x', 0)
                    self.offset_y = config.get('offset_y', 0)
                    self.elements = config.get('elements', {})
                print("✅ Configuração carregada!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar: {e}")
    
    def save_config(self):
        """Salva configuração"""
        config = {
            'market_x': self.market_x,
            'market_y': self.market_y,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'elements': self.elements
        }
        
        with open('market_elements.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        print("✅ Configuração salva!")
        messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
    
    def setup_ui(self):
        """Configura interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        ttk.Label(main_frame, text="📐 CADASTRO DE ELEMENTOS DO MERCADO", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        # ===== SEÇÃO 1: POSIÇÃO DO MERCADO =====
        pos_frame = ttk.LabelFrame(main_frame, text="1️⃣ Posição do Mercado", padding="10")
        pos_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(pos_frame, text="Posição X:").grid(row=0, column=0, sticky=tk.W)
        self.x_entry = ttk.Entry(pos_frame, width=10)
        self.x_entry.insert(0, str(self.market_x))
        self.x_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(pos_frame, text="Posição Y:").grid(row=0, column=2, padx=(20,0))
        self.y_entry = ttk.Entry(pos_frame, width=10)
        self.y_entry.insert(0, str(self.market_y))
        self.y_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(pos_frame, text="📍 Capturar (3s)", 
                  command=self.capture_position).grid(row=0, column=4, padx=10)
        
        # Offset
        ttk.Label(pos_frame, text="Offset X:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        self.offset_x_entry = ttk.Entry(pos_frame, width=10)
        self.offset_x_entry.insert(0, str(self.offset_x))
        self.offset_x_entry.grid(row=1, column=1, padx=5, pady=(10,0))
        
        ttk.Label(pos_frame, text="Offset Y:").grid(row=1, column=2, padx=(20,0), pady=(10,0))
        self.offset_y_entry = ttk.Entry(pos_frame, width=10)
        self.offset_y_entry.insert(0, str(self.offset_y))
        self.offset_y_entry.grid(row=1, column=3, padx=5, pady=(10,0))
        
        # ===== SEÇÃO 2: CADASTRO DE ELEMENTO =====
        element_frame = ttk.LabelFrame(main_frame, text="2️⃣ Cadastrar Novo Elemento", padding="10")
        element_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Nome do elemento
        ttk.Label(element_frame, text="Nome do Elemento:").grid(row=0, column=0, sticky=tk.W)
        self.element_name = ttk.Entry(element_frame, width=30)
        self.element_name.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Tipo (informativo)
        ttk.Label(element_frame, text="Tipo/Descrição:").grid(row=1, column=0, sticky=tk.W)
        self.element_desc = ttk.Entry(element_frame, width=30)
        self.element_desc.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Separator(element_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, 
                                                               sticky=(tk.W, tk.E), pady=10)
        
        # Sliders
        self.create_slider(element_frame, 3, "Posição X:", 'x', 0, 2500, 0)
        self.create_slider(element_frame, 4, "Posição Y:", 'y', 0, 2500, 0)
        self.create_slider(element_frame, 5, "Largura (W):", 'w', 10, 2500, 100)
        self.create_slider(element_frame, 6, "Altura (H):", 'h', 10, 2500, 30)
        
        ttk.Separator(element_frame, orient='horizontal').grid(row=7, column=0, columnspan=3, 
                                                               sticky=(tk.W, tk.E), pady=10)
        
        # Botões
        btn_frame = ttk.Frame(element_frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="➕ Adicionar Elemento", 
                  command=self.add_element).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="✏️ Atualizar Elemento", 
                  command=self.update_element).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Limpar Campos", 
                  command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        # ===== SEÇÃO 3: ELEMENTOS CADASTRADOS =====
        list_frame = ttk.LabelFrame(main_frame, text="3️⃣ Elementos Cadastrados", padding="10")
        list_frame.grid(row=2, column=1, pady=10, padx=(10,0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Lista de elementos
        self.element_listbox = tk.Listbox(list_frame, height=15, width=40)
        self.element_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.element_listbox.bind('<<ListboxSelect>>', self.on_element_select)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.element_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.element_listbox.config(yscrollcommand=scrollbar.set)
        
        # Botões da lista
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(list_btn_frame, text="🗑️ Deletar", 
                  command=self.delete_element).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(list_btn_frame, text="📋 Ver JSON", 
                  command=self.show_json).pack(side=tk.LEFT, padx=5)
        
        # ===== SEÇÃO 4: VISUALIZAÇÃO =====
        view_frame = ttk.LabelFrame(main_frame, text="4️⃣ Visualização", padding="10")
        view_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Button(view_frame, text="👁️ Mostrar Máscara (5s)", 
                  command=self.show_overlay).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(view_frame, text="💾 SALVAR TUDO", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(view_frame, text="📤 Exportar JSON", 
                  command=self.export_json).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(view_frame, text="Pronto para cadastrar elementos", 
                                     foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Atualizar lista
        self.refresh_list()
        
        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        element_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
    
    def create_slider(self, parent, row, label, var_name, min_val, max_val, current_val):
        """Cria um slider com label, campo de entrada e valor"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
        
        var = tk.IntVar(value=current_val)
        setattr(self, f'slider_{var_name}', var)
        
        # Slider
        slider = ttk.Scale(parent, from_=min_val, to=max_val, 
                          orient=tk.HORIZONTAL, variable=var)
        slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Campo de entrada (Entry)
        entry = ttk.Entry(parent, width=8)
        entry.insert(0, str(current_val))
        entry.grid(row=row, column=2, sticky=tk.W, pady=5, padx=(0, 5))
        
        # Label de valor (mantido para referência)
        value_label = ttk.Label(parent, text=str(current_val), width=6)
        value_label.grid(row=row, column=3, sticky=tk.W, pady=5)
        
        # Atualizar label e entry quando slider muda
        def on_slider_change(*args):
            val = var.get()
            value_label.config(text=str(val))
            entry.delete(0, tk.END)
            entry.insert(0, str(val))
        
        var.trace('w', on_slider_change)
        
        # Atualizar slider quando digita no entry
        def on_entry_change(event):
            try:
                val = int(entry.get())
                if min_val <= val <= max_val:
                    var.set(val)
                    value_label.config(text=str(val))
            except ValueError:
                pass  # Ignora valores inválidos
        
        entry.bind('<Return>', on_entry_change)
        entry.bind('<FocusOut>', on_entry_change)
        
        parent.columnconfigure(1, weight=1)
    
    def capture_position(self):
        """Captura posição do mouse"""
        self.status_label.config(text="Posicione no canto superior esquerdo...", foreground="orange")
        self.root.update()
        
        for i in range(3, 0, -1):
            self.status_label.config(text=f"Capturando em {i}...")
            self.root.update()
            time.sleep(1)
        
        pos = pyautogui.position()
        self.market_x = pos.x
        self.market_y = pos.y
        
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(self.market_x))
        
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(self.market_y))
        
        self.status_label.config(text=f"✅ Posição: ({self.market_x}, {self.market_y})", 
                                foreground="green")
    
    def add_element(self):
        """Adiciona novo elemento"""
        name = self.element_name.get().strip()
        
        if not name:
            messagebox.showwarning("Atenção", "Digite um nome para o elemento!")
            return
        
        if name in self.elements:
            messagebox.showwarning("Atenção", "Elemento já existe! Use 'Atualizar' ou mude o nome.")
            return
        
        self.elements[name] = {
            'x': self.slider_x.get(),
            'y': self.slider_y.get(),
            'w': self.slider_w.get(),
            'h': self.slider_h.get(),
            'desc': self.element_desc.get().strip(),
            'color': self.get_next_color()
        }
        
        self.refresh_list()
        self.status_label.config(text=f"✅ Elemento '{name}' adicionado!", foreground="green")
        
    def update_element(self):
        """Atualiza elemento existente"""
        name = self.element_name.get().strip()
        
        if not name:
            messagebox.showwarning("Atenção", "Digite um nome para o elemento!")
            return
        
        if name not in self.elements:
            messagebox.showwarning("Atenção", "Elemento não existe! Use 'Adicionar'.")
            return
        
        # Manter cor original
        color = self.elements[name].get('color', self.get_next_color())
        
        self.elements[name] = {
            'x': self.slider_x.get(),
            'y': self.slider_y.get(),
            'w': self.slider_w.get(),
            'h': self.slider_h.get(),
            'desc': self.element_desc.get().strip(),
            'color': color
        }
        
        self.refresh_list()
        self.status_label.config(text=f"✅ Elemento '{name}' atualizado!", foreground="green")
    
    def delete_element(self):
        """Deleta elemento selecionado"""
        selection = self.element_listbox.curselection()
        if not selection:
            messagebox.showwarning("Atenção", "Selecione um elemento para deletar!")
            return
        
        name = self.element_listbox.get(selection[0]).split(' - ')[0]
        
        if messagebox.askyesno("Confirmar", f"Deletar '{name}'?"):
            del self.elements[name]
            self.refresh_list()
            self.clear_fields()
            self.status_label.config(text=f"🗑️ Elemento '{name}' deletado!", foreground="orange")
    
    def on_element_select(self, event):
        """Quando seleciona elemento da lista"""
        selection = self.element_listbox.curselection()
        if not selection:
            return
        
        name = self.element_listbox.get(selection[0]).split(' - ')[0]
        element = self.elements[name]
        
        # Preencher campos
        self.element_name.delete(0, tk.END)
        self.element_name.insert(0, name)
        
        self.element_desc.delete(0, tk.END)
        self.element_desc.insert(0, element.get('desc', ''))
        
        self.slider_x.set(element['x'])
        self.slider_y.set(element['y'])
        self.slider_w.set(element['w'])
        self.slider_h.set(element['h'])
        
        self.status_label.config(text=f"📝 Editando: {name}", foreground="blue")
    
    def clear_fields(self):
        """Limpa campos"""
        self.element_name.delete(0, tk.END)
        self.element_desc.delete(0, tk.END)
        self.slider_x.set(0)
        self.slider_y.set(0)
        self.slider_w.set(100)
        self.slider_h.set(30)
        self.status_label.config(text="Campos limpos", foreground="gray")
    
    def refresh_list(self):
        """Atualiza lista de elementos"""
        self.element_listbox.delete(0, tk.END)
        
        for name, data in self.elements.items():
            desc = data.get('desc', '')
            display = f"{name} - {desc}" if desc else name
            coords = f"[{data['x']},{data['y']},{data['w']},{data['h']}]"
            self.element_listbox.insert(tk.END, f"{display} {coords}")
    
    def get_next_color(self):
        """Retorna próxima cor"""
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color
    
    def show_overlay(self):
        """Mostra overlay com todos os elementos"""
        # Atualizar valores
        self.market_x = int(self.x_entry.get())
        self.market_y = int(self.y_entry.get())
        self.offset_x = int(self.offset_x_entry.get())
        self.offset_y = int(self.offset_y_entry.get())
        
        if not self.elements:
            messagebox.showinfo("Info", "Nenhum elemento cadastrado ainda!")
            return
        
        # Criar overlay
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
        
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.4)
        self.overlay_window.overrideredirect(True)
        
        screen_width = self.overlay_window.winfo_screenwidth()
        screen_height = self.overlay_window.winfo_screenheight()
        self.overlay_window.geometry(f'{screen_width}x{screen_height}+0+0')
        
        canvas = tk.Canvas(self.overlay_window, width=screen_width, height=screen_height,
                          bg='black', highlightthickness=0)
        canvas.pack()
        
        base_x = self.market_x + self.offset_x
        base_y = self.market_y + self.offset_y
        
        # Desenhar cada elemento
        for name, data in self.elements.items():
            x = base_x + data['x']
            y = base_y + data['y']
            w = data['w']
            h = data['h']
            color = data.get('color', 'white')
            
            # Retângulo
            canvas.create_rectangle(x, y, x + w, y + h, 
                                   outline=color, width=3)
            
            # Nome
            canvas.create_text(x + w//2, y - 15, 
                              text=name, 
                              fill=color, 
                              font=('Arial', 10, 'bold'))
            
            # Coordenadas
            coords_text = f"[{data['x']}, {data['y']}, {w}, {h}]"
            canvas.create_text(x + w//2, y + h + 15, 
                              text=coords_text, 
                              fill=color, 
                              font=('Arial', 8))
        
        # Instruções
        canvas.create_text(screen_width//2, 30,
                          text=f"TOTAL: {len(self.elements)} elementos | Fecha automaticamente em 5s",
                          fill='white', font=('Arial', 14, 'bold'))
        
        # Fechar automaticamente após 5 segundos
        self.overlay_window.after(5000, lambda: self.overlay_window.destroy() if self.overlay_window.winfo_exists() else None)
        
        # Ou clicar para fechar
        self.overlay_window.bind('<Button-1>', lambda e: self.overlay_window.destroy())
        self.overlay_window.bind('<Escape>', lambda e: self.overlay_window.destroy())
        
        self.status_label.config(text="👁️ Máscara exibida! (5s)", foreground="blue")
    
    def show_json(self):
        """Mostra JSON dos elementos"""
        json_window = tk.Toplevel(self.root)
        json_window.title("📋 JSON dos Elementos")
        json_window.attributes('-topmost', True)
        
        text = scrolledtext.ScrolledText(json_window, width=80, height=30, font=('Courier', 10))
        text.pack(padx=10, pady=10)
        
        json_str = json.dumps(self.elements, indent=4)
        text.insert('1.0', json_str)
        
        ttk.Button(json_window, text="📋 Copiar", 
                  command=lambda: self.copy_to_clipboard(json_str)).pack(pady=10)
    
    def export_json(self):
        """Exporta JSON completo"""
        config = {
            'market_x': self.market_x,
            'market_y': self.market_y,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'elements': self.elements
        }
        
        json_str = json.dumps(config, indent=4)
        
        # Mostrar em janela
        export_window = tk.Toplevel(self.root)
        export_window.title("📤 Exportar Configuração Completa")
        export_window.attributes('-topmost', True)
        
        ttk.Label(export_window, text="Copie este JSON e envie para adaptação:", 
                 font=('Arial', 12, 'bold')).pack(padx=10, pady=10)
        
        text = scrolledtext.ScrolledText(export_window, width=80, height=30, font=('Courier', 10))
        text.pack(padx=10, pady=10)
        text.insert('1.0', json_str)
        
        ttk.Button(export_window, text="📋 Copiar Tudo", 
                  command=lambda: self.copy_to_clipboard(json_str)).pack(pady=10)
    
    def copy_to_clipboard(self, text):
        """Copia para clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Sucesso", "JSON copiado para a área de transferência!")
    
    def run(self):
        """Executa aplicação"""
        self.root.mainloop()


if __name__ == "__main__":
    import time
    
    print("="*70)
    print("📐 PXG MARKET - CADASTRO DE ELEMENTOS")
    print("="*70)
    print("\n🎯 COMO USAR:")
    print("1. Capture a posição do canto superior esquerdo do mercado")
    print("2. Cadastre cada elemento (colunas, botões, campos)")
    print("3. Ajuste posição e tamanho com os sliders")
    print("4. Visualize com 'Mostrar Máscara'")
    print("5. Salve tudo")
    print("6. Exporte o JSON e me envie para adaptação!")
    print("\n" + "="*70 + "\n")
    
    app = ElementRegistrar()
    app.run()