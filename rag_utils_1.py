from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

# Load the model and tokenizer (same as sentence-transformers model)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# Sample knowledge base documents
knowledge_base_docs = [
    "The stock market closed higher today with technology stocks leading the gains.",
    "The Federal Reserve announced an interest rate hike amid inflation concerns.",
    "Oil prices surged due to supply constraints and geopolitical tensions.",
    "Cryptocurrency markets saw a sharp decline following regulatory crackdowns.",
    "Major banks reported better-than-expected quarterly earnings."
    "The housing market shows signs of cooling off as mortgage rates rise.",
    "Unemployment rates dropped to a new low, signaling strong economic growth.",
    "Central banks around the world are coordinating policies to stabilize currencies.",
    "The government unveiled new stimulus packages aimed at supporting small businesses.",
    "Trade negotiations between major economies have stalled, impacting global markets.",
]

def mean_pooling(model_output, attention_mask):
    """Mean pooling of token embeddings."""
    token_embeddings = model_output[0]  # First element is the output embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
    return torch.sum(token_embeddings * input_mask_expanded, 1) / \
           torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def embed_text(text: str) -> torch.Tensor:
    """Embed input text into vector space using Hugging Face model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        model_output = model(**inputs)
    return mean_pooling(model_output, inputs['attention_mask'])

# Precompute embeddings for knowledge base
doc_embeddings = torch.stack([embed_text(doc) for doc in knowledge_base_docs]).squeeze()

def retrieve_similar_docs(query_embedding: torch.Tensor, top_k: int = 3):
    """Retrieve top_k similar documents from the knowledge base using cosine similarity."""
    # Normalize for cosine similarity
    query_embedding = F.normalize(query_embedding, p=2, dim=1)
    knowledge_embeddings = F.normalize(doc_embeddings, p=2, dim=1)

    cosine_scores = torch.matmul(query_embedding, knowledge_embeddings.T).squeeze()
    top_k_indices = torch.topk(cosine_scores, k=top_k).indices

    return [knowledge_base_docs[i] for i in top_k_indices]
