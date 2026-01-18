import os
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
import json
import random

from .rag import rag_manager

# Initialize generic LLM for tool-internal tasks if needed
llm_fast = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0, google_api_key=os.environ.get("GEMINI_API_KEY"))

@tool
def search_documents(query: str) -> str:
    """Search uploaded PDF documents for relevant information.
    
    Use this tool when:
    - User asks about content from uploaded documents.
    - User mentions 'the PDF', 'the document', or 'the file'.
    
    Args:
        query: The search query to find relevant passages.
    """
    try:
        docs = rag_manager.search(query)
        if not docs:
            return "No relevant information found in the documents."
        
        results = []
        for i, doc in enumerate(docs, 1):
            results.append(f"[Passage {i}]: {doc.page_content[:500]}...")
        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching documents: {str(e)}"

@tool
def calculator(expression: str) -> str:
    """Calculate the result of a mathematical expression or solve equations.
    
    Args:
        expression: The mathematical expression (e.g., '2 + 2', 'sin(pi/2)') or equation to solve (e.g., 'solve(x**2 + 2*x - 3, x)').
    """
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
        
        transformations = (standard_transformations + (implicit_multiplication_application,))
        
        # global_dict needs to include things solve might emit, like Integer, Float, etc.
        # We can just use sympy's global context + solve/Symbol
        global_context = {
            "solve": sympy.solve, 
            "Symbol": sympy.Symbol,
            "Integer": sympy.Integer,
            "Float": sympy.Float,
            "Rational": sympy.Rational,
            "sqrt": sympy.sqrt,
            "sin": sympy.sin,
            "cos": sympy.cos,
            "tan": sympy.tan,
            "pi": sympy.pi,
            "E": sympy.E
        }
        
        # Check if it's a solve request
        if "solve" in expression.lower():
            if "=" in expression and "solve" not in expression:
                 parts = expression.split("=")
                 lhs = parse_expr(parts[0], transformations=transformations)
                 rhs = parse_expr(parts[1], transformations=transformations)
                 eq = sympy.Eq(lhs, rhs)
                 result = sympy.solve(eq)
                 return f"Solution: {result}"
            
            expr = parse_expr(expression, transformations=transformations, global_dict=global_context)
            return str(expr)
        else:
            expr = parse_expr(expression, transformations=transformations, global_dict=global_context)
            return str(expr.evalf())
    except Exception as e:
        return f"Error calculating: {str(e)}"
    
@tool
def word_counter(text: str) -> str:
    """Count the number of words in a text.
    
    Args:
        text: The text to count words for.
    """
    count = len(text.split())
    return f"Word count: {count}"

@tool
def text_summarizer(text: str) -> str:
    """Summarize a text.
    
    Args:
        text: The text to summarize.
    """
    try:
        prompt = ChatPromptTemplate.from_template("Summarize the following text concisely:\n\n{text}")
        chain = prompt | llm_fast
        res = chain.invoke({"text": text})
        return res.content
    except Exception as e:
        return f"Error summarizing text: {str(e)}"

@tool
def sentiment_analyzer(text: str) -> str:
    """Analyze the sentiment of a text.
    
    Args:
        text: The text to analyze.
    """
    try:
        blob = TextBlob(text)
        return blob.sentiment
    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"

@tool
def url_fetcher(url: str) -> str:
    """Fetch the content of a URL.
    
    Args:
        url: The URL to fetch.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # Use BeautifulSoup to extract text and remove HTML tags to save tokens
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Kill all script and style elements
            for script in soup(["script", "style"]):
                script.extract()    # rip it out
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate to avoid hitting Gemini token limits (429 errors)
            max_chars = 5000
            if len(text) > max_chars:
                return text[:max_chars] + f"\n\n... [Content Truncated due to size limit. Original length: {len(text)} chars]"
            return text
            
        return f"Error: Status code {response.status_code}"
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

@tool
def translator(text: str, target_language: str) -> str:
    """Translate text to a target language.
    
    Args:
        text: The text to translate.
        target_language: The language to translate to (e.g., 'Spanish', 'French', 'Japanese').
    """
    prompt = ChatPromptTemplate.from_template("Translate the following text to {language}:\n\n{text}")
    chain = prompt | llm_fast
    res = chain.invoke({"language": target_language, "text": text})
    return res.content

@tool
def generate_chart(data_description: str) -> str:
    """Generate a chart visualization based on a description of data.
    
    Use this tool when the user wants to see a graph, chart, or plot.
    This tool returns a JSON string representing the chart data.
    
    Args:
        data_description: Description of the data and chart type (e.g., 'Bar chart of sales: Jan 10, Feb 20, Mar 15').
    """
    prompt = ChatPromptTemplate.from_template("""
    Create a JSON object for a chart based on this description: {description}
    
    The JSON must follow this exact schema:
    {{
        "type": "bar" | "line" | "pie",
        "title": "Chart Title",
        "labels": ["Label1", "Label2", ...],
        "datasets": [
            {{
                "label": "Dataset Label",
                "data": [10, 20, ...]
            }}
        ]
    }}
    
    Return ONLY the raw JSON string, no markdown formatting.
    """)
    chain = prompt | llm_fast
    res = chain.invoke({"description": data_description})
    return res.content.strip().strip('`').replace('json', '')

@tool
def search_web(query: str) -> str:
    """Search the web for information using DuckDuckGo.
    
    Use this tool when you need to find information outside your knowledge base or uploaded documents.
    Pass the search query directly.
    """
    try:
        # Fallback to manual scraping since the library is unstable in this env
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = "https://html.duckduckgo.com/html/"
        params = {'q': query}
        
        response = requests.post(url, data=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Search failed with status code: {response.status_code}"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='result'):
            title_tag = result.find('a', class_='result__a')
            snippet_tag = result.find('a', class_='result__snippet')
            
            if title_tag and snippet_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                snippet = snippet_tag.get_text(strip=True)
                
                # Filter Chinese characters
                if any(u'\u4e00' <= c <= u'\u9fff' for c in snippet):
                    continue
                    
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}")
                if len(results) >= 5:
                    break
        
        if not results:
            return "No English results found."
            
        return "\n\n".join(results)

    except Exception as e:
        return f"Error searching web: {str(e)}"

@tool
def visualization_demo() -> str:
    """Returns a sample chart JSON to demonstrate visualization capabilities.
    
    Use this when the user asks for a 'demo' or 'example' of data visualization.
    """
    return """{
        "type": "line",
        "title": "Quarterly Revenue Growth",
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [
            {
                "label": "Revenue (M$)",
                "data": [12, 19, 15, 25]
            }
        ]
    }"""

@tool
def read_document_intro(num_chars: int = 2000) -> str:
    """Read the beginning of the most recently uploaded document directly.
    
    Use this when:
    - The user asks to 'read the first sentence' or 'introduction'.
    - RAG search fails to find specific text that should be at the start.
    
    Args:
        num_chars: Number of characters to read (default 2000).
    """
    try:
        # Since files are processed and not saved persistently on disk in this demo,
        # we can't read the raw file back. We must rely on RAG.
        # However, to be helpful, we can instruct the user.
        return "Note: The system currently processes files into a vector database for semantic search and does not persist the original file on disk for sequential reading. Use 'search_documents' to find specific topics."
    except Exception as e:
        return str(e)
