from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import json
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

OLLAMA_URL = "http://ollama:11434"

@app.get("/v1/models")
async def models():
    """List available models"""
    logger.info(f"Attempting to connect to {OLLAMA_URL}/api/tags")
    try:
        async with httpx.AsyncClient() as client:
            logger.info("Making request to Ollama...")
            response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                ollama_models = response.json()
                logger.info(f"Ollama response: {ollama_models}")
                models_data = []
                for model in ollama_models.get("models", []):
                    models_data.append({
                        "id": model["name"],
                        "object": "model",
                        "created": 1677610602,
                        "owned_by": "ollama"
                    })
                logger.info(f"Models data: {models_data}")
                return {
                    "object": "list",
                    "data": models_data
                }
            else:
                logger.error(f"Ollama returned status {response.status_code}")
                # Fallback to default model if Ollama is not available
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": "llama2:7b",
                            "object": "model",
                            "created": 1677610602,
                            "owned_by": "ollama"
                        }
                    ]
                }
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        # Fallback to default model if there's an error
        return {
            "object": "list",
            "data": [
                {
                    "id": "llama2:7b",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "ollama"
                }
            ]
        }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Convert OpenAI chat completion to Ollama format"""
    body = await request.json()
    
    # Extract messages and convert to Ollama format
    messages = body.get("messages", [])
    model = body.get("model", "llama2:7b")
    stream = body.get("stream", False)
    
    # Convert messages to prompt
    prompt = ""
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "system":
            prompt += f"System: {content}\n"
        elif role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    
    prompt += "Assistant: "
    
    # Prepare Ollama request
    ollama_request = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": body.get("temperature", 0.7),
            "top_p": body.get("top_p", 0.9),
            "max_tokens": body.get("max_tokens", 1000)
        }
    }
    
    if stream:
        # Handle streaming
        async def generate():
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=ollama_request) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if data.get("done", False):
                                    # Send final response
                                    final_response = {
                                        "id": "chatcmpl-" + str(hash(prompt)),
                                        "object": "chat.completion.chunk",
                                        "created": 1677610602,
                                        "model": model,
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": {},
                                                "finish_reason": "stop"
                                            }
                                        ]
                                    }
                                    yield f"data: {json.dumps(final_response)}\n\n"
                                    yield "data: [DONE]\n\n"
                                    break
                                else:
                                    # Send content chunk
                                    chunk_response = {
                                        "id": "chatcmpl-" + str(hash(prompt)),
                                        "object": "chat.completion.chunk",
                                        "created": 1677610602,
                                        "model": model,
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": {
                                                    "content": data.get("response", "")
                                                },
                                                "finish_reason": None
                                            }
                                        ]
                                    }
                                    yield f"data: {json.dumps(chunk_response)}\n\n"
                            except json.JSONDecodeError:
                                continue
        return JSONResponse(content=generate(), media_type="text/event-stream")
    else:
        # Handle non-streaming
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=ollama_request)
            data = response.json()
            
            # Convert to OpenAI format
            openai_response = {
                "id": "chatcmpl-" + str(hash(prompt)),
                "object": "chat.completion",
                "created": 1677610602,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": data.get("response", "")
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(data.get("response", "").split()),
                    "total_tokens": len(prompt.split()) + len(data.get("response", "").split())
                }
            }
            return openai_response

@app.post("/v1/completions")
async def completions(request: Request):
    """Convert OpenAI completion to Ollama format"""
    body = await request.json()
    
    prompt = body.get("prompt", "")
    model = body.get("model", "llama2:7b")
    
    ollama_request = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": body.get("temperature", 0.7),
            "top_p": body.get("top_p", 0.9),
            "max_tokens": body.get("max_tokens", 1000)
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{OLLAMA_URL}/api/generate", json=ollama_request)
        data = response.json()
        
        openai_response = {
            "id": "cmpl-" + str(hash(prompt)),
            "object": "text_completion",
            "created": 1677610602,
            "model": model,
            "choices": [
                {
                    "text": data.get("response", ""),
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(data.get("response", "").split()),
                "total_tokens": len(prompt.split()) + len(data.get("response", "").split())
            }
        }
        return openai_response

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
            if response.status_code == 200:
                return {"status": "healthy", "ollama_connected": True}
            else:
                return {"status": "unhealthy", "ollama_connected": False, "error": f"Ollama returned {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "ollama_connected": False, "error": str(e)}
