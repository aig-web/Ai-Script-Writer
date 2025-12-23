"""
Centralized Logging for ScriptAI Pro
Provides consistent, timestamped logging across all modules
"""
import os
import sys
from datetime import datetime
from typing import Optional, Any
import json
import traceback

# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


# Log levels
LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_ERROR = 3

# Current log level (can be set via environment)
CURRENT_LOG_LEVEL = int(os.getenv("LOG_LEVEL", LOG_LEVEL_INFO))


def _get_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def _format_data(data: Any, max_length: int = 200) -> str:
    """Format data for logging, truncating if needed"""
    if data is None:
        return "None"

    if isinstance(data, dict):
        try:
            text = json.dumps(data, default=str)
        except:
            text = str(data)
    elif isinstance(data, (list, tuple)):
        text = str(data)
    else:
        text = str(data)

    if len(text) > max_length:
        return text[:max_length] + f"... ({len(text)} chars)"
    return text


class Logger:
    """Centralized logger for ScriptAI modules"""

    def __init__(self, module_name: str, emoji: str = ""):
        self.module = module_name
        self.emoji = emoji
        self.request_id: Optional[str] = None

    def set_request_id(self, request_id: str):
        """Set a request ID for tracking across async operations"""
        self.request_id = request_id

    def _log(self, level: str, color: str, message: str, data: Any = None):
        """Internal logging method"""
        timestamp = _get_timestamp()
        prefix = f"{self.emoji} " if self.emoji else ""
        req_id = f"[{self.request_id[:8]}] " if self.request_id else ""

        # Build log line
        log_line = f"{Colors.GRAY}{timestamp}{Colors.RESET} {color}[{level}]{Colors.RESET} {prefix}{Colors.BOLD}[{self.module}]{Colors.RESET} {req_id}{message}"

        if data is not None:
            formatted_data = _format_data(data)
            log_line += f" {Colors.CYAN}| {formatted_data}{Colors.RESET}"

        # Handle Windows console encoding issues with emojis
        try:
            print(log_line, file=sys.stderr if level in ["ERROR", "WARN"] else sys.stdout)
        except UnicodeEncodeError:
            # Fallback: remove emojis and try again
            safe_line = log_line.encode('ascii', 'ignore').decode('ascii')
            print(safe_line, file=sys.stderr if level in ["ERROR", "WARN"] else sys.stdout)

    def debug(self, message: str, data: Any = None):
        """Debug level log"""
        if CURRENT_LOG_LEVEL <= LOG_LEVEL_DEBUG:
            self._log("DEBUG", Colors.GRAY, message, data)

    def info(self, message: str, data: Any = None):
        """Info level log"""
        if CURRENT_LOG_LEVEL <= LOG_LEVEL_INFO:
            self._log("INFO", Colors.BLUE, message, data)

    def success(self, message: str, data: Any = None):
        """Success log (info level with green color)"""
        if CURRENT_LOG_LEVEL <= LOG_LEVEL_INFO:
            self._log("OK", Colors.GREEN, f"✓ {message}", data)

    def warn(self, message: str, data: Any = None):
        """Warning level log"""
        if CURRENT_LOG_LEVEL <= LOG_LEVEL_WARN:
            self._log("WARN", Colors.YELLOW, f"⚠ {message}", data)

    def error(self, message: str, data: Any = None, exc: Exception = None):
        """Error level log"""
        if CURRENT_LOG_LEVEL <= LOG_LEVEL_ERROR:
            self._log("ERROR", Colors.RED, f"✗ {message}", data)
            if exc:
                # Print traceback for debugging
                tb = traceback.format_exc()
                print(f"{Colors.RED}{tb}{Colors.RESET}", file=sys.stderr)

    def start(self, operation: str, data: Any = None):
        """Log start of an operation"""
        self.info(f"Starting: {operation}", data)

    def end(self, operation: str, duration_ms: float = None, data: Any = None):
        """Log end of an operation"""
        if duration_ms:
            self.success(f"Completed: {operation} ({duration_ms:.0f}ms)", data)
        else:
            self.success(f"Completed: {operation}", data)

    def step(self, step_name: str, data: Any = None):
        """Log a step in a multi-step process"""
        self._log("STEP", Colors.MAGENTA, f"→ {step_name}", data)

    def api_request(self, method: str, path: str, data: Any = None):
        """Log API request"""
        self.info(f"{method} {path}", data)

    def api_response(self, status: int, path: str, duration_ms: float = None):
        """Log API response"""
        color = Colors.GREEN if status < 400 else Colors.RED
        duration = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        self._log("RESP", color, f"{status} {path}{duration}")

    def llm_call(self, model: str, purpose: str, tokens: int = None):
        """Log LLM API call"""
        token_info = f" ({tokens} tokens)" if tokens else ""
        self.info(f"LLM Call: {purpose} → {model}{token_info}")

    def llm_response(self, model: str, duration_ms: float, output_preview: str = None):
        """Log LLM response"""
        preview = f" | Output: {output_preview[:100]}..." if output_preview and len(output_preview) > 100 else (f" | Output: {output_preview}" if output_preview else "")
        self.success(f"LLM Response: {model} ({duration_ms:.0f}ms){preview}")

    def db_query(self, operation: str, table: str, data: Any = None):
        """Log database operation"""
        self.debug(f"DB {operation}: {table}", data)

    def db_result(self, operation: str, table: str, count: int = None):
        """Log database result"""
        count_info = f" ({count} rows)" if count is not None else ""
        self.debug(f"DB {operation} OK: {table}{count_info}")


# Pre-configured loggers for each module
def get_logger(module_name: str, emoji: str = "") -> Logger:
    """Get a logger instance for a module"""
    return Logger(module_name, emoji)


# Common module loggers (convenience)
server_log = Logger("Server", "🚀")
session_log = Logger("Session", "💾")
research_log = Logger("Research", "🔍")
writer_log = Logger("Writer", "✍️")
critic_log = Logger("Critic", "👀")
checker_log = Logger("Checker", "✅")
chat_log = Logger("Chat", "💬")
graph_log = Logger("Graph", "🔄")
rag_log = Logger("RAG", "📚")
