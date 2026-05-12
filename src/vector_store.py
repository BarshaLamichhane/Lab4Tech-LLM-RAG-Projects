
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# step 1 chunk => split the documents into smaller pieces (chunks) to ensure they fit within the token limits of the embedding model and to improve retrieval performance.
# step 2 embedding => convert the text chunks into vector representations (embeddings) using a pre-trained model. These embeddings capture the semantic meaning of the text, allowing for more effective similarity comparisons. 
# step 3 vector store => store the generated embeddings in a vector database (FAISS) that allows for efficient similarity search and retrieval based on the vector representations of the text chunks. This enables the RAG pipeline to quickly find relevant information when processing user queries or matching CVs to job descriptions.


def create_vector_store(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512, # 512 is a common chunk size that balances context retention with token limits for embedding models. It allows for enough context to be captured in each chunk while ensuring that the chunks are not too large to exceed the model's input limits.
        chunk_overlap=50 # 50 is a common overlap size that helps maintain context between chunks. It ensures that important information that may be split between two chunks is still captured in both, improving the quality of the embeddings and retrieval performance.
        ## chunk_overlap 50 means that when the text is split into chunks, there will be an overlap of 50 characters between consecutive chunks. This helps to ensure that important context is not lost when splitting the text, as some information may be relevant across chunk boundaries. The overlap allows for better continuity and understanding of the text when generating embeddings and performing retrieval in the RAG pipeline.
    )

    chunks = splitter.create_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    ##embeddings.embed_documents([chunk.page_content for chunk in chunks])[:2] is a line of code that generates embeddings for the first two chunks of text using the specified HuggingFace embedding model. It takes the content of each chunk (chunk.page_content) and converts it into a vector representation (embedding) that captures the semantic meaning of the text. The resulting embeddings can then be used for similarity comparisons and retrieval in the RAG pipeline. The [:2] at the end indicates that only the embeddings for the first two chunks are being generated and printed for inspection.   
    print(f"embeddings sentences: {embeddings.embed_documents([chunk.page_content for chunk in chunks])[:2]}...")

    vector_db = FAISS.from_documents(
        chunks,
        embeddings
    )

    return vector_db

def retrieve_relevant_context(vector_db, query: str, k: int = 3) -> str:
    ###query is the user query or the target role for which we want to retrieve relevant context from the vector database. The function performs a similarity search in the vector database using the query and retrieves the top k most relevant chunks of text based on their embeddings. The retrieved chunks are then combined into a single string of context that can be used for further processing in the RAG pipeline, such as generating explanations or matching CVs to job descriptions.
    results = vector_db.similarity_search(query, k=k)

    context = "\n\n".join([doc.page_content for doc in results]) 

    return context