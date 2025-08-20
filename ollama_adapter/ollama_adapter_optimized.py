from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import json
import asyncio
import logging
import os
from typing import Optional, Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ollama Adapter for Llama3", version="2.0.0")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Оптимизированные параметры для MacBook Pro
DEFAULT_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_ctx": 4096,
    "num_predict": 512,
    "num_thread": int(os.getenv("OLLAMA_CPU_THREADS", "8")),
    "num_gpu": int(os.getenv("OLLAMA_GPU_LAYERS", "35")),
    "batch_size": int(os.getenv("OLLAMA_BATCH_SIZE", "512")),
    "rope_freq_base": 10000,
    "rope_freq_scale": 0.5,
}

@app.get("/v1/models")
async def models():
    """List available models"""
    logger.info(f"Attempting to connect to {OLLAMA_URL}/api/tags")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info("Making request to Ollama...")
            response = await client.get(f"{OLLAMA_URL}/api/tags")
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
                        "owned_by": "ollama",
                        "permission": [
                            {
                                "id": "modelperm-1234567890",
                                "object": "model_permission",
                                "created": 1677610602,
                                "allow_create_engine": False,
                                "allow_sampling": True,
                                "allow_logprobs": True,
                                "allow_search_indices": False,
                                "allow_view": True,
                                "allow_fine_tuning": False,
                                "organization": "*",
                                "group": None,
                                "is_blocking": False
                            }
                        ],
                        "root": model["name"],
                        "parent": None
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
                            "id": DEFAULT_MODEL,
                            "object": "model",
                            "created": 1677610602,
                            "owned_by": "ollama",
                            "permission": [
                                {
                                    "id": "modelperm-1234567890",
                                    "object": "model_permission",
                                    "created": 1677610602,
                                    "allow_create_engine": False,
                                    "allow_sampling": True,
                                    "allow_logprobs": True,
                                    "allow_search_indices": False,
                                    "allow_view": True,
                                    "allow_fine_tuning": False,
                                    "organization": "*",
                                    "group": None,
                                    "is_blocking": False
                                }
                            ],
                            "root": DEFAULT_MODEL,
                            "parent": None
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
                    "id": DEFAULT_MODEL,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "ollama",
                    "permission": [
                        {
                            "id": "modelperm-1234567890",
                            "object": "model_permission",
                            "created": 1677610602,
                            "allow_create_engine": False,
                            "allow_sampling": True,
                            "allow_logprobs": True,
                            "allow_search_indices": False,
                            "allow_view": True,
                            "allow_fine_tuning": False,
                            "organization": "*",
                            "group": None,
                            "is_blocking": False
                        }
                    ],
                    "root": DEFAULT_MODEL,
                    "parent": None
                }
            ]
        }

def convert_messages_to_prompt(messages: list) -> str:
    """Convert OpenAI format messages to Ollama prompt format"""
    prompt = ""
    system_message = ""
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "system":
            system_message = content
        elif role == "user":
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "assistant":
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
    
    # Add system message at the beginning if present
    if system_message:
        prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n" + prompt
    
    # Add assistant start token
    prompt += "<|im_start|>assistant\n"
    
    return prompt

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Convert OpenAI chat completion to Ollama format"""
    body = await request.json()
    
    # Extract parameters
    messages = body.get("messages", [])
    model = body.get("model", DEFAULT_MODEL)
    stream = body.get("stream", False)
    temperature = body.get("temperature", DEFAULT_OPTIONS["temperature"])
    max_tokens = body.get("max_tokens", DEFAULT_OPTIONS["num_predict"])
    
    # Convert messages to prompt
    prompt = convert_messages_to_prompt(messages)
    
    # Prepare Ollama request with optimized options
    ollama_request = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            **DEFAULT_OPTIONS,
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }
    
    logger.info(f"Sending request to Ollama: {ollama_request}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return await handle_streaming_response(client, ollama_request)
            else:
                return await handle_non_streaming_response(client, ollama_request)
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "internal_error",
                    "code": 500
                }
            }
        )

async def handle_streaming_response(client: httpx.AsyncClient, ollama_request: Dict[str, Any]):
    """Handle streaming response from Ollama"""
    async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=ollama_request) as response:
        if response.status_code != 200:
            error_text = await response.aread()
            logger.error(f"Ollama streaming error: {error_text}")
            return JSONResponse(
                status_code=response.status_code,
                content={"error": {"message": "Ollama service error", "type": "ollama_error"}}
            )
        
        async def generate():
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("done", False):
                            # Send final chunk
                            yield f"data: {json.dumps({'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                        else:
                            # Send content chunk
                            content = data.get("response", "")
                            yield f"data: {json.dumps({'choices': [{'index': 0, 'delta': {'content': content}}]})}\n\n"
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse line: {line}")
                        continue
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

async def handle_non_streaming_response(client: httpx.AsyncClient, ollama_request: Dict[str, Any]):
    """Handle non-streaming response from Ollama"""
    response = await client.post(f"{OLLAMA_URL}/api/generate", json=ollama_request)
    
    if response.status_code != 200:
        logger.error(f"Ollama error: {response.text}")
        return JSONResponse(
            status_code=response.status_code,
            content={"error": {"message": "Ollama service error", "type": "ollama_error"}}
        )
    
    data = response.json()
    content = data.get("response", "")
    
    return {
        "id": f"chatcmpl-{hash(content) % 1000000}",
        "object": "chat.completion",
        "created": int(asyncio.get_event_loop().time()),
        "model": ollama_request["model"],
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(ollama_request["prompt"].split()),
            "completion_tokens": len(content.split()),
            "total_tokens": len(ollama_request["prompt"].split()) + len(content.split())
        }
    }

@app.post("/v1/completions")
async def completions(request: Request):
    """Handle text completion requests"""
    body = await request.json()
    
    prompt = body.get("prompt", "")
    model = body.get("model", DEFAULT_MODEL)
    max_tokens = body.get("max_tokens", DEFAULT_OPTIONS["num_predict"])
    temperature = body.get("temperature", DEFAULT_OPTIONS["temperature"])
    
    # Convert to chat format for consistency
    messages = [{"role": "user", "content": prompt}]
    
    # Create a new request body for chat completion
    chat_body = {
        "messages": messages,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    # Reuse chat completion logic
    return await chat_completions(Request(scope={"type": "http"}, receive=None))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "ollama": "connected"}
            else:
                return {"status": "degraded", "ollama": "unavailable"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "ollama": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
