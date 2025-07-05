from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


LEFT_KEYWORDS = [
    "climate change", "diversity", "social justice", "inequality", "progressive", "gun control"
]
RIGHT_KEYWORDS = [
    "tax cuts", "border security", "second amendment", "free market", "patriot", "conservative"
]

def detect_bias(text: str) -> str:
    """Detects political bias in the input text based on keyword cosine similarity."""

    # Join keyword sets into pseudo-documents
    left_doc = " ".join(LEFT_KEYWORDS)
    right_doc = " ".join(RIGHT_KEYWORDS)

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([text, left_doc, right_doc])
    text_vec, left_vec, right_vec = vectors[0], vectors[1], vectors[2]

    # Compute cosine similarities
    sim_to_left = cosine_similarity(text_vec, left_vec)[0][0]
    sim_to_right = cosine_similarity(text_vec, right_vec)[0][0]

    # Determine bias based on similarity
    if abs(sim_to_left - sim_to_right) < 0.05:
        return "Center"
    elif sim_to_left > sim_to_right:
        return "Left"
    else:
        return "Right"