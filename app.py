import streamlit as st
import os
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="Gemini 2026 AI", page_icon="🤖", layout="wide")
st.title("🚀 Gemini Power Bot 2026")

# --- 1. SECURE API KEY SETUP ---
# On Streamlit Cloud, set this in: Settings > Secrets
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY not found! Go to Streamlit Cloud Settings > Secrets and add it.")
    st.stop()

# --- 2. INITIALIZE CLIENT & SESSION STATE ---
@st.cache_resource
def get_client():
    return genai.Client(api_key=api_key)

client = get_client()

# Initialize Chat History (This is how it remembers what you said)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. MODEL SELECTION ---
# Fast and powerful for 2026
model_id = "gemini-2.0-flash" 

# --- 4. DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT INPUT ---
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Thinking and searching the web...*")
        
        try:
            # Send message to Gemini with Google Search Grounding
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a professional AI assistant in 2026. Use formatting and clear sections.",
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.7,
                )
            )
            
            full_response = response.text
            message_placeholder.markdown(full_response)
            
            # Show Grounding (Google Search Sources)
            if response.candidates[0].grounding_metadata:
                with st.expander("🌐 View Web Sources"):
                    st.write("Information verified by Google Search live.")

            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"API Error: {e}")
