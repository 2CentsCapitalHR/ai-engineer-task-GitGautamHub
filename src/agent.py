import os
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from docx import Document

# Load the RAG system
def load_rag_system():
    """Loads the pre-built FAISS vector store."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()
    return retriever

def analyze_document(doc_content, retriever, llm):
    """Analyzes a single document for red flags using the RAG system."""
    
    # Prompt for Red Flag Detection
    prompt_template = """
    You are an ADGM-compliant corporate legal assistant. Your task is to review the following document content based on ADGM laws and regulations.
    Use the provided ADGM context to identify any legal inconsistencies or red flags from the following list:
    - Invalid or missing clauses
    - Incorrect jurisdiction (e.g., referencing UAE Federal Courts instead of ADGM)
    - Ambiguous or non-binding language
    - Missing signatory sections or improper formatting
    - Non-compliance with ADGM-specific templates

    Document Content:
    "{doc_content}"

    ADGM Context:
    "{context}"

    Instructions:
    - For each issue found, provide a clear description, its severity (High/Medium/Low), and a suggestion for correction.
    - Also, find the exact line or text snippet from the "Document Content" that has the issue.
    - If no issues are found, return an empty list.
    - Output the result as a structured JSON object, following this exact schema:

    Example Output:
    [
        {{
            "issue": "Jurisdiction clause does not specify ADGM",
            "section": "Clause 3.1",
            "relevant_text": "This agreement is governed by the laws of the UAE Federal Courts.",
            "severity": "High",
            "suggestion": "Update jurisdiction to ADGM Courts."
        }}
    ]

    JSON Output:
    """
    
    # Create a RetrievalQA chain to get answers from the RAG system
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    response = qa_chain({"query": prompt_template.format(doc_content=doc_content, context="")})
    
    return response['result']


def identify_legal_process(uploaded_files):
    # A simple, keyword-based approach to identify the process
    uploaded_doc_names = [f.name.lower() for f in uploaded_files]
    
    if any("incorporation" in name for name in uploaded_doc_names) or any("moa" in name for name in uploaded_doc_names):
        return "Company Incorporation"
    elif any("employment" in name for name in uploaded_doc_names):
        return "Employment HR"
    
    return "Unknown"

def check_missing_documents(uploaded_files):
    """
    Checks for missing documents based on a predefined checklist.
    For this example, we'll hardcode the checklist for 'Company Incorporation'.
    """
    required_docs_for_incorporation = [
        "Articles of Association",
        "Memorandum of Association",
        "Board Resolution Templates",
        "UBO Declaration Form",
        "Register of Members and Directors"
    ]

    uploaded_doc_names = [f.name for f in uploaded_files]
    missing_docs = []
    
    for required_doc in required_docs_for_incorporation:
        if not any(required_doc.lower() in name.lower() for name in uploaded_doc_names):
            missing_docs.append(required_doc)
            
    return missing_docs, len(required_docs_for_incorporation)

