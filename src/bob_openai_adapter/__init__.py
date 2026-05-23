"""
Bob OpenAI Adapter

This module provides a lightweight OpenAI-style chat-completions interface
for Bob Shell. It is intended for simple integrations that use
``client.chat.completions.create(...)`` and plain text chat messages.

The adapter accepts some OpenAI-style parameters for caller compatibility;
unsupported parameters are logged and ignored.
"""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import time
from typing import Any, Dict, Iterator, List, Literal, Optional, Union

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


class BobError(Exception):
    """Base exception for Bob adapter errors."""
    pass


class BobAPIError(BobError):
    """Exception raised when Bob API call fails."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BobTimeoutError(BobError):
    """Exception raised when Bob call times out."""
    pass


class BobConnectionError(BobError):
    """Exception raised when connection to Bob fails."""
    pass


class TransportConfig:
    """Configuration for transport layer (retry, timeout, etc.)."""
    
    def __init__(
        self,
        timeout: float = 300.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        max_retry_delay: float = 60.0,
        cwd: Optional[str] = None,
    ):
        """
        Initialize transport configuration.
        
        Args:
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            retry_backoff: Backoff multiplier for retry delay (default: 2.0)
            max_retry_delay: Maximum retry delay in seconds (default: 60.0)
            cwd: Working directory for the Bob subprocess
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.max_retry_delay = max_retry_delay


class Message:
    """Represents a chat message."""
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class Choice:
    """Represents a completion choice."""
    
    def __init__(self, message: Message, finish_reason: str = "stop", index: int = 0):
        self.message = message
        self.finish_reason = finish_reason
        self.index = index
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "message": self.message.to_dict(),
            "finish_reason": self.finish_reason,
        }


class Usage:
    """Represents token usage information."""
    
    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class ChatCompletion:
    """Represents a chat completion response."""
    
    def __init__(
        self,
        id: str,
        choices: List[Choice],
        created: int,
        model: str,
        usage: Optional[Usage] = None,
    ):
        self.id = id
        self.object = "chat.completion"
        self.created = created
        self.model = model
        self.choices = choices
        self.usage = usage or Usage()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [choice.to_dict() for choice in self.choices],
            "usage": self.usage.to_dict(),
        }

    def model_dump(self) -> Dict[str, Any]:
        """Return a dictionary representation, matching common SDK usage."""
        return self.to_dict()

    def to_json(self) -> str:
        """Return a JSON representation of the response."""
        return json.dumps(self.to_dict())


class DeltaChoice:
    """Represents a streaming delta choice."""

    def __init__(self, delta: Dict[str, Any], finish_reason: Optional[str] = None, index: int = 0):
        self.index = index
        self.delta = delta
        self.finish_reason = finish_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "delta": self.delta,
            "finish_reason": self.finish_reason,
        }


class ChatCompletionChunk:
    """Represents a streaming chat completion chunk."""
    
    def __init__(
        self,
        id: str,
        delta: Dict[str, Any],
        created: int,
        model: str,
        finish_reason: Optional[str] = None,
        index: int = 0,
    ):
        self.id = id
        self.object = "chat.completion.chunk"
        self.created = created
        self.model = model
        self.choices = [DeltaChoice(delta=delta, finish_reason=finish_reason, index=index)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [choice.to_dict() for choice in self.choices],
        }


class BobExecutor:
    """Handles execution of Bob commands with retry logic."""
    
    def __init__(
        self,
        command: str = "bob",
        transport_config: Optional[TransportConfig] = None,
        cwd: Optional[str] = None,
    ):
        self.command = command
        self.transport_config = transport_config or TransportConfig()
        self.cwd = cwd
    
    def _build_command(
        self,
        chat_mode: Optional[str] = None,
        model: Optional[str] = None,
        output_format: str = "text",
        approval_mode: str = "yolo",
        extra_args: Optional[List[str]] = None,
    ) -> List[str]:
        """Build the Bob command with arguments."""
        cmd = [self.command]
        
        # Add approval mode
        cmd.extend(["--approval-mode", approval_mode])
        
        # Add chat mode if specified
        if chat_mode:
            cmd.extend(["--chat-mode", chat_mode])
        
        # Add model if specified
        if model:
            cmd.extend(["-m", model])
        
        # Add output format
        cmd.extend(["-o", output_format])
        
        # Add any extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        return cmd
    
    def _execute_with_retry(
        self,
        cmd: List[str],
        prompt: str,
    ) -> str:
        """Execute command with retry logic."""
        last_exception = None
        retry_delay = self.transport_config.retry_delay
        
        for attempt in range(self.transport_config.max_retries + 1):
            try:
                logger.debug(
                    "Executing Bob command (attempt %d/%d): %s",
                    attempt + 1,
                    self.transport_config.max_retries + 1,
                    " ".join(shlex.quote(part) for part in cmd),
                )
                
                proc = subprocess.run(
                    cmd,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=self.transport_config.timeout,
                    env=os.environ.copy(),
                    cwd=self.cwd,
                    check=False,
                )
                
                stdout = (proc.stdout or "").strip()
                stderr = (proc.stderr or "").strip()
                
                if proc.returncode != 0:
                    detail = stderr or stdout or "<no output>"
                    if len(detail) > 2000:
                        detail = detail[:2000] + "..."
                    raise BobAPIError(
                        f"Bob exited with code {proc.returncode}: {detail}",
                        status_code=proc.returncode,
                    )
                
                if not stdout:
                    detail = stderr or "<no stderr>"
                    raise BobAPIError(f"Bob returned empty output. stderr: {detail}")
                
                return stdout
                
            except FileNotFoundError as exc:
                raise BobConnectionError(
                    f"Bob executable not found: {self.command!r}. "
                    "Make sure Bob is installed and available on PATH."
                ) from exc
            
            except subprocess.TimeoutExpired as exc:
                last_exception = BobTimeoutError(
                    f"Bob timed out after {self.transport_config.timeout} second(s)."
                )
                logger.warning("Bob timeout on attempt %d: %s", attempt + 1, last_exception)
            
            except BobAPIError as exc:
                last_exception = exc
                logger.warning("Bob API error on attempt %d: %s", attempt + 1, exc)
            
            except Exception as exc:
                last_exception = BobError(f"Failed to execute Bob: {exc}")
                logger.warning("Bob execution error on attempt %d: %s", attempt + 1, exc)
            
            # Don't retry if this was the last attempt
            if attempt < self.transport_config.max_retries:
                logger.info("Retrying in %.2f seconds...", retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * self.transport_config.retry_backoff,
                    self.transport_config.max_retry_delay,
                )
        
        # All retries exhausted
        raise last_exception or BobError("Unknown error during Bob execution")
    
    def execute(
        self,
        prompt: str,
        chat_mode: Optional[str] = None,
        model: Optional[str] = None,
        output_format: str = "text",
        approval_mode: str = "yolo",
        extra_args: Optional[List[str]] = None,
    ) -> str:
        """Execute Bob command and return output."""
        cmd = self._build_command(
            chat_mode=chat_mode,
            model=model,
            output_format=output_format,
            approval_mode=approval_mode,
            extra_args=extra_args,
        )
        return self._execute_with_retry(cmd, prompt)


class Completions:
    """Chat completions endpoint."""
    
    def __init__(self, executor: BobExecutor):
        self.executor = executor
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI messages format to a single prompt for Bob."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)
    
    def create(
        self,
        messages: List[Dict[str, str]],
        model: str = "bob",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        chat_mode: Optional[str] = None,
        approval_mode: str = "yolo",
        # Accept but ignore unsupported OpenAI parameters
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """
        Create a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (default: "bob")
            temperature: Sampling temperature (accepted but not used by Bob)
            max_tokens: Maximum tokens to generate (accepted but not used by Bob)
            stream: Whether to stream the response (default: False)
            chat_mode: Bob chat mode ('plan', 'code', 'advanced', 'ask')
            approval_mode: Bob approval mode ('default', 'auto_edit', 'yolo')
            extra_args: Additional Bob CLI arguments to append to the command
            **kwargs: Other OpenAI parameters (accepted but ignored)
        
        Returns:
            ChatCompletion object or iterator of ChatCompletionChunk objects
        """
        # Log ignored parameters
        ignored_params = []
        if temperature is not None:
            ignored_params.append(f"temperature={temperature}")
        if max_tokens is not None:
            ignored_params.append(f"max_tokens={max_tokens}")
        if top_p is not None:
            ignored_params.append(f"top_p={top_p}")
        if n is not None:
            ignored_params.append(f"n={n}")
        if stop is not None:
            ignored_params.append(f"stop={stop}")
        if presence_penalty is not None:
            ignored_params.append(f"presence_penalty={presence_penalty}")
        if frequency_penalty is not None:
            ignored_params.append(f"frequency_penalty={frequency_penalty}")
        if logit_bias is not None:
            ignored_params.append(f"logit_bias={logit_bias}")
        if user is not None:
            ignored_params.append(f"user={user}")
        
        if ignored_params:
            logger.info(
                "The following OpenAI parameters are not supported by Bob and will be ignored: %s",
                ", ".join(ignored_params),
            )
        
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)
        
        # Handle streaming
        if stream:
            return self._create_stream(prompt, model, chat_mode, approval_mode, extra_args=extra_args)
        
        # Execute Bob command
        output = self.executor.execute(
            prompt=prompt,
            chat_mode=chat_mode,
            model=model if model != "bob" else None,
            output_format="text",
            approval_mode=approval_mode,
            extra_args=extra_args,
        )
        
        # Create response
        completion_id = f"chatcmpl-{int(time.time() * 1000)}"
        created = int(time.time())
        
        message = Message(role="assistant", content=output)
        choice = Choice(message=message, finish_reason="stop", index=0)
        
        # Estimate token usage (rough approximation)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(output.split())
        usage = Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        
        return ChatCompletion(
            id=completion_id,
            choices=[choice],
            created=created,
            model=model,
            usage=usage,
        )
    
    def _create_stream(
        self,
        prompt: str,
        model: str,
        chat_mode: Optional[str],
        approval_mode: str,
        extra_args: Optional[List[str]] = None,
    ) -> Iterator[ChatCompletionChunk]:
        """Create a streaming chat completion."""
        # Execute Bob command with stream-json output
        output = self.executor.execute(
            prompt=prompt,
            chat_mode=chat_mode,
            model=model if model != "bob" else None,
            output_format="stream-json",
            approval_mode=approval_mode,
            extra_args=extra_args,
        )
        
        completion_id = f"chatcmpl-{int(time.time() * 1000)}"
        created = int(time.time())
        
        # Parse stream-json output and yield chunks
        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                content = data.get("content", "")
                
                if content:
                    delta = {"role": "assistant", "content": content}
                    yield ChatCompletionChunk(
                        id=completion_id,
                        delta=delta,
                        created=created,
                        model=model,
                        index=0,
                    )
            except json.JSONDecodeError:
                # If not JSON, treat as plain text chunk
                if line:
                    delta = {"role": "assistant", "content": line}
                    yield ChatCompletionChunk(
                        id=completion_id,
                        delta=delta,
                        created=created,
                        model=model,
                        index=0,
                    )
        
        # Send final chunk with finish_reason
        yield ChatCompletionChunk(
            id=completion_id,
            delta={},
            created=created,
            model=model,
            finish_reason="stop",
            index=0,
        )


class Chat:
    """Chat endpoint."""
    
    def __init__(self, executor: BobExecutor):
        self.completions = Completions(executor)


class BobOpenAI:
    """
    OpenAI-style client for Bob Shell.

    This client supports a practical subset of the OpenAI chat-completions
    interface for plain text calls to Bob Shell.
    
    Example:
        client = BobOpenAI(api_key=os.getenv("BOBSHELL_API_KEY"))
        response = client.chat.completions.create(
            model="bob",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )
        print(response.choices[0].message.content)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        bob_command: str = "bob",
        timeout: float = 300.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        max_retry_delay: float = 60.0,
        cwd: Optional[str] = None,
    ):
        """
        Initialize Bob OpenAI client.
        
        Args:
            api_key: API key value accepted for caller compatibility
            bob_command: Path to Bob executable (default: "bob")
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
            retry_backoff: Backoff multiplier for retry delay (default: 2.0)
            max_retry_delay: Maximum retry delay in seconds (default: 60.0)
            cwd: Working directory for the Bob subprocess
        """
        # API key is accepted for compatibility but not used by Bob
        self.api_key = api_key or os.getenv("BOBSHELL_API_KEY")
        
        # Create transport configuration
        transport_config = TransportConfig(
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            retry_backoff=retry_backoff,
            max_retry_delay=max_retry_delay,
        )
        
        # Create executor
        executor = BobExecutor(command=bob_command, transport_config=transport_config, cwd=cwd)
        
        # Create chat endpoint
        self.chat = Chat(executor)
