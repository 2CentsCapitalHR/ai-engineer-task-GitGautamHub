import os
import requests
from bs4 import BeautifulSoup



from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document as LangchainDocument

def create_rag_system(data_path="data/adgm_docs"):
    """
    Loads ADGM documents and web content, splits them, creates embeddings, and saves a FAISS vector store.
    """
    documents = []
    
    # 1. Load documents from the local folder (.pdf and .docx)
    for filename in os.listdir(data_path):
        filepath = os.path.join(data_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())
        elif filename.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(filepath)
            documents.extend(loader.load())
            
    # 2. Scrape content from the provided ADGM web links
    web_links = [
        "https://www.adgm.com/registration-authority/registration-and-incorporation",
        "https://www.adgm.com/setting-up",
        "https://www.adgm.com/legal-framework/guidance-and-policy-statements",
        "https://www.adgm.com/operating-in-adgm/obligations-of-adgm-registered-entities/annual-filings/annual-accounts",
        "https://www.adgm.com/operating-in-adgm/post-registration-services/letters-and-permits"
    ]
    
    for url in web_links:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract text from relevant tags like p, h1, h2, li
                page_text = " ".join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'a', 'span', 'div'])])
                
                if page_text:
                    documents.append(LangchainDocument(page_content=page_text, metadata={"source": url}))
                    print(f"Scraped content from {url}")
            else:
                print(f"Failed to fetch content from {url} with status code {response.status_code}")
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    if not documents:
        print("No documents or web content found to process. RAG system creation aborted.")
        return

    # 3. Split documents into chunks for better processing
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    
    print(f"Loaded {len(documents)} total documents/pages, split into {len(texts)} chunks.")

    # 4. Create embeddings using a HuggingFace model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)

    # 5. Create the FAISS vector store
    db = FAISS.from_documents(texts, embeddings)
    
    # 6. Save the vector store to disk
    db.save_local("faiss_index")
    print("RAG system created and saved as 'faiss_index'!")

if __name__ == "__main__":
    os.makedirs("data/adgm_docs", exist_ok=True)
    create_rag_system()