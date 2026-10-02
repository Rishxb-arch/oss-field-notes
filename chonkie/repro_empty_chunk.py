# Repro: TokenChunker(tokenizer="gpt2") silently emits empty chunks and shifts all later offsets
# when a token window boundary falls inside a multi-byte UTF-8 character (e.g. box-drawing "│").
import chonkie
from chonkie import TokenChunker
from chonkie.tokenizer import AutoTokenizer
tk = AutoTokenizer("gpt2")
ids = tk.encode("a│b")                      # "│" is two gpt2 byte tokens: [6552, 224]
print("chonkie", chonkie.__version__, "| ids:", ids, "| decode(ids[:2]) =", repr(tk.decode(ids[:2])), "(expected 'a' or 'a\\ufffd')")
text = "│ cactus run [model]   run a model │\n" * 40
ch = TokenChunker(tokenizer="gpt2", chunk_size=7, chunk_overlap=0)
cs = ch.chunk(text)
empty = [i for i, c in enumerate(cs) if c.text == ""]
covered = "".join(c.text for c in cs)
print(f"{len(cs)} chunks, {len(empty)} empty (token_count still {cs[empty[0]].token_count if empty else '-'}), "
      f"joined chunk text = {len(covered)} chars vs original {len(text)} chars")
bad = sum(text[c.start_index:c.end_index] != c.text for c in cs)
print("chunks where text[start:end] != chunk.text:", bad)
