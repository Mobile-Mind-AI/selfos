"""
Standard I/O Transport for MCP

Implements stdio transport for the Model Context Protocol,
enabling communication with local AI agents and CLI tools.
"""

import asyncio
import sys
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StdioTransport:
    """Standard I/O transport implementation for MCP."""
    
    def __init__(self, server):
        """Initialize stdio transport with MCP server."""
        self.server = server
        self.running = False
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def start(self):
        """Start the stdio transport."""
        logger.info("Starting MCP stdio transport")
        self.running = True
        
        try:
            # Create stdin/stdout streams
            self.reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self.reader)
            
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            self.writer = asyncio.StreamWriter(
                sys.stdout, 
                protocol, 
                self.reader, 
                loop
            )
            
            # Start message processing loop
            await self._message_loop()
            
        except Exception as e:
            logger.error(f"Error in stdio transport: {e}")
            raise
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the stdio transport."""
        logger.info("Stopping MCP stdio transport")
        self.running = False
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
    
    async def _message_loop(self):
        """Main message processing loop."""
        while self.running:
            try:
                # Read message from stdin
                message = await self._read_message()
                if not message:
                    break
                
                # Process message
                response = await self._process_message(message)
                
                # Send response to stdout
                if response:
                    await self._send_message(response)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
                await self._send_message(error_response)
    
    async def _read_message(self) -> Optional[dict]:
        """Read a JSON-RPC message from stdin."""
        try:
            # Read Content-Length header
            content_length = None
            while True:
                line = await self.reader.readline()
                if not line:
                    return None
                
                line = line.decode('utf-8').strip()
                if not line:
                    break
                
                if line.startswith('Content-Length: '):
                    content_length = int(line[16:])
            
            if content_length is None:
                logger.warning("No Content-Length header found")
                return None
            
            # Read message body
            body = await self.reader.read(content_length)
            if not body:
                return None
            
            # Parse JSON
            message = json.loads(body.decode('utf-8'))
            logger.debug(f"Received message: {message.get('method', 'unknown')}")
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None
    
    async def _send_message(self, message: dict):
        """Send a JSON-RPC message to stdout."""
        try:
            # Serialize message
            body = json.dumps(message, separators=(',', ':'))
            body_bytes = body.encode('utf-8')
            
            # Write Content-Length header and body
            self.writer.write(f'Content-Length: {len(body_bytes)}\\r\\n\\r\\n'.encode('utf-8'))
            self.writer.write(body_bytes)
            await self.writer.drain()
            
            logger.debug(f"Sent message: {message.get('method', message.get('result', 'response'))}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
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
            logger.error(f"Error processing message: {e}")
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
                "tools": {
                    "listChanged": True
                },
                "resources": {
                    "subscribe": True,
                    "listChanged": True
                },
                "prompts": {
                    "listChanged": True
                }
            }
        }
    
    async def _handle_list_tools(self, params: dict) -> dict:
        """Handle tools/list request."""
        # This would call the actual server method
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