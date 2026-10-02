"""Chunker bake-off on a real doc corpus: which Chonkie chunker gives the best retrieval?
Local only: model2vec potion-base-8M embeddings, cosine top-k. Hit = retrieved chunk contains the answer string."""
import glob, time, json, numpy as np
from chonkie import TokenChunker, SentenceChunker, RecursiveChunker, SemanticChunker, FastChunker
from chonkie.embeddings import Model2VecEmbeddings

QA = [  # (question, answer substring that must appear in the retrieved chunk)
 ("Which port does cactus serve listen on by default?", "8080"),
 ("How do I merge a LoRA adapter when converting a model for Cactus?", "--lora"),
 ("What confidence threshold is used in the hybrid inference example?", "0.7"),
 ("What AUROC does the probe reach on audio benchmarks?", "0.79"),
 ("Which HF weight tag should I use for my runtime version?", "latest HF weight tag that is"),
 ("What sample rate does Kitten TTS output?", "24 kHz"),
 ("How many parameters does kitten-tts-micro have?", "40M"),
 ("How do I change the speech speed in Kitten TTS?", "speed=1.2"),
 ("Where does RunAnywhere cache models by default?", "~/.runanywhere"),
 ("Which extra do I install for RunAnywhere RAG support?", 'runanywhere[rag]'),
 ("What happens if I call ra.voice.create_session in the Python SDK?", "SDKException"),
 ("How do I list downloaded models in RunAnywhere?", "ModelFilter(downloaded=True)"),
 ("What is Needle?", "26m parameter"),
 ("How do I install Kitten TTS on GPU?", "requirements_gpu.txt"),
]
docs = {p.split("/")[-1]: open(p).read() for p in sorted(glob.glob("corpus/*.md"))}
emb = Model2VecEmbeddings("minishlab/potion-base-8M")
Q = np.array(emb.embed_batch([q for q, _ in QA]))
Q /= np.linalg.norm(Q, axis=1, keepdims=True)

chunkers = {
  "token(512,ovl64)": TokenChunker(tokenizer="gpt2", chunk_size=512, chunk_overlap=64),
  "sentence(512)":    SentenceChunker(tokenizer="gpt2", chunk_size=512, chunk_overlap=64),
  "recursive(512)":   RecursiveChunker(tokenizer="gpt2", chunk_size=512),
  "recursive-md(512)":RecursiveChunker.from_recipe("markdown", tokenizer="gpt2", chunk_size=512),
  "semantic(512)":    SemanticChunker(embedding_model="minishlab/potion-base-8M", chunk_size=512, threshold=0.7),
  "fast(2048B)":      FastChunker(chunk_size=2048),
}
rows = []
for name, ch in chunkers.items():
    t = time.time(); allc = []; bad_offsets = 0
    for fn, text in docs.items():
        for c in ch.chunk(text):
            allc.append((fn, c.text))
            if text[c.start_index:c.end_index] != c.text: bad_offsets += 1
    ct = time.time() - t
    E = np.array(emb.embed_batch([c for _, c in allc])); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
    top = np.argsort(-(Q @ E.T), axis=1)
    h1 = sum(a in allc[top[i, 0]][1] for i, (_, a) in enumerate(QA))
    h5 = sum(any(a in allc[j][1] for j in top[i, :5]) for i, (_, a) in enumerate(QA))
    rows.append(dict(chunker=name, chunks=len(allc), avg_chars=int(np.mean([len(c) for _, c in allc])),
                     chunk_s=round(ct, 2), hit1=f"{h1}/{len(QA)}", hit5=f"{h5}/{len(QA)}", offset_mismatches=bad_offsets))
    print(rows[-1], flush=True)
json.dump(rows, open("rag_eval_results.json", "w"), indent=1)
