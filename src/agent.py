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
    
    # The response will contain the LLM's output and source documents
    # The LLM is instructed to return JSON, which we will parse later.
    return response['result']


def identify_legal_process(uploaded_files):
    # A simple, keyword-based approach to identify the process
    uploaded_doc_names = [f.name.lower() for f in uploaded_files]
    
    if any("incorporation" in name for name in uploaded_doc_names) or any("moa" in name for name in uploaded_doc_names):
        return "Company Incorporation"
    elif any("employment" in name for name in uploaded_doc_names):
        return "Employment HR"
    # Add more conditions for other categories as needed
    
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
        # A simple check based on filename, can be more sophisticated
        if not any(required_doc.lower() in name.lower() for name in uploaded_doc_names):
            missing_docs.append(required_doc)
            
    return missing_docs, len(required_docs_for_incorporation)

if __name__ == "__main__":
    
    # 1. Load RAG System
    retriever = load_rag_system()
    
    # 2. Setup LLM
    
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o", openai_api_key=os.environ.get("OPENAI_API_KEY"))

    # 3. Simulate uploaded documents (for testing)
    # A flawed document for testing red flag detection
    flawed_doc_content = "This agreement is governed by the laws of the UAE Federal Courts."
    
    # 4. Analyze the flawed document
    analysis_result = analyze_document(flawed_doc_content, retriever, llm)
    print("--- Document Analysis Result ---")
    print(analysis_result)
    
    # 5. Check for missing documents (simulating a list of uploaded file objects)
    # Let's say user uploaded 4 out of 5 docs
    dummy_uploaded_files = [
        type('obj', (object,), {'name': 'Articles of Association.docx'}),
        type('obj', (object,), {'name': 'Memorandum of Association.docx'}),
        type('obj', (object,), {'name': 'UBO Declaration Form.docx'}),
        type('obj', (object,), {'name': 'Board Resolution Templates.docx'})
    ]
    missing_docs, total_docs = check_missing_documents(dummy_uploaded_files)
    
    print("\n--- Document Checklist Result ---")
    print(f"Total documents required: {total_docs}")
    print(f"Uploaded documents: {len(dummy_uploaded_files)}")
    print(f"Missing documents: {', '.join(missing_docs)}")