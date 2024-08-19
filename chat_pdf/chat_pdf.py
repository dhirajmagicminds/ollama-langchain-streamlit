#chat_pdf.py

import os
import uuid
from flask import Flask, request, jsonify
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

app = Flask(__name__)

# Dictionary to store RAG data for each session
session_rag_data = {}

class ChatPDF:
    
    def __init__(self):
        self.model = ChatOllama(model="phi3:latest", base_url="http://ollama:11434", verbose=True)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
        self.embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.prompt_template = PromptTemplate.from_template(
            """
            <s> [INST] You are an assistant for answering questions. Use the following context to answer the question. 
            If you do not know the answer, simply say that you do not know. Use at most three sentences and be concise in your response. [/INST] </s> 
            [INST] Question: {question} 
            Context: {context} 
            Answer: [/INST]
            """
        )

    def ingest(self, pdf_file_path: str, session_id: str):
        try:
            # Load and process the PDF
            docs = PyPDFLoader(file_path=pdf_file_path).load()
            chunks = self.text_splitter.split_documents(docs)
            print(f"chunks created: {len(chunks)}")

            persist_directory = f"./chroma_db/{session_id}"
            os.makedirs(persist_directory, exist_ok=True)
            db = Chroma.from_documents(chunks, self.embedding, persist_directory=persist_directory)
            
            # Store RAG data for the session
            session_rag_data[session_id] = db
            print(f"FAQ RAG data created and persisted for session ID: {session_id}")

            return jsonify({"session_id": session_id, "message": "PDF ingested successfully and FAQ data created."})
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return jsonify({"error": f"Error processing PDF: {str(e)}"}), 500

    def ask(self, session_id: str, query: str):
        try:
            if session_id not in session_rag_data:
                return jsonify({"error": "FAQ data is not available for this session. Please contact the admin to upload the FAQ document."}), 404

            # Retrieve session-specific RAG data
            db = session_rag_data[session_id]
            matching_docs = db.similarity_search(query)
            print(f"Matched documents: {len(matching_docs)} numbers")

            if not matching_docs:
                return jsonify({"response": "No relevant documents/result found."})

            chain = RetrievalQA.from_chain_type(
                llm=self.model,
                retriever=db.as_retriever(),
                chain_type='stuff',
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True,
                verbose=True
            )
            print("Chain created")
            result = chain.invoke({"input_documents": matching_docs, "query": query})
            response_text = result.get('result', 'No answer found.')
            print(f"Response text length: {len(response_text)}")

            return jsonify({"response": response_text})
        except Exception as e:
            print(f"Error during query processing: {str(e)}")
            return jsonify({"error": f"Error during query processing: {str(e)}"}), 500

@app.route('/ingest', methods=['POST'])
def admin_ingest():
    try:
        pdf_file = request.files['file']
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        temp_file_path = f'/tmp/{pdf_file.filename}'
        pdf_file.save(temp_file_path)

        chat_pdf = ChatPDF()
        result = chat_pdf.ingest(temp_file_path, session_id)
        os.remove(temp_file_path)

        return result
    except Exception as e:
        print(f"Error ingesting PDF: {str(e)}")
        return jsonify({"error": f"Error ingesting PDF: {str(e)}"}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        session_id = data.get('session_id')
        query = data.get('query')
        
        if not session_id:
            return jsonify({"error": "Session ID is not set. Please ask the admin to upload the relevant documents."}), 400

        print(f"ask API parameters - Session ID: {session_id}, Query: {query}")

        chat_pdf = ChatPDF()
        response = chat_pdf.ask(session_id, query)
        return response
    except Exception as e:
        print(f"Error during query processing: {str(e)}")
        return jsonify({"error": f"Error during query processing: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
