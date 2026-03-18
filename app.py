import os
import sys
from google import genai
from google.genai import types

class GeminiBot:
    def __init__(self):
        # SECURITY: Get API key from GitHub Secrets / Environment Variables
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            print("❌ ERROR: GEMINI_API_KEY not found. Please set it in GitHub Secrets.")
            sys.exit(1)
            
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = self._get_latest_model()
        except Exception as e:
            print(f"❌ Failed to initialize Gemini Client: {e}")
            sys.exit(1)

    def _get_latest_model(self):
        """
        FEATURE: Auto-Correction. 
        Lists available models and picks the best one to avoid 404 errors.
        """
        print("🔍 Scanning for available models...")
        try:
            # Get all models that support generating content
            available_models = [
                m.name for m in self.client.models.list() 
                if 'generateContent' in m.supported_methods
            ]
            
            # Priority list for 2026 (Newest to Oldest)
            priority = ["gemini-3.1", "gemini-3.0", "gemini-2.5"]
            
            for version in priority:
                for model_path in available_models:
                    if version in model_path:
                        # Strip 'models/' prefix if present
                        selected = model_path.split('/')[-1]
                        print(f"✅ Selected Model: {selected}")
                        return selected
            
            # Absolute fallback if no 2026 models found
            fallback = available_models[0].split('/')[-1]
            return fallback
        except Exception as e:
            print(f"⚠️ Could not list models: {e}. Falling back to gemini-2.5-flash.")
            return "gemini-2.5-flash"

    def ask(self, prompt):
        """
        FEATURE: Generate content with System Instructions and Live Web Grounding.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # FEATURE: System Instructions (Gives the AI a persona)
                    system_instruction="You are a helpful assistant running in a 2026 production environment.",
                    
                    # FEATURE: Google Search Grounding (Live facts from the web)
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            print("\n--- AI Response ---")
            print(response.text)
            
            # Show if the AI used Google Search to verify info
            if response.candidates[0].grounding_metadata:
                print("\n🌐 [Fact-checked with Google Search]")
                
        except Exception as e:
            print(f"❌ API Call Failed: {e}")

if __name__ == "__main__":
    bot = GeminiBot()
    
    # Example usage
    user_input = "What is the current state of AI in March 2026?"
    bot.ask(user_input)
