# 🎯 DETECÇÃO AUTOMÁTICA DE COLUNAS

## 🆕 Novidade!

Agora o sistema **DETECTA AS COLUNAS AUTOMATICAMENTE**! 🚀

### ❌ Antes (modo antigo):
- Você tinha que definir posições FIXAS de cada coluna
- Se o texto mudava de tamanho, não funcionava
- Muito trabalho manual

### ✅ Agora (modo novo):
- **Lê a linha TODA**
- **Detecta automaticamente** onde estão os espaços
- **Separa as colunas** sozinho
- Funciona mesmo se o texto tiver tamanhos diferentes!

## 📦 Arquivos:

1. **column_detector.py** - Detecta colunas automaticamente
2. **test_auto_columns.py** - Sistema principal com detecção automática
3. **ocr_engine.py** - Motor de OCR com EasyOCR

## 🚀 Instalação:

```bash
pip install pillow pandas matplotlib seaborn pyautogui easyocr numpy scipy
```

## 💡 Como Funciona:

1. **Captura a linha toda** (ex: "Feather Stone | Phoneutrya | 1 | 7K")
2. **Analisa densidade de pixels** verticalmente
3. **Detecta onde tem espaços grandes** (baixa densidade)
4. **Divide automaticamente** em colunas
5. **Passa cada coluna para o OCR**

## 🎮 Como Usar:

```bash
# Execute o sistema com detecção automática
python test_auto_columns.py
```

**Menu:**
1. Normal
2. Debug (RECOMENDADO - salva visualizações) ⭐

**Modo Debug salva:**
- Linha completa
- Cada coluna separada
- Gráfico de densidade
- Visualização dos cortes

## 🔧 Como Ajustar:

Se não estiver detectando corretamente, ajuste no `column_detector.py`:

```python
# Linha 13 - Gap mínimo entre colunas
self.min_gap_width = 10  # Aumente para 15 ou 20
```

## 📊 Exemplo Visual:

```
Densidade:  ████░░░░████░░░████░░░██
Linha:      Feather Stone  Phoneutrya  1  7K
            ↑              ↑           ↑  ↑
            Col1           Col2       Col3 Col4
```

## 🐛 Debug:

Execute em modo Debug e abra a pasta `debug_captures/`:
- `Linha01_full.png` - Linha completa
- `Linha01_density.png` - Gráfico de densidade
- `Linha01_col1_original.png` - Coluna 1
- `Linha01_col2_original.png` - Coluna 2
- etc...

## ✨ Vantagens:

✅ Não precisa cadastrar posição de cada coluna  
✅ Funciona com textos de tamanhos variáveis  
✅ Mais robusto e inteligente  
✅ Detecta automaticamente quantas colunas existem  
✅ Adapta-se a diferentes layouts  

## 📝 Notas:

- **Primeira vez:** EasyOCR demora para baixar modelos (2-5 min)
- **Depois:** Fica rápido! ⚡
- **Recomendado:** Sempre use modo Debug na primeira vez

---

**Feito com ❤️ para facilitar ainda mais o grind no PXG!**
