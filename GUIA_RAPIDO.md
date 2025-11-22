# 🚀 GUIA RÁPIDO - Começar em 3 Passos

## 📦 Passo 1: Instalar

```bash
pip install pillow pandas matplotlib seaborn pyautogui easyocr numpy scipy
```

**⚠️ IMPORTANTE:** Na primeira execução, EasyOCR vai baixar modelos (2-5 minutos). É normal!

## 📁 Passo 2: Arquivos Necessários

Baixe e coloque na mesma pasta:
- ✅ `test_auto_columns_final.py` (sistema principal)
- ✅ `column_detector_final.py` (detector de colunas)
- ✅ `ocr_engine.py` (motor de OCR)
- ✅ `market_elements.json` (configuração - você já tem)

## 🎮 Passo 3: Executar

```bash
python test_auto_columns_final.py
```

**Menu:**
```
1. Normal
2. Debug (salva imagens) ⭐ ESCOLHA ESTE!
```

**Depois:**
```
1. Captura única (teste)
2. Auto-refresh (5 segundos) ⭐ ESCOLHA ESTE!
3. Auto-refresh (10 segundos)
...
```

## 🎯 O que vai acontecer:

1. Sistema clica em "Atualizar" sozinho
2. Captura as 8 linhas visíveis
3. **Para cada linha:**
   - Analisa densidade de pixels
   - Encontra os VALES (espaços entre colunas)
   - Divide em colunas automaticamente
   - OCR em cada coluna
   - Salva no DataFrame
4. Mostra estatísticas
5. Repete a cada 5 segundos

**Pressione Ctrl+C para parar!**

## 📊 Verificando se Funcionou:

Abra a pasta `debug_captures/`:

```
debug_captures/
├─ Linha01_full.png          ← Linha completa capturada
├─ Linha01_density.png       ← Gráfico mostrando vales detectados
├─ Linha01_col1_original.png ← Coluna 1 (Nome)
├─ Linha01_col2_original.png ← Coluna 2 (Vendedor)
├─ Linha01_col3_original.png ← Coluna 3 (Quantidade)
├─ Linha01_col4_original.png ← Coluna 4 (Preço)
├─ Linha01_col1_processed.png ← Coluna 1 processada para OCR
...
```

**Abra `Linha01_density.png`:**
- Veja o gráfico de densidade
- Vales marcados em **vermelho** (espaços detectados)
- Imagem original embaixo

Se os vales estiverem nos lugares certos = **FUNCIONANDO! ✅**

## 🔧 Se não funcionar bem:

### Detectou colunas demais:
Edite `column_detector_final.py`, linha 70:
```python
prominence=0.2  # Era 0.15, aumente para 0.2 ou 0.25
```

### Não detectou algumas colunas:
```python
prominence=0.1  # Era 0.15, diminua para 0.1
```

### OCR não lê nada:
1. Certifique-se que instalou: `pip install easyocr`
2. Primeira vez DEMORA (2-5 min baixando modelos)
3. Depois fica rápido!

## 📈 Estatísticas em Tempo Real:

```
📊 ESTATÍSTICAS RÁPIDAS
────────────────────────────────────────
📦 Total de linhas capturadas: 24
🏷️  Itens únicos: 18
👥 Vendedores únicos: 12
💰 Preço médio: 45,250
💎 Preço máximo: 500,000
💵 Preço mínimo: 1,000
📦 Quantidade total: 86
────────────────────────────────────────
```

## 💾 Salvar Dados:

Durante execução:
- Opção **6**: Mostrar DataFrame
- Opção **7**: Exportar CSV

Ao sair (Ctrl+C):
- Sistema pergunta se quer salvar
- Gera arquivo `market_data_YYYYMMDD_HHMMSS.csv`

## ✨ Diferencial:

### Outros sistemas:
❌ Precisam de posições FIXAS de cada coluna
❌ Se texto mudar de tamanho, quebra
❌ Muito trabalho manual

### Este sistema:
✅ Detecta colunas **AUTOMATICAMENTE**
✅ Funciona com textos de qualquer tamanho
✅ Adapta-se sozinho
✅ **LÊ A LINHA TODA e divide inteligentemente**

## 🎯 Exemplo Real:

Sua linha: `Sneasler Backpack    Aschow Ww    1    -`

Sistema detecta:
1. Vale em x=243 → separa "Sneasler Backpack" | "Aschow Ww"
2. Vale em x=377 → separa "Aschow Ww" | "1"
3. Vale em x=432 → separa "1" | "-"

Resultado:
```python
{
  'Nome': 'Sneasler Backpack',
  'Vendedor': 'Aschow Ww',
  'Quantidade': 1,
  'Preco': 0  # "-" vira 0
}
```

---

**Pronto! Agora é só rodar e deixar trabalhando! 🚀**

**Dúvidas? Leia o README_FINAL.md para mais detalhes!**
