from pathlib import Path
from datetime import datetime
from typing_extensions import Annotated, List, Literal
from langchain.chat_models import init_chat_model 
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from schema import tavily_client,llm,Summary
from prompts.prompt_ricerca_tavily import summarize_webpage_gameReview, summarize_webpage_gameGuide

def process_search_results(results: dict, topic: str) -> dict:
    all_contents = []

    for item in results["results"]:
        url = item["url"]
        title = item["title"]
        content = item.get("raw_content") or item.get("content", "")
        all_contents.append(f"""URL: {url}\nTitle: {title}\nContent: {content}\n""")

    combined_content = "\n\n".join(all_contents)
    summarized_results = summarize_webpage_content(combined_content, topic=topic)

    return summarized_results

def summarize_webpage_content(webpage_content: str,topic:str) -> str:
    """Summarize webpage content using the configured summarization model.
    Args:
        webpage_content: Raw webpage content to summarize

    Returns:
        Formatted summary with key excerpts
    """
    try:
        if(topic=="video games review"):
            summarize_prompt = summarize_webpage_gameReview
        elif(topic=="video games guide"):
            summarize_prompt = summarize_webpage_gameGuide

        summary = llm.invoke([
            HumanMessage(content=summarize_prompt.format(
                webpage_content=webpage_content,))
        ])
        formatted_summary = f"<summary>\n{summary.content}\n</summary>\n\n"
        return formatted_summary
    except Exception as e:
        print(f"Failed to summarize webpage: {str(e)}")
        return webpage_content[:1000] + "..." if len(webpage_content) > 1000 else webpage_content


@tool
def tavily_search(query:str, topic:Literal["video games review","video games guide"],)->str:
    """Fetch results from Tavily search API with content summarization.
    Args:
        query: A single search query to execute
        max_results: Maximum number of results to return
        topic: Topic to filter results by ('video games review', 'video games guide')

    Returns:
        Formatted string of search results with summaries
    """

    result=tavily_client.search(query,max_results=3, max_content_length=5000, )
    summarized_results = process_search_results(result,topic=topic)
    # Format output for consumption
    return summarized_results

