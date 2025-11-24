
import requests
import json
import os
import logging

# Configuration
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "element")
NTFY_BASE_URL = os.getenv("NTFY_BASE_URL", "https://ntfy.sh")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.aaca.eu.org/v1/chat/completions") # Example for Ollama
LLM_API_KEY = "sk-5rlYnWayiG2UNEiJJUUodMfpjYJ1M2lfhFRgDVBxOmqp5Uck" or os.getenv("LLM_API_KEY", "sk-5rlYnWayiG2UNEiJJUUodMfpjYJ1M2lfhFRgDVBxOmqp5Uck") # If your LLM API requires an API key
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4.5-flash") # Example for Ollama

# Conversation history
conversation_history = []
MAX_HISTORY_LENGTH = 10 # Keep last 10 messages (5 user, 5 assistant)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_to_llm_api(message_text: str) -> str:
    """
    Sends a message to the LLM API and returns its response.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    global conversation_history

    # Prepare messages for LLM, including system message and history
    messages = [
        {"role": "system", "content": "你是一个有帮助的助手。"}
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": message_text})

    data = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False # We want a single response
    }

    try:
        logging.info(f"Sending message to LLM: {message_text[:100]}...")
        response = requests.post(LLM_API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        llm_response = response.json()

        # Adjust based on your LLM API's response structure
        # This example assumes an Ollama-like response with a "response" key
        if llm_response.get("choices") and llm_response["choices"][0].get("message") and llm_response["choices"][0]["message"].get("content"):
            assistant_response = llm_response["choices"][0]["message"]["content"]

            # Update conversation history
            conversation_history.append({"role": "user", "content": message_text})
            conversation_history.append({"role": "assistant", "content": assistant_response})

            # Trim history if it exceeds MAX_HISTORY_LENGTH
            if len(conversation_history) > MAX_HISTORY_LENGTH:
                conversation_history = conversation_history[len(conversation_history) - MAX_HISTORY_LENGTH:]

            return assistant_response
        else:
            logging.warning(f"Unexpected LLM response structure: {llm_response}")
            return "Error: Unexpected LLM response format."
    except requests.exceptions.RequestException as e:
        logging.error(f"Error communicating with LLM API: {e}")
        return ""

def push_to_ntfy(message: str, title: str = "LLM Response", tags: list = None):
    """
    Pushes a message to the ntfy topic.
    """
    if tags is None:
        tags = ["llm"]

    ntfy_url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}"
    headers = {
        "Title": title,
        "Tags": ",".join(tags),
        "Content-Type": "text/plain"
    }

    try:
        logging.info(f"Pushing response to ntfy topic {NTFY_TOPIC}: {message[:100]}...")
        response = requests.post(ntfy_url, headers=headers, data=message.encode('utf-8'))
        response.raise_for_status()
        logging.info("Successfully pushed message to ntfy.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error pushing to ntfy: {e}")

def listen_to_ntfy():
    """
    Listens to the ntfy topic for new messages, sends them to LLM, and pushes the response.
    """
    listen_url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}/json"
    logging.info(f"Listening for ntfy messages on {listen_url}...")

    try:
        with requests.get(listen_url, stream=True, timeout=None) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    try:
                        message = json.loads(line.decode('utf-8'))
                        if message.get("event") == "message":
                            message_text = message.get("message")
                            if message_text:
                                logging.info(f"Received ntfy message: {message_text}")
                                llm_response = send_to_llm_api(message_text)
                                if llm_response:
                                    push_to_ntfy(llm_response, title=f"LLM Reply to: {message_text[:50]}...")
                    except json.JSONDecodeError:
                        logging.warning(f"Received non-JSON line from ntfy: {line.decode('utf-8')}")
                    except Exception as e:
                        logging.error(f"Error processing ntfy message: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error listening to ntfy: {e}. Retrying in 5 seconds...")
        # Simple reconnect logic, consider exponential backoff for production
        import time
        time.sleep(5)
        listen_to_ntfy() # Recursive call to retry listening

if __name__ == "__main__":
    logging.info("Starting ntfy-LLM bot...")
    listen_to_ntfy()
