"""
LLM Zoomcamp 2026 - Homework 1: Agentic RAG
https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw1
"""

from dotenv import load_dotenv
load_dotenv()

from gitsource import GithubRepositoryDataReader, chunk_documents
import minsearch
from openai import OpenAI
from rag_helper import RAGBase, INSTRUCTIONS, PROMPT_TEMPLATE

QUERY = 'How does the agentic loop keep calling the model until it stops?'

# --- Fetch documents ---
reader = GithubRepositoryDataReader(
    repo_owner='DataTalksClub',
    repo_name='llm-zoomcamp',
    commit_id='8c1834d',
    allowed_extensions={'md'},
    filename_filter=lambda path: '/lessons/' in path,
)
documents = [f.parse() for f in reader.read()]

# Q1 - How many lesson pages
print(f"Q1: {len(documents)} lesson pages")

# Q2 - Index and search
index = minsearch.Index(text_fields=['content'], keyword_fields=['filename'])
index.fit(documents)
results = index.search(QUERY)
print(f"Q2: {results[0]['filename']}")


# Q3 / Q5 - RAG helper adapted for filename/content schema
class RAG(RAGBase):
    def search(self, query, num_results=5):
        return self.index.search(query, num_results=num_results)

    def build_context(self, search_results):
        lines = []
        for doc in search_results:
            lines.append(f'File: {doc["filename"]}')
            lines.append(doc['content'])
            lines.append('')
        return '\n'.join(lines).strip()

    def llm(self, prompt):
        input_messages = [
            {'role': 'developer', 'content': self.instructions},
            {'role': 'user', 'content': prompt}
        ]
        response = self.llm_client.responses.create(model=self.model, input=input_messages)
        return response.output_text, response.usage.input_tokens

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer, tokens = self.llm(prompt)
        return answer, tokens


client = OpenAI()

# Q3 - RAG with full documents, count input tokens
rag = RAG(index=index, llm_client=client)
_, q3_tokens = rag.rag(QUERY)
print(f"Q3: {q3_tokens} input tokens")

# Q4 - Chunk documents
chunks = chunk_documents(documents, size=2000, step=1000)
print(f"Q4: {len(chunks)} chunks")

# Q5 - RAG with chunked index, compare tokens
chunk_index = minsearch.Index(text_fields=['content'], keyword_fields=['filename'])
chunk_index.fit(chunks)
rag_chunked = RAG(index=chunk_index, llm_client=client)
_, q5_tokens = rag_chunked.rag(QUERY)
print(f"Q5: {q3_tokens} → {q5_tokens} tokens ({q3_tokens/q5_tokens:.1f}x fewer)")
