from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rouge_score import rouge_scorer

def compute_cosine_similarity(text1, text2):
    try:
        vec = TfidfVectorizer().fit([text1, text2])
        tfidf = vec.transform([text1, text2])
        return cosine_similarity(tfidf[0], tfidf[1])[0][0]
    except:
        return 0.0

def compute_rouge_l(summary, reference):
    try:
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        return scorer.score(reference, summary)['rougeL'].fmeasure
    except:
        return 0.0
