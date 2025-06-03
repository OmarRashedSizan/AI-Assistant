import streamlit as st
import os
import sys
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import io
import logging
import google.generativeai as genai

# --- Streamlit Page Configuration MUST BE THE FIRST Streamlit command ---
st.set_page_config(page_title="Siz Voice Assistant", page_icon="🎙️")
 # Replace with your name or organization
# --- End of Streamlit Page Configuration ---

# --- Core Voice Assistant Functions (included directly for simplicity) ---
# If you prefer separate files, ensure 'voice_assistant_core.py' exists
# and contains these functions, then uncomment the import below and remove definitions.
# try:
#     from voice_assistant_core import takeCommand, gemini_model, speak
# except ImportError:
#     st.warning("Could not find 'voice_assistant_core.py'. Defining functions directly in app.py for demonstration.")


# Logging Configuration
LOG_DIR = "logs"
LOG_FILE_NAME = "application.log"
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def speak(audio, lang='en'):
    """
    Function for the assistant to speak, using gTTS and pydub.
    Sets 'slow=False' for faster, more human-like speech.
    """
    try:
        tts = gTTS(text=audio, lang=lang, slow=False) # slow=False makes it faster
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        audio_segment = AudioSegment.from_file(mp3_fp, format="mp3")
        play(audio_segment)

    except Exception as e:
        print(f"Problem playing audio: {e}")
        st.error(f"Error playing audio: {e}. Ensure ffmpeg is installed and accessible.")
        print("Possible reasons: No internet connection, or ffmpeg is not installed or not added to PATH.")
        print("If ffmpeg is not installed, download it from https://ffmpeg.org/download.html and add it to PATH.")
        logging.error(f"Audio playback error: {e}")


def takeCommand():
    """
    Function to take voice input from the microphone.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        r.pause_threshold = 1
        r.energy_threshold = 300
        audio = r.listen(source)

    try:
        st.info("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        query = query.lower()
        st.success(f"User said: {query}")
        return query

    except sr.UnknownValueError:
        st.warning("Sorry, I couldn't understand what you said.")
        return "None"
    except sr.RequestError as e:
        st.error(f"Could not request results from Speech Recognition service; {e}")
        return "None"
    except Exception as e:
        logging.info(e)
        st.error("Please say again...")
        return "None"


def gemini_model(user_input):
    """
    Function to process user input using the Gemini AI model.
    The model name is directly set to 'gemini-1.5-flash-latest' in this version.
    """
    
    genai.configure(api_key="AIzaSyAFqRbuJxDJKsfWWb0ld6Ci5DNcuI6XazU") 

    chosen_model_name = "gemini-1.5-flash-latest"

    try:
        st.info(f"Using Gemini model: {chosen_model_name}")
        model = genai.GenerativeModel(chosen_model_name)
        response = model.generate_content(user_input)
        result = response.text
        return result
    except Exception as e:
        st.error(f"Problem connecting to or processing data with Gemini model: {e}")
        print(f"Possible reason: Model '{chosen_model_name}' is not available or supported for your API key or region.")
        logging.error(f"Error in gemini_model with hardcoded model '{chosen_model_name}': {e}")
        return "Sorry, there was a problem connecting to or processing data with the Gemini model."


# --- Streamlit UI ---

st.title("🗣️ Hi I am Siz, AI Voice Assistant")
st.markdown("""### Develpoed by Omar Rashed Sizan""")
# Initialize session state for conversation history and last response
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'last_ai_response' not in st.session_state:
    st.session_state.last_ai_response = ""

# Display conversation history
st.subheader("Conversation Log:")
chat_display = st.container(height=400, border=True) # A scrollable container for chat
with chat_display:
    for entry in st.session_state.conversation_history:
        if entry['type'] == 'user':
            st.markdown(f"**You:** {entry['text']}")
        elif entry['type'] == 'ai':
            st.markdown(f"**AI:** {entry['text']}")
    # Auto-scroll to bottom (Note: this JS might not work perfectly with all Streamlit updates)
    st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)


# Text input for "Chat" functionality
typed_prompt = st.text_input("Type your message here:", key="typed_prompt")

# --- Functions to handle button clicks ---

def process_and_display_response(user_input_text):
    if user_input_text and user_input_text.strip() != "":
        st.session_state.conversation_history.append({'type': 'user', 'text': user_input_text})
        ai_response = gemini_model(user_input_text)
        if ai_response:
            st.session_state.last_ai_response = ai_response # Store for speaking
            st.session_state.conversation_history.append({'type': 'ai', 'text': ai_response})
            st.rerun() # Rerun to update the history display
    else:
        st.warning("Please type a message or speak into the microphone.")


def ask_me_callback():
    """Handles logic for the 'Ask Me' (voice input) button."""
    user_command = takeCommand()
    process_and_display_response(user_command)


def chat_callback():
    """Handles logic for the 'Chat' (text input) button."""
    if typed_prompt:
        process_and_display_response(typed_prompt)
        st.session_state.typed_prompt = "" # Clear the input field after sending
    else:
        st.warning("Please type a message before clicking 'Chat'.")


def speak_response_callback():
    """Handles logic for the 'Speak Response' button."""
    if st.session_state.last_ai_response:
        st.info("Speaking the last AI response...")
        speak(st.session_state.last_ai_response, lang='en')
    else:
        st.warning("No AI response to speak yet. Ask me a question first!")


def end_conversation_callback():
    """Handles logic for the 'End Conversation' button."""
    st.session_state.conversation_history = []
    st.session_state.last_ai_response = ""
    st.success("Conversation ended. History cleared.")
    st.rerun()


# --- Buttons for interaction ---
st.markdown("---") # Separator
col1, col2, col3, col4 = st.columns(4) # Added one more column for the new button

with col1:
    if st.button("💬 Chat"):
        chat_callback()

with col2:
    if st.button("🎙️ Ask Me"):
        ask_me_callback()

with col3:
    if st.button("🔊 Speak Response"):
        speak_response_callback()

with col4:
    if st.button("👋 End Conversation"):
        end_conversation_callback()