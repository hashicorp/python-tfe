"""LogReader implementation for streaming TFE plan/apply logs."""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from .models.plan import PlanStatus


class LogReader:
    """
    LogReader implements io.Reader for streaming logs.
    
    This class exactly mirrors the Go LogReader implementation:
    - Implements Read() method that works with bytes (like io.Reader)
    - Handles context cancellation with select-like behavior
    - STX/ETX control character handling at byte level
    - Exponential backoff with exact same algorithm as Go
    - Proper HTTP error handling via checkResponseCode equivalent

    Usage:
        # For streaming logs byte by byte (like Go's io.Reader)
        log_reader = LogReader(transport, log_url, done_func, context)
        buffer = bytearray(4096)
        while True:
            n, err = await log_reader.read(buffer)
            if n > 0:
                print(buffer[:n].decode('utf-8', errors='ignore'), end='')
            if err:
                break

        # For reading all logs at once
        all_logs = await log_reader.read_all()
    """

    def __init__(
        self,
        transport: Any,
        log_url: str,
        done_func: Callable[[], tuple[bool, Exception | None]],
        context: Any = None,
    ) -> None:
        """
        Initialize LogReader.

        Args:
            transport: HTTP transport for internal requests
            log_url: URL to fetch logs from
            done_func: Function that returns (done, error) tuple
            context: Optional context for cancellation
        """
        self.transport = transport
        self.done_func = done_func
        self.context = context

        # State tracking (exactly like Go implementation)
        self.offset = 0
        self.reads = 0
        self.start_of_text = False
        self.end_of_text = False

        # Parse URL for validation (like Go url.Parse)
        self.parsed_url = urlparse(log_url)
        if not self.parsed_url.scheme or not self.parsed_url.netloc:
            raise ValueError(f"Invalid log URL: {log_url}")

    async def read(self, buffer: bytearray | bytes) -> tuple[int, Exception | None]:
        """
        Read data into the provided buffer (io.Reader equivalent).
        
        This method exactly mirrors the Go LogReader.Read() behavior:
        - Returns (bytes_read, error) tuple like Go
        - Handles context cancellation with select-like behavior
        - Implements exponential backoff
        - Processes STX/ETX control characters at byte level
        
        Args:
            buffer: Buffer to read data into
            
        Returns:
            Tuple of (bytes_read, error). Returns (0, EOFError) when done,
            (0, NoProgressError) for no progress, or (n, None) for n bytes read.
        """
        # First attempt to read (like Go: if written, err := r.read(l))
        written, err = await self._read(buffer)
        if err is not None and not isinstance(err, NoProgressError):
            return written, err

        # Loop until we get data, context is cancelled, or run is finished
        # This exactly mirrors the Go implementation's for loop
        self.reads = 1
        while True:
            try:
                # Context cancellation check (equivalent to Go's select case <-r.ctx.Done())
                if self.context and hasattr(self.context, 'cancelled') and self.context.cancelled():
                    return 0, self.context.exception()

                # Wait with backoff (equivalent to Go's case <-time.After(backoff(...)))
                await asyncio.sleep(self._backoff(500, 2000, self.reads) / 1000.0)

                written, err = await self._read(buffer)
                if err is not None and not isinstance(err, NoProgressError):
                    return written, err

                self.reads += 1
            except asyncio.CancelledError as e:
                return 0, e

    async def _read(self, buffer: bytearray | bytes) -> tuple[int, Exception | None]:
        """
        Internal read method that handles HTTP requests and data processing.
        
        This method exactly mirrors the Go LogReader.read() method.
        
        Args:
            buffer: Buffer to read data into
            
        Returns:
            Tuple of (bytes_read, error)
        """
        # Update the query string (exactly like Go: r.logURL.RawQuery = fmt.Sprintf(...))
        url_parts = list(self.parsed_url)
        query = f"limit={len(buffer)}&offset={self.offset}"
        url_parts[4] = query  # query component
        chunk_url = urlunparse(url_parts)

        try:
            # Create a new request (like Go: req, err := http.NewRequest("GET", ...))
            # Use the transport to make the request (like Go client.http.HTTPClient.Do)
            response = await self.transport.arequest("GET", chunk_url)
            
            # Read the response body as bytes (like Go: written, err := resp.Body.Read(l))
            chunk_data = response.content
            
        except Exception as e:
            return 0, e

        if not chunk_data:
            return 0, NoProgressError()

        written = len(chunk_data)

        # Handle STX/ETX control characters at byte level (exactly like Go)
        if written > 0:
            # Check for STX (Start of Text) ASCII control marker
            if not self.start_of_text and chunk_data[0] == 2:
                self.start_of_text = True

                # Remove the STX marker from the received chunk (like Go copy operation)
                chunk_data = chunk_data[1:]
                self.offset += 1
                written -= 1

                # Return early if we only received the STX marker
                if written == 0:
                    return 0, NoProgressError()

            # If we found an STX ASCII control character, start looking for ETX
            if self.start_of_text and chunk_data[-1] == 3:
                self.end_of_text = True

                # Remove the ETX marker from the received chunk
                chunk_data = chunk_data[:-1]
                self.offset += 1
                written -= 1

        # Copy data to buffer
        if written > 0:
            buffer[:written] = chunk_data[:written]

        # Check if we need to continue the loop (exactly like Go logic)
        if written != 0:
            # Update the offset for the next read
            self.offset += written
            return written, None

        # Check completion conditions (exactly like Go implementation)
        if (
            (self.start_of_text and self.end_of_text) or  # The logstream finished without issues
            (self.start_of_text and self.reads % 10 == 0) or  # The logstream terminated unexpectedly
            (not self.start_of_text and self.reads > 1)  # The logstream doesn't support STX/ETX
        ):
            # Check if operation is done (like Go: done, err := r.done())
            try:
                done, err = self.done_func()
                if err:
                    return 0, err
                if done:
                    return 0, EOFError("End of log stream")
            except Exception as e:
                return 0, e

        return 0, NoProgressError()

    async def read_all(self, chunk_size: int = 4096) -> str:
        """
        Read all available logs as a single string.
        
        Args:
            chunk_size: Size of each chunk to read
            
        Returns:
            Complete log content as string
        """
        buffer = bytearray(chunk_size)
        result = bytearray()
        
        while True:
            n, err = await self.read(buffer)
            if n > 0:
                result.extend(buffer[:n])
            if err:
                if isinstance(err, EOFError):
                    break
                raise err
                
        return result.decode('utf-8', errors='ignore')

    def _backoff(self, minimum: float, maximum: float, iter: int) -> float:
        """
        Calculate exponential backoff duration (exactly like Go implementation).
        
        Args:
            minimum: Minimum backoff in milliseconds
            maximum: Maximum backoff in milliseconds
            iter: Current iteration number
            
        Returns:
            Backoff duration in milliseconds
        """
        backoff = math.pow(2, iter / 5) * minimum
        if backoff > maximum:
            backoff = maximum
        return backoff


class NoProgressError(Exception):
    """Error indicating no progress was made (equivalent to Go's io.ErrNoProgress)."""
    pass