import os
import sys
import asyncio
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")

# Force API key usage and avoid ADC conflicts
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

# Add current directory to path
sys.path.append(os.getcwd())

async def run_tests():
    print("=== STARTING TOOL VERIFICATION ===\n")
    
    # 1. Test Calculator (SymPy)
    try:
        from backend.tools import calculator
        print("[TEST] Calculator (Symbolic): solve(x**2 + 2*x - 3, x)")
        res = calculator.invoke("solve(x**2 + 2*x - 3, x)")
        print(f"   Result: {res}")
        if "Solution:" in res or "[-3, 1]" in res:
            print("   [PASS]")
        else:
            print("   [FAIL] Content mismatch")
    except Exception as e:
        print(f"   [FAIL] Exception: {e}")

    # 2. Test Web Search (Language Check)
    try:
        from backend.tools import search_web
        print("\n[TEST] Web Search: 'Gradient Descent'")
        res = search_web.invoke("Gradient Descent")
        print(f"   Result Snippet: {res[:300]}...")
        
        # Simple heuristic for Chinese characters
        if any(u'\u4e00' <= c <= u'\u9fff' for c in res):
            print("   [FAIL] Detected Chinese characters. Region setting likely needed.")
        else:
            print("   [PASS] No obvious Chinese characters detected.")
    except Exception as e:
        from duckduckgo_search import DDGS
        print(f"   [FAIL] Exception: {e}")

    # 3. Test Visualization Demo (JSON Format)
    try:
        from backend.tools import visualization_demo
        print("\n[TEST] Visualization Demo")
        res = visualization_demo.invoke({})
        print(f"   Result: {res}")
        if res.strip().startswith("{") and "datasets" in res:
            print("   [PASS] Valid JSON format.")
        else:
            print("   [FAIL] Not valid JSON start.")
    except Exception as e:
        print(f"   [FAIL] Exception: {e}")

    # 4. Test URL Fetcher (Specific Google Support Link)
    try:
        from backend.tools import url_fetcher
        print("\n[TEST] URL Fetcher: Google Support Link")
        url = "https://support.google.com/websearch/answer/1696588?sjid=4251503761237645311-NC"
        res = url_fetcher.invoke(url)
        print(f"   Result Snippet: {res[:300]}...")
        if "SafeSearch" in res or "Filter explicit results" in res:
             print("   [PASS] Content seems relevant.")
        else:
             print("   [WARN] Content might not be fully extracted or different than expected.")
    except Exception as e:
        print(f"   [FAIL] Exception: {e}")
        
    # 5. Test NLP Tools
    try:
        from backend.tools import translator, sentiment_analyzer, text_summarizer
        
        # Translate
        print("\n[TEST] Translator: 'Hello world' -> Spanish")
        res = translator.invoke({"text": "Hello world", "target_language": "Spanish"})
        print(f"   Result: {res}")
        if "Hola" in res:
             print("   [PASS]")
             
        # Sentiment
        print("\n[TEST] Sentiment Analyzer: 'I love this project!'")
        res = sentiment_analyzer.invoke("I love this project!")
        print(f"   Result: {res}")
        if "Positive" in str(res): # Returns NamedTuple or string
             print("   [PASS]")

        # Summarizer
        print("\n[TEST] Text Summarizer")
        long_text = "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals."
        res = text_summarizer.invoke(long_text)
        print(f"   Result: {res}")
        if len(str(res)) < len(long_text):
             print("   [PASS]")
             
    except Exception as e:
        print(f"   [FAIL] Exception: {e}")

    # 6. Test RAG Pipeline (File Processing & Retrieval)
    # Note: We will use the 'test' directory found.
    try:
        from backend.rag import rag_manager
        test_dir = os.path.join(os.getcwd(), "test")
        
        files = {
            "pdf": "chu de 7 trang 136-150 ÁP SUẤT VÀ ĐỘNG NĂNG PHÂN TỬ CHẤT KHÍ -HS - QUỐC BÌNH.pdf",
            "docx": "PM2.5_Project.docx",
            "txt": "neural_network_explanation.txt"
        }
        
        # Queries mapping
        queries = {
            "pdf": "problem 7.1 to 7.3 are listed in the document chu de 7 trang 136-150 ÁP SUẤT VÀ ĐỘNG NĂNG PHÂN TỬ CHẤT KHÍ -HS - QUỐC BÌNH.pdf",
            "docx": "main method and summarize the document PM2.5_Project.docx",
            "txt": "steps in Backward Pass neural_network_explanation.txt"
        }
        
        print("\n[TEST] RAG Pipeline (Processing & Search)")
        
        for file_type, filename in files.items():
            path = os.path.join(test_dir, filename)
            if not os.path.exists(path):
                print(f"   [WARN] File not found: {path}")
                continue
                
            print(f"   Processing {file_type.upper()}: {filename}...")
            try:
                # Call appropriate process method
                if file_type == "pdf":
                    rag_manager.process_pdf(path)
                elif file_type == "docx":
                    rag_manager.process_docx(path)
                elif file_type == "txt":
                    rag_manager.process_text(path)
                    
                print(f"   [PASS] Processed {filename}")
                
                # Test Search
                q = queries[file_type]
                print(f"      Searching: '{q}'")
                results = rag_manager.search(q, k=2)
                if results:
                    print(f"      [PASS] Found {len(results)} relevant chunks.")
                    print(f"      Snippet: {results[0].page_content[:100]}...")
                else:
                    print(f"      [FAIL] No results found for query.")
                    
            except Exception as e:
                print(f"   [FAIL] Error processing {filename}: {e}")

    except Exception as e:
        print(f"   [FAIL] RAG Exception: {e}")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
