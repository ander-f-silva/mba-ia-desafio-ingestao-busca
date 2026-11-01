import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres import PGVector

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def search_prompt(question: str) -> str:
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))

    vectorstore = PGVector(
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        embedding=embeddings,
        connection=os.getenv("DATABASE_URL"),
    )

    #k=10: retorna os 10 chunks mais similares
    result = vectorstore.similarity_search_with_score(question, k=10)

    #join: junta os chunks em um único string com \n entre eles
    context = "\n\n".join([doc.page_content for doc, score in result])

    prompt = PROMPT_TEMPLATE.format(contexto=context, pergunta=question)

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), temperature=0)
    response = llm.invoke(prompt)

    return response.content