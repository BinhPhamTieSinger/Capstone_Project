import os
import shutil
import logging
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env variables
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH, override=True)

# Debug: Check keys
if os.getenv("GEMINI_API_KEY"):
    logger.info("GEMINI_API_KEY found. Mapping to GOOGLE_API_KEY for LangChain.")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
else:
    logger.error("GEMINI_API_KEY NOT FOUND! Check your .env file.")

if os.getenv("PINECONE_API_KEY"):
    logger.info("PINECONE_API_KEY found.")
else:
    logger.error("PINECONE_API_KEY NOT FOUND! Check your .env file.")

from .models import ChatRequest, ChatResponse, UploadResponse
from .agent import agent_app
from .rag import rag_manager
from langchain_core.messages import HumanMessage

app = FastAPI(title="Capstone AI Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for chat history
memory = {}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Save file locally
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Determine file type and process
        if file.filename.lower().endswith('.pdf'):
            num_chunks = rag_manager.process_pdf(file_path)
        elif file.filename.lower().endswith('.txt'):
            num_chunks = rag_manager.process_text(file_path)
        elif file.filename.lower().endswith('.docx'):
            num_chunks = rag_manager.process_docx(file_path)
        else:
            os.remove(file_path)
            return JSONResponse(status_code=400, content={"message": "Unsupported file type"})

        os.remove(file_path)
        return UploadResponse(
            filename=file.filename,
            status="success",
            info=f"File processed successfully. Added {num_chunks} chunks to knowledge base."
        )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Processing chat message: {request.message}")
    try:
        # LangGraph with MemorySaver handles history automatically based on thread_id.
        # We only need to pass the NEW message.
        
        result = agent_app.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.thread_id}}
        )
        
        # Get last message from the result
        # result["messages"] contains the full history from the graph state
        if result and "messages" in result and result["messages"]:
            # Check if any ToolMessage has chart data in the CURRENT turn
            from langchain_core.messages import ToolMessage
            chart_json = ""
            for m in reversed(result["messages"]):
                if isinstance(m, HumanMessage):
                    break # Stop if we reach the start of the interaction
                if isinstance(m, ToolMessage):
                    if '"type":' in m.content and '"datasets":' in m.content:
                        chart_json = m.content
                        break
            
            last_msg = result["messages"][-1]
            content = last_msg.content
            
            # If we found chart data but it's not in the final message, append it
            if chart_json and chart_json not in content:
                content += f"\n\n```json\n{chart_json}\n```"

            pass
        else:
            content = "Error: No response from agent."

        # Check for content type
        if isinstance(content, list):
            content = "".join([str(c) for c in content])
        
        return ChatResponse(response=str(content))
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}")
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice")
async def voice_recognition():
    """
    Captures audio from the server's microphone and transcribes it using Google Speech Recognition.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return {"error": "Missing libraries. Please install SpeechRecognition and pyaudio: pip install SpeechRecognition pyaudio"}

    r = sr.Recognizer()
    
    try:
        # Use simple printing to console for server feedback
        print("--- Voice Input Started: Listening... ---")
        
        with sr.Microphone() as source:
            # Short adjustment for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.5)
            # Listen with a timeout to avoid hanging forever
            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                print("--- Voice Input: Timeout (No speech detected) ---")
                return {"text": "", "error": "No speech detected (Timeout)."}

        print("--- Audio captured, processing... ---")
        text = r.recognize_google(audio)
        print(f"--- Recognized: {text} ---")
        return {"text": text}
        
    except sr.UnknownValueError:
        return {"text": "", "error": "Could not understand audio."}
    except sr.RequestError as e:
        return {"text": "", "error": f"Speech service error: {e}"}
    except Exception as e:
        # Handle cases where Microphone is not available (e.g. server has no mic)
        logger.error(f"Voice Error: {str(e)}")
        return {"text": "", "error": f"Microphone error: {str(e)}. Ensure the server has a microphone connected."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
