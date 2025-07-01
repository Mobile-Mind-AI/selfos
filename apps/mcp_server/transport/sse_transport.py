"""
Server-Sent Events Transport for MCP

Implements SSE transport for the Model Context Protocol,
enabling communication with web clients and browser-based applications.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Set
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import uuid

logger = logging.getLogger(__name__)


class SSETransport:
    """Server-Sent Events transport implementation for MCP."""
    
    def __init__(self, server):
        """Initialize SSE transport with MCP server."""
        self.server = server
        self.running = False
        self.connections: Dict[str, asyncio.Queue] = {}
        self.app = FastAPI()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up SSE routes."""
        
        @self.app.get("/mcp/sse")
        async def sse_endpoint(request: Request):
            """SSE endpoint for MCP communication."""
            connection_id = str(uuid.uuid4())
            logger.info(f"New SSE connection: {connection_id}")
            
            # Create message queue for this connection
            message_queue = asyncio.Queue()
            self.connections[connection_id] = message_queue
            
            try:
                return StreamingResponse(
                    self._sse_generator(connection_id, message_queue),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Cache-Control"
                    }
                )
            except Exception as e:
                logger.error(f"SSE connection error: {e}")
                # Clean up connection
                self.connections.pop(connection_id, None)
                raise HTTPException(status_code=500, detail="SSE connection failed")
        
        @self.app.post("/mcp/sse/{connection_id}/message")
        async def send_message(connection_id: str, message: dict):
            """Receive messages from client via POST."""
            if connection_id not in self.connections:
                raise HTTPException(status_code=404, detail="Connection not found")
            
            try:
                # Process the message
                response = await self._process_message(message)
                
                # Send response back via SSE
                if response:
                    await self.connections[connection_id].put({
                        "type": "response",
                        "data": response
                    })
                
                return {"status": "message_processed"}
                
            except Exception as e:
                logger.error(f"Error processing SSE message: {e}")
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get('id'),
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
                await self.connections[connection_id].put({
                    "type": "error",
                    "data": error_response
                })
                raise HTTPException(status_code=500, detail="Message processing failed")
    
    async def start(self):
        """Start the SSE transport."""
        logger.info("Starting MCP SSE transport")
        self.running = True
        
        # In a real implementation, this would start the FastAPI server
        # For now, we just mark as running
        logger.info("SSE transport ready (routes configured)")
    
    async def stop(self):
        """Stop the SSE transport."""
        logger.info("Stopping MCP SSE transport")
        self.running = False
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            await self._close_connection(connection_id)
    
    async def _sse_generator(self, connection_id: str, message_queue: asyncio.Queue):
        """Generate SSE events for a connection."""
        try:
            # Send initial connection event
            yield f"event: connected\\ndata: {{\"connection_id\": \"{connection_id}\"}}\\n\\n"
            
            while self.running and connection_id in self.connections:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                    
                    # Send message as SSE event
                    event_type = message.get("type", "message")
                    event_data = json.dumps(message.get("data", {}))
                    yield f"event: {event_type}\\ndata: {event_data}\\n\\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"event: keepalive\\ndata: {{\"timestamp\": \"{asyncio.get_event_loop().time()}\"}}\\n\\n"
                
                except Exception as e:
                    logger.error(f"Error in SSE generator: {e}")
                    break
        
        except Exception as e:
            logger.error(f"SSE generator error: {e}")
        
        finally:
            # Clean up connection
            await self._close_connection(connection_id)
    
    async def _close_connection(self, connection_id: str):
        """Close and clean up a connection."""
        if connection_id in self.connections:
            logger.info(f"Closing SSE connection: {connection_id}")
            del self.connections[connection_id]
    
    async def _process_message(self, message: dict) -> Optional[dict]:
        """Process an incoming JSON-RPC message."""
        try:
            method = message.get('method')
            params = message.get('params', {})
            message_id = message.get('id')
            
            # Handle different MCP methods
            if method == 'initialize':
                result = await self._handle_initialize(params)
            elif method == 'tools/list':
                result = await self._handle_list_tools(params)
            elif method == 'tools/call':
                result = await self._handle_call_tool(params)
            elif method == 'resources/list':
                result = await self._handle_list_resources(params)
            elif method == 'resources/read':
                result = await self._handle_read_resource(params)
            elif method == 'prompts/list':
                result = await self._handle_list_prompts(params)
            elif method == 'prompts/get':
                result = await self._handle_get_prompt(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Return success response
            if message_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing SSE message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get('id'),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialization request."""
        return {
            "protocolVersion": "1.0.0",
            "serverInfo": {
                "name": "selfos-mcp-server",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            }
        }
    
    async def _handle_list_tools(self, params: dict) -> dict:
        """Handle tools/list request."""
        tools = await self.server.list_tools()
        return {"tools": [tool.dict() for tool in tools]}
    
    async def _handle_call_tool(self, params: dict) -> dict:
        """Handle tools/call request."""
        name = params.get('name')
        arguments = params.get('arguments', {})
        
        result = await self.server.call_tool(name, arguments)
        return {"content": [content.dict() for content in result]}
    
    async def _handle_list_resources(self, params: dict) -> dict:
        """Handle resources/list request."""
        resources = await self.server.list_resources()
        return {"resources": [resource.dict() for resource in resources]}
    
    async def _handle_read_resource(self, params: dict) -> dict:
        """Handle resources/read request."""
        uri = params.get('uri')
        content = await self.server.read_resource(uri)
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": content
            }]
        }
    
    async def _handle_list_prompts(self, params: dict) -> dict:
        """Handle prompts/list request."""
        prompts = await self.server.list_prompts()
        return {"prompts": [prompt.dict() for prompt in prompts]}
    
    async def _handle_get_prompt(self, params: dict) -> dict:
        """Handle prompts/get request."""
        name = params.get('name')
        arguments = params.get('arguments', {})
        
        content = await self.server.get_prompt(name, arguments)
        return {
            "description": f"Prompt: {name}",
            "messages": [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": content
                }
            }]
        }
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app for integration."""
        return self.app
    
    def get_connection_count(self) -> int:
        """Get current number of active connections."""
        return len(self.connections)