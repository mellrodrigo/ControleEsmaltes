# 💅 Controle de Esmaltes

Aplicativo (PWA) para **cadastro e controle de validade** dos esmaltes da
prateleira. Permite registrar cada esmalte com **várias fotos**, gera
**número de etiqueta sequencial** e **data de cadastro** automaticamente, e
mostra o que está **vencendo / vencido** para retirada da prateleira.

Construído sobre a planilha original `Controle_prateleira_esmaltes_202606.xlsx`,
cujos 1.471 registros são importados e **normalizados** para um banco SQLite.

## Funcionalidades

- 📷 Cadastro com **uma ou mais fotos** do esmalte (câmera do celular ou galeria).
- 🔢 **Etiqueta sequencial automática** (continua de onde a planilha parou).
- 📅 **Data de cadastro automática** e validade por mês/ano.
- 🏷️ Campos: marca, série, cor, validade, status, motivo, data de remoção.
- ⏰ Painel com **na prateleira / vencendo em 90 dias / vencidos / total**.
- 🔎 Busca e filtros (prateleira, vencendo, vencidos, removidos, todos).
- ♻️ Retirar da prateleira (registra data e motivo) ou devolver à prateleira.
- 📲 **PWA instalável** no celular, com ícone na tela inicial e uso offline da interface.
- 🧹 Importação que **padroniza** marcas/status/motivos (ex.: `impala` → `Impala`).

> Observação: a leitura automática dos dados a partir das fotos (IA/OCR) **não**
> está ativada nesta versão — as fotos são anexadas e os campos preenchidos
> manualmente. A estrutura já está pronta para adicionar essa extração depois.

## Tecnologias

- **Back-end:** Python + FastAPI + SQLite (sem ORM, biblioteca padrão).
- **Front-end:** HTML/CSS/JS puro como PWA (manifest + service worker).
- **Imagens:** Pillow (redimensiona e corrige orientação das fotos).

## Como rodar

```bash
# 1. (recomendado) ambiente virtual
python3 -m venv .venv && source .venv/bin/activate

# 2. dependências
pip install -r requirements.txt

# 3. importar a planilha para o banco (cria data/esmaltes.db)
python -m app.importer --recriar

# 4. iniciar o servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Acesse **http://localhost:8000** no navegador. Para usar no celular pela
mesma rede Wi-Fi, acesse `http://IP-DO-COMPUTADOR:8000` e use a opção
**"Adicionar à tela inicial"** do navegador para instalar o app.

## Estrutura

```
app/
  main.py        API FastAPI + servidor estático
  db.py          conexão SQLite, schema e sequência de etiqueta
  normalize.py   normalização de marca, status, motivo e textos
  importer.py    importa e normaliza a planilha original
static/          PWA (index.html, app.js, styles.css, manifest, SW, ícones)
seed/            planilha original usada na importação
data/            banco SQLite e fotos enviadas (gerados em runtime, fora do git)
```

## Banco de dados

Tabela `esmaltes`: `etiqueta` (único), `marca`, `serie`, `cor`, `validade`,
`data_cadastro`, `status`, `motivo`, `data_removido`.
Tabela `fotos`: várias fotos por esmalte (`esmalte_id`, `arquivo`).

O arquivo `data/esmaltes.db` e as fotos em `data/uploads/` **não** vão para o
Git (veja `.gitignore`). Rode o passo 3 após clonar o repositório.
