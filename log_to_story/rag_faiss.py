import os
from sentence_transformers import SentenceTransformer
import pickle
import numpy as np

try:
    import faiss
    HAS_FAISS = True
except Exception:
    HAS_FAISS = False

MODEL_NAME = 'all-MiniLM-L6-v2'


def _ensure_model():
    return SentenceTransformer(MODEL_NAME)


def build_playbook_index(playbook_path, index_path=None):
    model = _ensure_model()
    with open(playbook_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # split into sections by '## ' headers
    parts = [p.strip() for p in text.split('##') if p.strip()]
    docs = []
    for p in parts:
        lines = p.splitlines()
        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()
        docs.append({'title': title, 'content': content})

    texts = [d['title'] + '\n' + d['content'] for d in docs]
    embeddings = model.encode(texts, convert_to_numpy=True)

    if HAS_FAISS:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings.astype(np.float32))
        index_data = {'index': index, 'docs': docs, 'embeddings_shape': embeddings.shape, 'has_faiss': True}
    else:
        # Fallback: store embeddings and do numpy-based similarity search at query time
        index_data = {'embeddings': embeddings, 'docs': docs, 'has_faiss': False}

    if index_path:
        with open(index_path, 'wb') as f:
            pickle.dump(index_data, f)

    return index_data


def load_playbook_index(path_or_index):
    # if path to saved index
    if isinstance(path_or_index, str) and os.path.exists(path_or_index) and path_or_index.endswith('.md'):
        # build from md and save to temp file
        return build_playbook_index(path_or_index)
    if isinstance(path_or_index, str) and os.path.exists(path_or_index):
        with open(path_or_index, 'rb') as f:
            return pickle.load(f)
    return None


def query_playbook(index_data, query, top_k=3):
    if not index_data:
        return []
    model = _ensure_model()
    q_emb = model.encode([query], convert_to_numpy=True)

    if index_data.get('has_faiss'):
        index = index_data['index']
        D, I = index.search(q_emb.astype(np.float32), top_k)
        results = []
        for i in I[0]:
            if i < 0 or i >= len(index_data['docs']):
                continue
            results.append(index_data['docs'][i])
        return results
    else:
        # numpy cosine similarity fallback
        emb = index_data['embeddings']  # shape (N, d)
        # normalize
        emb_norm = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        qn = q_emb[0]
        qn = qn / np.linalg.norm(qn)
        sims = np.dot(emb_norm, qn)
        idx = np.argsort(-sims)[:top_k]
        results = [index_data['docs'][i] for i in idx]
        return results
