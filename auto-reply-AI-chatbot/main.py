import os
import sys
import time
import urllib.request
import json
import pyautogui
import pyperclip
import ssl

# Disable SSL verification globally (fixes macOS Python SSL certificate issues)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# --- 1. CONFIGURATION & ENVIRONMENT LOADING ---
def load_env():
    """Loads environment variables from .env file manually to minimize external dependencies."""
    # Ensure it looks for .env in the same directory as main.py, regardless of where the script is run from
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip()
                        # Remove surrounding quotes if present
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        os.environ[key.strip()] = val

load_env()

# Read settings from env with sensible defaults
PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TARGET_USER = os.environ.get("TARGET_USER", "Rohan Das")

# Coordinates calibration settings
CHROME_ICON = (int(os.environ.get("CHROME_ICON_X", 100)), int(os.environ.get("CHROME_ICON_Y", 800)))
DRAG_START = (int(os.environ.get("DRAG_START_X", 400)), int(os.environ.get("DRAG_START_Y", 200)))
DRAG_END = (int(os.environ.get("DRAG_END_X", 1000)), int(os.environ.get("DRAG_END_Y", 700)))
INPUT_BOX = (int(os.environ.get("INPUT_BOX_X", 600)), int(os.environ.get("INPUT_BOX_Y", 750)))

# --- 2. LLM RESPONSE GENERATION ---
def generate_roast_response(chat_history):
    """Generates a response using either Google Gemini or OpenAI API."""
    prompt = (
        f"You are a wildly hilarious and savage virtual assistant named Naruto. "
        f"You need to write a witty, friendly roast/reply to the latest message in this chat history. "
        f"Keep the reply extremely short (1 to 2 sentences maximum). "
        f"IMPORTANT: You must write the response in 'Banglish' (Bengali written in English letters, mixed with English). "
        f"Make it extremely humorous, savage, and packed with relevant emojis! 😂🔥 "
        f"Do not include any quotes or prefix like 'Naruto: ' in your output. Just return the raw message with emojis.\n\n"
        f"Chat History:\n{chat_history}\n"
    )

    if PROVIDER == "gemini":
        if not GEMINI_API_KEY or "your_gemini_api" in GEMINI_API_KEY:
            print("Error: Gemini API Key not set in .env")
            return None
        
        # Call Gemini API via raw urllib (no package install needed)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                return res_body['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            print(f"Gemini API request failed: {e}")
            return None

    elif PROVIDER == "openai":
        if not OPENAI_API_KEY or "your_openai_api" in OPENAI_API_KEY:
            print("Error: OpenAI API Key not set in .env")
            return None
        
        # Call OpenAI API via raw urllib (no package install needed)
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are Naruto, a funny AI chatbot helper."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                return res_body['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"OpenAI API request failed: {e}")
            return None
    
    print(f"Unknown provider: {PROVIDER}")
    return None

# --- 3. CHAT HISTORY PARSING ---
def is_last_message_from_target(chat_text, target):
    """
    Checks if the last message in the chat history is from the target user.
    Optimized for WhatsApp Desktop format: '[10:15 AM, 5/27/2026] Name: Message'
    """
    if not chat_text:
        return False
    
    # Split text into lines and clean them
    lines = [line.strip() for line in chat_text.split("\n") if line.strip()]
    if not lines:
        return False
    
    recent_lines = lines[-5:]
    print("--- Detected Recent Chat Lines ---")
    for rl in recent_lines:
        print(f"  > {rl}")
    print("---------------------------------")
    
    # Iterate from the last line upwards to find the most recent message block
    for line in reversed(lines):
        # WhatsApp format: '[10:15 AM, 5/27/2026] Sandip: Hello'
        if "]" in line and ":" in line.split("]", 1)[-1]:
            # Get everything after the ']' which contains ' SenderName: Message'
            after_bracket = line.split("]", 1)[-1]
            # Split at the colon to get the sender name
            sender_name = after_bracket.split(":", 1)[0]
            
            # Check if target name is present in the sender name
            if target.lower() in sender_name.lower():
                return True
            else:
                return False
                
    # Fallback containment check
    for line in reversed(recent_lines):
        if target.lower() in line.lower():
            return True
            
    return False

# --- 4. MAIN AUTOMATION LOOP ---
def run_chatbot():
    print(f"Starting Naruto Auto-Reply Chatbot (Target: {TARGET_USER}, Provider: {PROVIDER})...")
    
    # Step 1: Open/focus the Chrome or Chat Application
    print("Focusing chat application...")
    pyautogui.click(CHROME_ICON[0], CHROME_ICON[1])
    time.sleep(1.5)
    
    # Platform-specific copy shortcut modifier key
    modifier = "command" if sys.platform == "darwin" else "ctrl"
    
    try:
        while True:
            print("\nScanning for new messages...")
            # Step 2: Drag mouse to select chat history area (top to bottom)
            pyautogui.moveTo(DRAG_START[0], DRAG_START[1])
            time.sleep(0.3)
            # Use PyAutoGUI's dragTo for a continuous drag movement
            pyautogui.dragTo(DRAG_END[0], DRAG_END[1], duration=1.5, button="left")
            time.sleep(0.5)
            
            # Step 3: Copy selected text to clipboard
            pyautogui.keyDown(modifier)
            pyautogui.press("c")
            pyautogui.keyUp(modifier)
            time.sleep(0.5)  # Wait for clipboard buffer
            
            # Click somewhere neutral to deselect text
            pyautogui.click(DRAG_START[0], DRAG_START[1])
            time.sleep(0.2)
            
            chat_text = pyperclip.paste()
            print(f"[Debug] Copied text length from clipboard: {len(chat_text)}")
            if len(chat_text) > 0:
                print(f"[Debug] First 50 chars of clipboard: {repr(chat_text[:50])}")
            
            # Step 4: Analyze if target sent the last message
            if is_last_message_from_target(chat_text, TARGET_USER):
                print(f"New message from target '{TARGET_USER}' detected! Generating reply...")
                
                response = generate_roast_response(chat_text)
                if response:
                    print(f"Generated Response: {response}")
                    
                    # Step 5: Paste and Send reply
                    pyperclip.copy(response)
                    
                    # Click input box
                    pyautogui.click(INPUT_BOX[0], INPUT_BOX[1])
                    time.sleep(0.2)
                    
                    # Paste response
                    pyautogui.keyDown(modifier)
                    pyautogui.press("v")
                    pyautogui.keyUp(modifier)
                    time.sleep(0.2)
                    
                    # Press enter to send
                    pyautogui.press("enter")
                    print("Reply sent successfully!")
                else:
                    print("Failed to generate response.")
            else:
                print("No new message from target user.")
                
            # Wait before scanning again (cooldown)
            print("Waiting 10 seconds before next scan...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nChatbot stopped by user.")

if __name__ == "__main__":
    run_chatbot()