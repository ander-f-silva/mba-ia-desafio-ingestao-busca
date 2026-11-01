# Ingestão e Busca Semântica com LangChain e Postgres

Software de RAG (Retrieval-Augmented Generation): lê o `document.pdf`, grava os embeddings no PostgreSQL com pgVector e responde perguntas no terminal **somente** com o conteúdo do PDF.

Esta implementação usa **OpenAI**:

- embeddings: `text-embedding-3-small`
- LLM do chat: `gpt-4o-mini`

## O que o usuário faz

1. Sobe o banco (Docker).
2. Configura as variáveis de ambiente (API key + conexão).
3. Roda a ingestão (`src/ingest.py`) — carrega o PDF no PGVector.
4. Roda o chat (`src/chat.py`) — pergunta e recebe resposta.

```
PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhões de reais.

PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Para sair do chat, envie uma linha vazia (Enter sem texto).

---

## Pré-requisitos

| Ferramenta | Para quê |
|---|---|
| **Python 3.11 ou 3.12** | As dependências (ex.: `numpy==2.3.2`) não instalam no 3.9 do macOS |
| **Docker Desktop** (ou Rancher Desktop) com Compose | PostgreSQL + pgVector |
| **Conta OpenAI** e API key | Embeddings (`text-embedding-3-small`) e chat (`gpt-4o-mini`) |

No macOS, o `python3` do sistema costuma ser 3.9. Instale outro Python, por exemplo:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 --version
```

Confirme que o Docker está rodando (`docker ps` precisa funcionar).

---

## 1. Clonar o repositório

```bash
git clone <url-do-seu-fork>
cd mba-ia-desafio-ingestao-busca
```

Estrutura:

```
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── document.pdf
├── src/
│   ├── ingest.py    # carrega o PDF no banco
│   ├── search.py    # busca + LLM
│   └── chat.py      # CLI do usuário
└── README.md
```

---

## 2. Ambiente virtual e dependências

Use o Python 3.12 (não o 3.9 do Mac):

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python --version          # deve ser 3.12.x
pip install -U pip
pip install -r requirements.txt
```

No Cursor/VS Code: **Python: Select Interpreter** → `.venv/bin/python`.

---

## 3. Variáveis de ambiente

Copie o template e **preencha o `.env`** (nunca commite o `.env`; ele já está no `.gitignore`):

```bash
cp .env.example .env
```

Valores usados por este projeto (OpenAI + banco do `docker-compose.yml`):

| Variável | Obrigatória | Exemplo / função |
|---|---|---|
| `OPENAI_API_KEY` | Sim | Key em https://platform.openai.com/api-keys |
| `OPENAI_EMBEDDING_MODEL` | Sim | `text-embedding-3-small` (mesmo modelo da ingestão e da busca) |
| `OPENAI_MODEL` | Sim (chat) | LLM, ex.: `gpt-4o-mini` — usada em `src/search.py` |
| `DATABASE_URL` | Sim | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | Sim | Nome da collection, ex.: `documents` |
| `PDF_PATH` | Sim (ingestão) | `./document.pdf` |
| `GOOGLE_API_KEY` / `GOOGLE_EMBEDDING_MODEL` | Não | Não usadas nesta versão (só OpenAI) |

Exemplo de `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=documents
PDF_PATH=./document.pdf
```

`postgresql+psycopg://` usa o driver psycopg3, que é o do `langchain-postgres`.

**Importante:** ingestão e chat devem usar o **mesmo** modelo de embedding. Trocar o modelo depois exige apagar a collection (ou o volume do Docker) e ingerir de novo.

---

## 4. Subir o PostgreSQL + pgVector

Na raiz do projeto, com o Docker ligado:

```bash
docker compose up -d
docker ps
```

O container `postgres_rag` deve ficar **healthy**. Credenciais do compose:

- usuário: `postgres`
- senha: `postgres`
- banco: `rag`
- porta: `5432`

---

## 5. Ingerir o PDF (`ingest.py`)

Com o venv **ativado** e o `.env` preenchido:

```bash
python src/ingest.py
```

O script:

1. Lê `PDF_PATH` (`document.pdf`).
2. Parte o texto em chunks de 1000 caracteres com overlap 150.
3. Gera embeddings com a OpenAI.
4. Grava na collection do PGVector (`pre_delete_collection=True` apaga a collection anterior para não duplicar).

Na primeira execução pode aparecer o aviso `Collection not found`. É esperado: a collection ainda não existia. Ao final deve imprimir algo como `Inseridos N chunks no vector store`.

Conferir no banco (opcional):

```bash
docker exec -it postgres_rag psql -U postgres -d rag -c "SELECT COUNT(*) FROM langchain_pg_embedding;"
docker exec -it postgres_rag psql -U postgres -d rag -c "SELECT LEFT(document, 200) FROM langchain_pg_embedding LIMIT 5;"
```

Se `COUNT` for `0`, a ingestão não gravou. Não rode o chat antes de ter chunks no banco.

---

## 6. Usar o chat (`chat.py`)

Ainda com o venv ativo, o banco no ar e a ingestão feita:

```bash
python src/chat.py
```

O terminal pede a pergunta:

```
PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: ...
```

Fluxo interno (`search.py`):

1. Vetoriza a pergunta com o mesmo modelo de embedding.
2. Busca os 10 chunks mais próximos (`k=10`).
3. Monta o prompt obrigatório (contexto + regras).
4. Chama a LLM (`OPENAI_MODEL`).
5. Imprime só o que estiver no contexto do PDF.

Perguntas fora do PDF devem responder:

`Não tenho informações necessárias para responder sua pergunta.`

---

## Ordem resumida

```bash
# 1. Python 3.12 + venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# 2. Segredos e conexão
cp .env.example .env
# edite o .env (API key, DATABASE_URL, modelos, PDF_PATH, collection)

# 3. Banco
docker compose up -d

# 4. Carga do PDF
python src/ingest.py

# 5. Chat para o usuário
python src/chat.py
```

---

## Problemas comuns

| Sintoma | Causa / o que fazer |
|---|---|
| `No matching distribution found for numpy==2.3.2` | Python < 3.11. Recrie o venv com 3.12 |
| `Cannot connect to Docker` | Abra o Docker Desktop / Rancher e tente de novo |
| `Environment variable X is not set` | Variável vazia no `.env` |
| `unexpected keyword argument 'embedding'` | No `PGVector(...)` use `embeddings=` |
| `unexpected keyword argument 'connection_string'` | Use `connection=` |
| `Collection not found` na ingestão | Aviso da 1ª carga; se o script terminar e imprimir os chunks, ok |
| Chat sem contexto / respostas vazias | Rode `ingest.py` de novo e confira `COUNT(*)` no banco |
| Erro de dimensão de vetor | Trocou o modelo de embedding; apague o volume e ingira de novo: `docker compose down -v && docker compose up -d` |

---

## Requisitos do desafio (referência)

- Chunks: 1000 caracteres, overlap 150.
- Store: PostgreSQL + pgVector via Docker Compose.
- Busca: `similarity_search_with_score(query, k=10)`.
- Respostas apenas com o CONTEXTO do PDF.

## Entregável

Repositório público no GitHub com o código e este README.
