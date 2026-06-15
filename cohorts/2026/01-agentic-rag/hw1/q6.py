from dotenv import load_dotenv
load_dotenv('/Users/mario/dev/learning/llm-zoomcamp/hw1/.env')

from gitsource import GithubRepositoryDataReader, chunk_documents
import minsearch
from toyaikit.tools import Tools
from toyaikit.llm import OpenAIClient
from toyaikit.chat.runners import OpenAIResponsesRunner

reader = GithubRepositoryDataReader(
    repo_owner='DataTalksClub',
    repo_name='llm-zoomcamp',
    commit_id='8c1834d',
    allowed_extensions={'md'},
    filename_filter=lambda path: '/lessons/' in path,
)
documents = [f.parse() for f in reader.read()]
chunks = chunk_documents(documents, size=2000, step=1000)

index = minsearch.Index(text_fields=['content'], keyword_fields=['filename'])
index.fit(chunks)

search_call_count = 0

def search(query: str) -> list:
    """Search the course lesson pages for relevant content."""
    global search_call_count
    search_call_count += 1
    print(f"  [tool call #{search_call_count}] search('{query[:60]}')")
    results = index.search(query, num_results=3)
    return [{'filename': r['filename'], 'content': r['content'][:500]} for r in results]

tools = Tools()
tools.add_tool(search)
llm_client = OpenAIClient(model='gpt-4.1-mini')

SYSTEM_PROMPT = """You're a course teaching assistant. Answer the student's question using the
search tool. Make multiple searches with different keywords before answering."""

runner = OpenAIResponsesRunner(
    tools=tools,
    developer_prompt=SYSTEM_PROMPT,
    llm_client=llm_client,
)

result = runner.loop("How does the agentic loop work, and how is it different from plain RAG?")

print(f"\nQ6 Answer: search() was called {search_call_count} times")
print(f"\nFinal response:\n{result.output_text[:600]}")
