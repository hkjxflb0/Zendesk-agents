from flask import Flask, render_template, request, jsonify, Response
import requests
import json
from threading import Lock
import time
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from pyngrok import ngrok
 
app = Flask(__name__)
 
# Zendesk API configuration
ZENDESK_SUBDOMAIN = "netsmartz3231"
ZENDESK_EMAIL = "ambikeshjha07@gmail.com"
ZENDESK_API_TOKEN = "hWL2MYxrucJaGJRkgT3YHPibYasaDQUzXcb9X0Nv"
ZENDESK_API_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"
 
# Function to fetch agents IDs from Zendesk (agents, admins)
def fetch_all_user_ids():
    url = f"{ZENDESK_API_URL}/users.json?role[]=agent&role[]=admin"
    headers = {"Content-Type": "application/json"}
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    user_ids = []
 
    while url:
        response = requests.get(url, headers=headers, auth=auth)
        if response.status_code == 200:
            data = response.json()
            for user in data["users"]:
                user_ids.append(user["id"])
            url = data.get("next_page")
            logger.debug(f"Fetched {len(data['users'])} users, next page: {url}")
        else:
            logger.error(f"Failed to fetch users: {response.status_code} - {response.text}")
            break
 
    return user_ids
 
# Fetch all user IDs at startup
AGENT_IDS = fetch_all_user_ids()
logger.info(f"Fetched {len(AGENT_IDS)} user IDs: {AGENT_IDS}")
 
GROUP_ID = 19035713601692
 
# Global variables
current_ticket_id = None
message_queue = []
message_lock = Lock()
chat_history = []
 
# Simple chatbot responses (used only before handover)
responses = {
    "hi": "Hello! How can I help you today?",
    "hello": "Hi there! How can I assist you?",
    "what can you do": "I can answer basic questions or hand this conversation over to a human agent. What do you need?",
    "how are you": "I’m doing great, thanks for asking! How about you?",
    "bye": "Goodbye! Let me know if you need me again.",
    "i want to talk to a human": "Sure, I’ll assign a human agent to you shortly.",
    "help": "I’m here to help! What do you need assistance with?"
}
 
requester_id = None
 
# Create a ticket and store the requester_id
def create_ticket(message):
    global requester_id

    # Format the chat history into a readable string
    transcript = "Chat History Before Handover:\n"
    if chat_history:
        for entry in chat_history:
            transcript += f"{entry['source']}: {entry['message']}\n"
    else:
        transcript += "No prior chat history.\n"
    transcript += f"\nCustomer Message Triggering Handover: {message}"

    url = f"{ZENDESK_API_URL}/tickets.json"
    headers = {"Content-Type": "application/json"}
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

    payload = {
        "ticket": {
            "subject": "Chatbot Escalation to Human Agent",
            "comment": {"body": transcript},  # Use the full transcript here
            "priority": "normal",
            "requester": {"name": "Chatbot User", "email": "chatbot.user@example.com"}
        }
    }
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    if response.status_code == 201:
        ticket_data = response.json()
        ticket_id = ticket_data["ticket"]["id"]
        requester_id = ticket_data["ticket"]["requester_id"]  # Save the user's ID
        return ticket_id, "Ticket created successfully with transcript!"
    else:
        return None, f"Failed to create ticket: {response.text}"
 
# Update the ticket with the correct author
def update_ticket(ticket_id, message):
    global requester_id
    url = f"{ZENDESK_API_URL}/tickets/{ticket_id}.json"
    headers = {"Content-Type": "application/json"}
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    payload = {
        "ticket": {
            "comment": {
                "body": message,
                "public": True,
                "author_id": requester_id
            }
        }
    }
    response = requests.put(url, json=payload, headers=headers, auth=auth)
    if response.status_code == 200:
        return True, "Message sent to agent successfully!"
    else:
        return False, f"Failed to send message: {response.text}"
   
 
def get_least_busy_agent(channel="support"):
    url = f"{ZENDESK_API_URL}/agent_availabilities"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Zendesk-Api-Version": "2023-02-01"
    }
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
 
    agent_ids_str = ",".join(str(agent_id) for agent_id in AGENT_IDS)
    params = {
        "filter[agent_id]": agent_ids_str,
        "filter[channel_status]": f"{channel}:online",
    }
 
    response = requests.get(url, params=params, headers=headers, auth=auth)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch agent availability: {response.text}")
 
    data = response.json()
    agents = data.get("data", [])
    if not agents:
        raise Exception("No online agents found for channel 'support'.")
 
    agent_workloads = {}
    included_channels = {item["id"]: item["attributes"] for item in data.get("included", []) if item["type"] == "channels"}
    for agent in agents:
        agent_id = agent["attributes"]["agent_id"]
        channel_refs = agent["relationships"]["channels"]["data"]
        for ref in channel_refs:
            channel_data = included_channels.get(ref["id"])
            if channel_data and channel_data["name"] == channel:
                work_items = channel_data.get("work_item_count", 0)
                agent_workloads[agent_id] = work_items
                break
 
    if not agent_workloads:
        raise Exception(f"No workload data found for channel '{channel}'.")
 
    least_busy_agent = min(agent_workloads, key=agent_workloads.get)
    min_work_items = agent_workloads[least_busy_agent]
    return least_busy_agent, min_work_items
 
def assign_ticket(ticket_id):
    try:
        agent_id, work_items = get_least_busy_agent(channel="support")
        url = f"{ZENDESK_API_URL}/tickets/{ticket_id}.json"
        headers = {"Content-Type": "application/json"}
        auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
        payload = {
            "ticket": {
                "assignee_id": agent_id,
                "group_id": GROUP_ID
            }
        }
        response = requests.put(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 200:
            return f"Ticket assigned to agent ID = {agent_id} (work items: {work_items}) successfully!"
        else:
            return f"Failed to assign ticket: {response.text}"
    except Exception as e:
        return f"Error during assignment: {str(e)}"
 
@app.route('/webhook', methods=['POST'])
def webhook():
    global current_ticket_id, message_queue, requester_id
    data = request.json
    logger.debug(f"Webhook received: {data}")
 
    ticket_id = data.get('ticket_id')
    if not ticket_id or ticket_id != str(current_ticket_id):
        logger.debug(f"Ignoring webhook - ticket_id {ticket_id} does not match current_ticket_id {current_ticket_id}")
        return jsonify({"status": "ignored"}), 200
 
    comment = data.get('ticket', {}).get('comment', {}).get('body')
    author_id = data.get('ticket', {}).get('comment', {}).get('author_id')
 
    if comment:
       
        if author_id in AGENT_IDS or author_id == "" or author_id == " " or author_id == None:  # Only process agent messages
            with message_lock:
                message_queue.append(f"Agent: {comment}")
        elif author_id == requester_id:  # Ignore user messages
            pass
        else:
            logger.debug(f"Skipping comment - author_id {author_id} not in AGENT_IDS or comment missing")
            with message_lock:
                message_queue.append(f"User: {comment}")
    return jsonify({"status": "received"}), 200
 
@app.route('/stream')
def stream():
    def event_stream():
        while True:
            with message_lock:
                if message_queue:
                    yield f"data: {json.dumps({'response': message_queue.pop(0)})}\n\n"
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")
 
@app.route('/')
def home():
    global current_ticket_id, message_queue, chat_history
    if not current_ticket_id:
        message_queue = []
        chat_history = []
    return render_template('index.html')
 
@app.route('/chat', methods=['POST'])
def chat():
    global current_ticket_id, requester_id, chat_history
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({'response': "Please say something!"})

    chat_history.append({"source": "User", "message": user_input})

    if current_ticket_id:  # If a ticket exists (human handover)
        success, response = update_ticket(current_ticket_id, user_input)
        return jsonify({'response': response})

    if user_input.lower() == "human_handover":
        ticket_id, create_response = create_ticket(user_input)  # Pass user_input to include in transcript
        if ticket_id:
            current_ticket_id = ticket_id
            assign_response = assign_ticket(ticket_id)
            response = f"{create_response} Ticket ID: {ticket_id}. {assign_response}"
        else:
            response = create_response
    else:
        response = responses.get(user_input.lower(), "I’m not sure how to respond to that. Ask for a human agent by clicking 'Talk to agent' button above")
        chat_history.append({"source": "Bot", "message": response})
    return jsonify({'response': response})
 
 
if __name__ == "__main__":
    ngrok.set_auth_token("2sL0plCt2Nt0XbX5xGcPwPpX2EQ_6NhM4CevXbvjA5BDugjNB")
    public_url = ngrok.connect(5000).public_url
    print(f"ngrok tunnel opened at: {public_url}")
    print(f"Set your Zendesk webhook to: {public_url}/webhook")
    app.run(host="0.0.0.0", port=5000)
 