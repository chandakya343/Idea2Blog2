from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
import uvicorn
import os
from mangum import Adapter

from idea2draft2 import ThoughtProcessor
from Draft2Blog import Draft2Blog, BlogConfig

# Load API key from environment variable
API_KEY = os.environ.get("GEMINI_API_KEY") 

class IdeaRequest(BaseModel):
    idea: str

class RefinementRequest(BaseModel):
    refinement: str

class Orchestrator:
    def __init__(self):
        self.thought_processor = ThoughtProcessor(API_KEY)
        self.blog_converter = Draft2Blog(API_KEY)
        self.current_state = None

    def process_initial_idea(self, idea: str) -> Dict:
        result = self.thought_processor.process_brain_dump(idea)
        self.current_state = result
        return result

    def refine_content(self, refinement: str) -> Dict:
        result = self.thought_processor.refine_narrative(refinement)
        self.current_state = result
        return result

    def finalize_to_blog(self) -> str:
        if not self.current_state:
            raise ValueError("No content to finalize")
        return self.blog_converter.convert_draft(self.current_state["connected_narrative"])

app = FastAPI(title="Idea@Blog")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
handler = Adapter(app)  # For AWS Lambda compatibility if needed
orchestrator = Orchestrator()

@app.get("/health")
async def health_check():
    """Health check endpoint for Render.com"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Idea to Blog Pipeline</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
        <style>
            .hidden { display: none; }
            .fade-in { animation: fadeIn 0.5s; }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            
            .spinner {
                width: 24px;
                height: 24px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-left: 8px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Markdown Styles */
            .markdown-content h1 { font-size: 2em; font-weight: bold; margin: 1em 0; }
            .markdown-content h2 { font-size: 1.5em; font-weight: bold; margin: 0.83em 0; }
            .markdown-content h3 { font-size: 1.17em; font-weight: bold; margin: 1em 0; }
            .markdown-content ul { list-style-type: disc; margin: 1em 0; padding-left: 2em; }
            .markdown-content ol { list-style-type: decimal; margin: 1em 0; padding-left: 2em; }
            .markdown-content code { background-color: #f0f0f0; padding: 0.2em 0.4em; border-radius: 3px; }
            .markdown-content pre { background-color: #f6f8fa; padding: 1em; border-radius: 6px; overflow-x: auto; }
            .markdown-content blockquote { border-left: 4px solid #ddd; margin: 1em 0; padding-left: 1em; color: #666; }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <!-- Initial Input View -->
        <div id="initial-view" class="max-w-4xl mx-auto p-8">
            <h1 class="text-3xl font-bold mb-8">Idea to Blog Pipeline</h1>
            <div class="bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">Share Your Idea</h2>
                <textarea id="initial-idea" placeholder="Enter your brain dump here..." 
                    class="w-full p-4 border rounded mb-4 h-48 focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                <button id="process-btn" onclick="processIdea()" 
                    class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">
                    Process
                </button>
            </div>
        </div>

        <!-- Processing Result View -->
        <div id="result-view" class="max-w-4xl mx-auto p-8 hidden">
            <h1 class="text-3xl font-bold mb-8">Analysis Results</h1>
            
            <div class="mb-8 bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">Connected Narrative</h2>
                <div id="connected-narrative" class="prose max-w-none markdown-content"></div>
            </div>

            <div class="mb-8 bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">Growth Points</h2>
                <div id="growth-points" class="prose max-w-none markdown-content"></div>
            </div>

            <div class="mb-8 bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">AI Contributions</h2>
                <div id="ai-contributions" class="prose max-w-none markdown-content"></div>
            </div>

            <div class="flex gap-4 mb-8">
                <div class="flex-grow">
                    <textarea id="refinement-input" placeholder="Enter refinement request..." 
                        class="w-full p-4 border rounded mb-2 h-24 focus:outline-none focus:ring-2 focus:ring-purple-500"></textarea>
                    <button id="refine-btn" onclick="refineContent()" 
                        class="bg-purple-500 text-white px-6 py-2 rounded hover:bg-purple-600">
                        Refine
                    </button>
                </div>
                <div class="flex items-end">
                    <button id="finalize-btn" onclick="finalizeToBlog()" 
                        class="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 h-12">
                        Finalize to Blog
                    </button>
                </div>
            </div>
        </div>

        <!-- Blog View -->
        <div id="blog-view" class="max-w-4xl mx-auto p-8 hidden">
            <h1 class="text-3xl font-bold mb-8">Final Blog Post</h1>
            <div class="bg-white p-6 rounded-lg shadow">
                <div id="blog-content" class="prose max-w-none markdown-content"></div>
            </div>
            <button onclick="startNew()" 
                class="mt-8 bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">
                Start New
            </button>
        </div>

        <script>
            marked.setOptions({
                breaks: true,
                gfm: true,
                headerIds: true
            });

            function showLoadingState(buttonId) {
                const button = document.getElementById(buttonId);
                const originalText = button.textContent;
                button.disabled = true;
                button.innerHTML = originalText + '<div class="spinner"></div>';
                return () => {
                    button.disabled = false;
                    button.textContent = originalText;
                };
            }

            function showView(viewId) {
                ['initial-view', 'result-view', 'blog-view'].forEach(id => {
                    document.getElementById(id).classList.add('hidden');
                });
                document.getElementById(viewId).classList.remove('hidden');
                document.getElementById(viewId).classList.add('fade-in');
            }

            async function processIdea() {
                const resetLoading = showLoadingState('process-btn');
                const idea = document.getElementById('initial-idea').value;
                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ idea: idea })
                    });
                    const data = await response.json();
                    
                    document.getElementById('connected-narrative').innerHTML = marked.parse(data.connected_narrative);
                    document.getElementById('growth-points').innerHTML = marked.parse(data.growth_points);
                    document.getElementById('ai-contributions').innerHTML = marked.parse(data.ai_contributions);
                    
                    showView('result-view');
                } catch (error) {
                    alert('Error processing idea: ' + error.message);
                } finally {
                    resetLoading();
                }
            }

            async function refineContent() {
                const resetLoading = showLoadingState('refine-btn');
                const refinement = document.getElementById('refinement-input').value;
                try {
                    const response = await fetch('/refine', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refinement: refinement })
                    });
                    const data = await response.json();
                    
                    document.getElementById('connected-narrative').innerHTML = marked.parse(data.connected_narrative);
                    document.getElementById('growth-points').innerHTML = marked.parse(data.growth_points);
                    document.getElementById('ai-contributions').innerHTML = marked.parse(data.ai_contributions);
                    
                    document.getElementById('refinement-input').value = '';
                } catch (error) {
                    alert('Error refining content: ' + error.message);
                } finally {
                    resetLoading();
                }
            }

            async function finalizeToBlog() {
                const resetLoading = showLoadingState('finalize-btn');
                try {
                    const response = await fetch('/finalize', { method: 'POST' });
                    const data = await response.json();
                    
                    document.getElementById('blog-content').innerHTML = marked.parse(data.blog_post);
                    showView('blog-view');
                } catch (error) {
                    alert('Error finalizing blog: ' + error.message);
                } finally {
                    resetLoading();
                }
            }

            function startNew() {
                document.getElementById('initial-idea').value = '';
                document.getElementById('refinement-input').value = '';
                showView('initial-view');
            }
        </script>
    </body>
    </html>
    """

@app.post("/process")
async def process_idea(request: IdeaRequest):
    try:
        result = orchestrator.process_initial_idea(request.idea)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refine")
async def refine_content(request: RefinementRequest):
    try:
        result = orchestrator.refine_content(request.refinement)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize")
async def finalize_to_blog():
    try:
        blog_post = orchestrator.finalize_to_blog()
        return {"blog_post": blog_post}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 10000))
    
    # Configure uvicorn with necessary settings for Render.com
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",  # Required for Render.com
        port=port,
        log_level="info",
        proxy_headers=True,  # Important for proper header handling behind proxy
        forwarded_allow_ips="*",  # Allow forwarded IPs from Render's proxy
    )
    
    # Create and run server
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    main()