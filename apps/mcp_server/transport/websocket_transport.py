"""
WebSocket Transport for MCP

Implements WebSocket transport for the Model Context Protocol,
enabling real-time bidirectional communication with clients.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uuid

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.authenticated = False
        self.user_id: Optional[str] = None
        self.client_info: Dict = {}
    
    async def send_message(self, message: dict):
        """Send a message to the client."""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            raise
    
    async def receive_message(self) -> Optional[dict]:
        """Receive a message from the client."""
        try:
            data = await self.websocket.receive_text()
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving WebSocket message: {e}")
            raise


class WebSocketTransport:
    """WebSocket transport implementation for MCP."""
    
    def __init__(self, server):
        """Initialize WebSocket transport with MCP server."""
        self.server = server
        self.running = False
        self.connections: Dict[str, WebSocketConnection] = {}
        self.app = FastAPI()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up WebSocket routes."""
        
        @self.app.websocket("/mcp/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for MCP communication."""
            connection_id = str(uuid.uuid4())
            logger.info(f"New WebSocket connection: {connection_id}")
            
            await websocket.accept()
            
            connection = WebSocketConnection(websocket, connection_id)
            self.connections[connection_id] = connection
            
            try:
                # Send welcome message
                await connection.send_message({
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {
                        "connection_id": connection_id,
                        "server_info": {
                            "name": "selfos-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                })
                
                # Handle messages
                await self._handle_connection(connection)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
            finally:
                # Clean up connection
                self.connections.pop(connection_id, None)
                logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def start(self):
        """Start the WebSocket transport."""
        logger.info("Starting MCP WebSocket transport")
        self.running = True
        
        # In a real implementation, this would start the FastAPI server
        # For now, we just mark as running
        logger.info("WebSocket transport ready (routes configured)")
    
    async def stop(self):
        """Stop the WebSocket transport."""
        logger.info("Stopping MCP WebSocket transport")
        self.running = False
        
        # Close all connections
        for connection_id in list(self.connections.keys()):
            await self._close_connection(connection_id)
    
    async def _handle_connection(self, connection: WebSocketConnection):
        """Handle messages for a WebSocket connection."""
        while self.running:
            try:
                # Receive message from client
                message = await connection.receive_message()
                if not message:
                    continue
                
                # Process message
                response = await self._process_message(connection, message)
                
                # Send response if there is one
                if response:
                    await connection.send_message(response)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": message.get('id') if 'message' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
                try:
                    await connection.send_message(error_response)
                except:
                    break
    
    async def _close_connection(self, connection_id: str):
        """Close and clean up a connection."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            try:
                await connection.websocket.close()
            except:
                pass
            del self.connections[connection_id]
            logger.info(f"Closed WebSocket connection: {connection_id}")
    
    async def _process_message(self, connection: WebSocketConnection, message: dict) -> Optional[dict]:
        """Process an incoming JSON-RPC message."""
        try:
            method = message.get('method')
            params = message.get('params', {})
            message_id = message.get('id')
            
            # Handle different MCP methods
            if method == 'initialize':
                result = await self._handle_initialize(connection, params)
            elif method == 'tools/list':
                result = await self._handle_list_tools(connection, params)
            elif method == 'tools/call':
                result = await self._handle_call_tool(connection, params)
            elif method == 'resources/list':
                result = await self._handle_list_resources(connection, params)
            elif method == 'resources/read':
                result = await self._handle_read_resource(connection, params)
            elif method == 'prompts/list':
                result = await self._handle_list_prompts(connection, params)
            elif method == 'prompts/get':
                result = await self._handle_get_prompt(connection, params)
            elif method == 'notifications/cancelled':
                # Handle cancellation notification
                return None
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Return success response for requests (not notifications)
            if message_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get('id'),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _handle_initialize(self, connection: WebSocketConnection, params: dict) -> dict:
        """Handle initialization request."""
        # Store client info
        connection.client_info = params.get('clientInfo', {})
        
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
    
    async def _handle_list_tools(self, connection: WebSocketConnection, params: dict) -> dict:
        """Handle tools/list request."""
        tools = await self.server.list_tools()
        return {"tools": [tool.dict() for tool in tools]}
    
    async def _handle_call_tool(self, connection: WebSocketConnection, params: dict) -> dict:
        """Handle tools/call request."""
        name = params.get('name')
        arguments = params.get('arguments', {})
        
        result = await self.server.call_tool(name, arguments)
        return {"content": [content.dict() for content in result]}
    
    async def _handle_list_resources(self, connection: WebSocketConnection, params: dict) -> dict:
        """Handle resources/list request."""
        resources = await self.server.list_resources()
        return {"resources": [resource.dict() for resource in resources]}
    
    async def _handle_read_resource(self, connection: WebSocketConnection, params: dict) -> dict:
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
    
    async def _handle_list_prompts(self, connection: WebSocketConnection, params: dict) -> dict:
        """Handle prompts/list request."""
        prompts = await self.server.list_prompts()
        return {"prompts": [prompt.dict() for prompt in prompts]}
    
    async def _handle_get_prompt(self, connection: WebSocketConnection, params: dict) -> dict:
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
    
    async def broadcast_notification(self, notification: dict):
        """Broadcast a notification to all connected clients."""
        if not self.connections:
            return
        
        # Send to all connections
        tasks = []
        for connection in self.connections.values():
            try:
                tasks.append(connection.send_message(notification))
            except Exception as e:
                logger.error(f"Error broadcasting to {connection.connection_id}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)