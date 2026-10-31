import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()

MANDATORY_ENV_VARS = [    
    "OPENAI_API_KEY",
    "OPENAI_EMBEDDING_MODEL",
    "DATABASE_URL",
    "PG_VECTOR_COLLECTION_NAME",
    "PDF_PATH",
]

def check_env_vars():
    for var in MANDATORY_ENV_VARS:
        if not os.getenv(var):
            raise RuntimeError(f"Environment variable {var} is not set")

PDF_PATH = os.getenv("PDF_PATH")

def ingest_pdf():
    check_env_vars()

    # 1) Carregar o PDF
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()

    # 2) Splitar o PDF
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(docs)
    chunks = [c for c in chunks if c.page_content.strip()] #deleta chunks vazios

    # 3) Embeddings
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"))

    # 4) Inserir os chunks no vector store
    PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        pre_delete_collection=True,  # evita duplicar se rodar de novo
    )  

    print(f"Inseridos {len(chunks)} chunks no vector store")

if __name__ == "__main__":
    ingest_pdf()