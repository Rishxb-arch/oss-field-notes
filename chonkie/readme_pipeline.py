from chonkie import Pipeline
pipe = (
    Pipeline()
    .chunk_with("recursive", tokenizer="gpt2", chunk_size=2048, recipe="markdown")
    .chunk_with("semantic", chunk_size=512)
    .refine_with("overlap", context_size=128)
    .refine_with("embeddings", embedding_model="sentence-transformers/all-MiniLM-L6-v2")
)
doc = pipe.run(texts="Chonkie is the goodest boi! My favorite chunking hippo hehe.")
for chunk in doc.chunks:
    print(chunk.text)
import asyncio
async def main():
    doc = await pipe.arun(texts="Chonkie runs fast!")
    print(len(doc.chunks))
asyncio.run(main())
