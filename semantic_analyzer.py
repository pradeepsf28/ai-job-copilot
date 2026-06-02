from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_match(resume_text, job_text):
    if not resume_text or not job_text:
        return {
            "semantic_score": 0,
            "label": "No Match"
        }

    embeddings = model.encode([resume_text, job_text])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    score = round(similarity * 100)

    if score >= 80:
        label = "Strong semantic match"
    elif score >= 60:
        label = "Good semantic match"
    elif score >= 40:
        label = "Moderate semantic match"
    else:
        label = "Low semantic match"

    return {
        "semantic_score": score,
        "label": label
    }
