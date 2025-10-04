from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


class Database:
    def __init__(self, persist_directory="./discord_db", model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        # Initialize Chroma vector database
        self.vector_db = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)


    def add_message(self, content, username, date):
        metadata = {
            "username": username,
            "date": date
        }
        self.vector_db.add_texts([content], metadatas=[metadata])


    def query(self, question, k=50, min_confidence=0.7, max_results=None):
        """
        Perform a semantic search with normalized confidence.


        Args:
            question (str): Query text.
            k (int): Number of top results to retrieve initially.
            min_confidence (float): Minimum confidence (0-1) to keep a message.
            max_results (int | None): Maximum number of messages to return.


        Returns:
            List of tuples: (content, metadata, confidence)
        """
        # Get top-k results with raw scores
        results_with_scores = self.vector_db.similarity_search_with_score(question, k=k)


        if not results_with_scores:
            return []


        # Extract raw distances/scores
        scores = [score for _, score in results_with_scores]
        min_score, max_score = min(scores), max(scores)


        # Normalize to confidence 0-1 (higher = more similar)
        normalized_results = []
        for doc, score in results_with_scores:
            if max_score - min_score == 0:
                confidence = 1.0  # avoid divide by zero
            else:
                confidence = 1 - (score - min_score) / (max_score - min_score)
            if confidence >= min_confidence:
                normalized_results.append((doc.page_content, doc.metadata, confidence))




        # Optionally limit max results
        if max_results:
            normalized_results = normalized_results[:max_results]


        return normalized_results


# Example usage
if __name__ == "__main__":
    db = Database()
    db.add_message("Alex said to meet at 3 PM", "Alex", "2025-10-04")
    db.add_message("Don't forget the meeting tomorrow", "Jamie", "2025-10-03")
    db.add_message("Fuck off", "Jamie", "2025-10-03")


    query_results = db.query("When did Alex say to meet?", k=10, min_confidence=0.5)


    for content, metadata, confidence in query_results:
        print(f"Content: {content}, Metadata: {metadata}, Confidence: {confidence:.7f}")
