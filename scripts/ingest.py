# ingest.py
import glob
import os
from typing import List

# load from .env file
from dotenv import load_dotenv
load_dotenv()

# for reading files
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# for splitting large documents
from langchain_text_splitters import RecursiveCharacterTextSplitter

# to convert text chunks into embeddings
from langchain_openai import OpenAIEmbeddings

# for storing and querying the embeddings 
from langchain_community.vectorstores import Chroma

# config
DATA_DIR = "data"   # personal data
PERSIST_DIR = "chroma"   # on disk db folder 
COLLECTION = "profile"   # logical collection name
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# load documents
def load_docs() -> List:
    """
    walk the data/ folder and load PDFs and .txt files.
    each loader returns list of LangChain document objects:
    - .page_content
    - .metadata
    """
    docs = []

    for path in glob.glob(f"{DATA_DIR}/**/*.pdf", recursive=True):
        docs.extend(PyPDFLoader(path).load())

    return docs


# split into chunks
def chunk_docs(docs: List) -> List:
    """
    split docs into overlapping chunks so retrieval can return focused context
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_documents(docs)

    for d in chunks:
        meta = d.metadata or {}
        meta.setdefault("doc_type", "resume")
        d.metadata = meta
    
    return chunks

# embed + store
def build_index(chunks: List):
    """
    convert chunks -> vectors and persist to Chroma
    """
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name=COLLECTION,
    )
    vectordb.persist()
    return vectordb

def main():
    docs = load_docs()
    if not docs:
        print("No documents found in ./data. Add your resume")
        return 
    print(f"loaded {len(docs)} documents"
          f"(e.g., pages), first source: {docs[0].metadata.get('source')}")
    
    sample_text = docs[0].page_content[:400].replace("\n", " ")
    print(f"Sample extracted text: {sample_text!r}\n")

    # B2) Chunk
    chunks = chunk_docs(docs)
    print(f"Created {len(chunks)} chunks. Example chunk len:",
          len(chunks[0].page_content))

    # C1) Embed + store
    _ = build_index(chunks)
    print(f"✅ Indexed {len(chunks)} chunks → {PERSIST_DIR}/ "
          f"(collection: {COLLECTION})")

if __name__ == "__main__":
    main()


