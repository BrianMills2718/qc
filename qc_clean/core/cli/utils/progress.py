"""
Progress Monitoring Utilities - Progress indicators for CLI operations
"""

import time
import threading
import sys
from typing import Optional


class ProgressIndicator:
    """Simple progress indicator for long-running operations"""
    
    def __init__(self, message: str = "Processing", animation_chars: str = "|/-\\"):
        self.message = message
        self.animation_chars = animation_chars
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.current_char = 0
    
    def start(self) -> None:
        """Start the progress animation"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the progress animation"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
    
    def _animate(self) -> None:
        """Internal animation loop"""
        while self.is_running:
            char = self.animation_chars[self.current_char % len(self.animation_chars)]
            sys.stdout.write(f'\r{char} {self.message}...')
            sys.stdout.flush()
            self.current_char += 1
            time.sleep(0.3)


class SimpleProgressBar:
    """Simple text-based progress bar"""
    
    def __init__(self, total: int, width: int = 40, message: str = "Progress"):
        self.total = total
        self.width = width
        self.message = message
        self.current = 0
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment"""
        self.current = min(self.current + increment, self.total)
        self.display()
    
    def set_progress(self, current: int) -> None:
        """Set absolute progress"""
        self.current = min(max(current, 0), self.total)
        self.display()
    
    def display(self) -> None:
        """Display current progress"""
        if self.total == 0:
            percent = 100
        else:
            percent = int((self.current / self.total) * 100)
        
        filled = int((self.current / self.total) * self.width) if self.total > 0 else 0
        bar = '=' * filled + '-' * (self.width - filled)
        
        sys.stdout.write(f'\r{self.message}: [{bar}] {percent}% ({self.current}/{self.total})')
        sys.stdout.flush()
    
    def finish(self) -> None:
        """Finish progress bar and move to next line"""
        self.set_progress(self.total)
        sys.stdout.write('\n')
        sys.stdout.flush()


def print_status(message: str, status: str = "INFO") -> None:
    """Print a status message with prefix"""
    if status == "SUCCESS":
        prefix = "✅"
    elif status == "ERROR":
        prefix = "❌"
    elif status == "WARNING":
        prefix = "⚠️"
    elif status == "INFO":
        prefix = "ℹ️"
    else:
        prefix = "📝"
    
    print(f"{prefix} {message}")


def print_separator(char: str = "-", length: int = 50) -> None:
    """Print a separator line"""
    print(char * length)