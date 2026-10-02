# SemanticChunker + model2vec: a sentence made only of box-drawing chars (common in CLI READMEs/ASCII diagrams)
# embeds to an all-zero vector -> cosine = 0/0 = NaN + RuntimeWarning.
import warnings, numpy as np, chonkie
from chonkie import SemanticChunker
from chonkie.embeddings import Model2VecEmbeddings
emb = Model2VecEmbeddings("minishlab/potion-base-8M")
box = "┌─────────────────┐"
print("norm(embed(box)) =", np.linalg.norm(emb.embed(box)), "| similarity(box, 'hello') =", emb.similarity(emb.embed(box), emb.embed("hello")))
text = ("Cactus runs models on phones. It supports LoRA merges.\n" + box + "\n│  Cactus Engine  │\n└─────────────────┘\n"
        "Kitten TTS is a tiny speech model. It runs on CPU.")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always", RuntimeWarning)
    cs = SemanticChunker(embedding_model="minishlab/potion-base-8M", chunk_size=512, threshold=0.7).chunk(text)
    print("chonkie", chonkie.__version__, "| RuntimeWarnings during chunk():", [str(x.message) for x in w if issubclass(x.category, RuntimeWarning)])
for c in cs: print("  chunk:", repr(c.text[:70]))
