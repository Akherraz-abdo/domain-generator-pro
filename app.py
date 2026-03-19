import os
import sys
import logging
from typing import List, Union, Optional
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Initialize Rich Console for beautiful UI
console = Console()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class GeminiPowerBot:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            console.print("[bold red]❌ ERROR: GEMINI_API_KEY not found in environment variables.[/bold red]")
            sys.exit(1)

        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = self._get_latest_model()
            # Start a chat session for persistent memory
            self.chat = self.client.chats.create(
                model=self.model_id,
                config=self._get_default_config()
            )
        except Exception as e:
            console.print(f"[bold red]❌ Failed to initialize Gemini: {e}[/bold red]")
            sys.exit(1)

    def _get_default_config(self):
        """Centralized AI behavior configuration."""
        return types.GenerateContentConfig(
            system_instruction=(
                "You are an elite AI Architect in 2026. You provide concise, "
                "factually accurate, and highly technical responses. Always use "
                "Markdown for formatting. When using Google Search, prioritize "
                "primary sources."
            ),
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.7,
            max_output_tokens=2048,
            safety_settings=[
                types.SafetySetting(category="HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
                types.SafetySetting(category="HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
            ]
        )

    def _get_latest_model(self) -> str:
        """Smart model discovery with 2026 priority."""
        try:
            models = [m.name for m in self.client.models.list() if 'generateContent' in m.supported_methods]
            # 2026 flagship models
            priority = ["gemini-3.1-pro", "gemini-3.0-pro", "gemini-2.5-flash"]
            
            for p in priority:
                for m in models:
                    if p in m:
                        selected = m.split('/')[-1]
                        console.print(f"[bold green]✨ Engine Online:[/bold green] {selected}")
                        return selected
            return models[0].split('/')[-1]
        except Exception:
            return "gemini-2.5-flash"

    def ask(self, prompt: str, file_path: Optional[str] = None):
        """
        Powerful Query Method: Handles Text, Files (Images/PDFs), and Search.
        """
        content_parts = [prompt]

        # FEATURE: Handle Multimodality (Images/Documents)
        if file_path and os.path.exists(file_path):
            try:
                console.print(f"[yellow]📂 Processing file: {file_path}...[/yellow]")
                uploaded_file = self.client.files.upload(path=file_path)
                content_parts.append(uploaded_file)
            except Exception as e:
                console.print(f"[red]⚠️ File upload failed: {e}[/red]")

        try:
            # Using self.chat.send_message instead of generate_content to keep memory
            response = self.chat.send_message(content_parts)
            
            # Display Markdown Response
            console.print(Panel(Markdown(response.text), title="Gemini AI Response", border_style="blue"))

            # Enhanced Grounding Visualization
            if response.candidates[0].grounding_metadata:
                self._display_grounding(response.candidates[0].grounding_metadata)
                
        except Exception as e:
            console.print(f"[bold red]❌ API Error:[/bold red] {e}")

    def _display_grounding(self, metadata):
        """Extracts and prints citations from Google Search."""
        console.print("\n[bold cyan]🌐 Sources Used:[/bold cyan]")
        if metadata.search_entry_point:
            # In 2026 SDKs, this often contains a rendered HTML or snippet
            console.print("  • Verified via Google Search Engine")
        
        # Pull specific links if available in the 2026 schema
        if hasattr(metadata, 'grounding_chunks'):
            for i, chunk in enumerate(metadata.grounding_chunks):
                if chunk.web:
                    console.print(f"  [{i+1}] {chunk.web.title}: {chunk.web.uri}")

    def interactive_shell(self):
        """Turns the script into a powerful CLI tool."""
        console.print("[bold magenta]Gemini Power-Shell Active. Type 'exit' to quit.[/bold magenta]")
        while True:
            try:
                user_input = console.input("[bold green]➜ [/bold green]")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                # Check for file attachments (syntax: prompt @path/to/image.jpg)
                file_path = None
                if "@" in user_input:
                    user_input, file_path = user_input.split("@")
                    user_input = user_input.strip()
                    file_path = file_path.strip()

                self.ask(user_input, file_path)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    bot = GeminiPowerBot()
    
    # If arguments are passed, run once; otherwise, enter interactive mode
    if len(sys.argv) > 1:
        bot.ask(" ".join(sys.argv[1:]))
    else:
        bot.interactive_shell()
