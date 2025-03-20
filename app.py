# # from flask import Flask, render_template, request, jsonify, Response
# # import requests
# # import json
# # from threading import Lock
# # import time
# # import logging
# # logging.basicConfig(level=logging.DEBUG)
# # logger = logging.getLogger(__name__)
# # from pyngrok import ngrok
 
# # app = Flask(__name__)
 
# # # Zendesk API configuration (replace with your own details)
# # ZENDESK_SUBDOMAIN = "netsmartz3231"  
# # ZENDESK_EMAIL = "ambikeshjha07@gmail.com"
# # ZENDESK_API_TOKEN = "hWL2MYxrucJaGJRkgT3YHPibYasaDQUzXcb9X0Nv"
# # ZENDESK_API_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"
 
# # # # Hardcoded agent and group IDs (replace with real IDs from your Zendesk)
# # # AGENT_ID = 19035726117532  # Ambikesh Jha
# # # # AGENT_ID = 19035726117532  # Test user
 
# # # List of agent IDs (replace with your three agents' real IDs)
# # AGENT_IDS = [19035726117532, 19059726748444, 19059774975772,19103307476764]  
# # GROUP_ID = 19035713601692  # Example group ID (all agents should belong to this group)
 
# # last_agent_index = -1
 
# # # Store the current ticket ID and messages
# # current_ticket_id = None
# # message_queue = []
# # message_lock = Lock()
 
# # # Simple chatbot responses
# # responses = {
# #     "hi": "Hello! How can I help you today?",
# #     "hello": "Hi there! How can I assist you?",
# #     "what can you do": "I can answer basic questions or hand this conversation over to a human agent. What do you need?",
# #     "how are you": "I’m doing great, thanks for asking! How about you?",
# #     "bye": "Goodbye! Let me know if you need me again.",
# #     "i want to talk to a human": "Sure, I’ll assign a human agent to you shortly.",
# #     "help": "I’m here to help! What do you need assistance with?"
# # }
 
# # # Function to create a ticket in Zendesk
# # def create_ticket(message):
# #     url = f"{ZENDESK_API_URL}/tickets.json"
# #     headers = {"Content-Type": "application/json"}
# #     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
# #     payload = {
# #         "ticket": {
# #             "subject": "Chatbot Escalation to Human Agent",
# #             "comment": {"body": message},
# #             "priority": "normal"
# #         }
# #     }
# #     response = requests.post(url, json=payload, headers=headers, auth=auth)
# #     if response.status_code == 201:
# #         ticket_data = response.json()
# #         return ticket_data["ticket"]["id"], "Ticket created successfully!"
# #     else:
# #         return None, f"Failed to create ticket: {response.text}"
 
 
# # def get_least_busy_agent(channel="support"):
# #     url = f"{ZENDESK_API_URL}/agent_availabilities"
# #     headers = {
# #         "Content-Type": "application/json",
# #         "Accept": "application/json",
# #         "Zendesk-Api-Version": "2023-02-01"
# #     }
# #     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
 
# #     agent_ids_str = ",".join(str(agent_id) for agent_id in AGENT_IDS)
# #     params = {
# #         "filter[agent_id]": agent_ids_str,
# #         "filter[channel_status]": f"{channel}:online",  # Only online agents
# #     }
 
# #     logger.debug(f"Fetching availability: {url} with params {params}")
# #     response = requests.get(url, params=params, headers=headers, auth=auth)
# #     if response.status_code != 200:
# #         logger.error(f"API error: {response.status_code} - {response.text}")
# #         raise Exception(f"Failed to fetch agent availability: {response.text}")
 
# #     data = response.json()
# #     logger.debug(f"Raw API response: {data}")
 
# #     agents = data.get("data", [])
# #     if not agents:
# #         logger.warning("No agents found.")
# #         raise Exception("No online agents found for channel 'support'.")
 
# #     agent_workloads = {}
# #     included_channels = {item["id"]: item["attributes"] for item in data.get("included", []) if
# #                          item["type"] == "channels"}
# #     logger.debug(f"Included channels: {included_channels}")
 
# #     for agent in agents:
# #         agent_id = agent["attributes"]["agent_id"]
# #         channel_refs = agent["relationships"]["channels"]["data"]
# #         logger.debug(f"Agent {agent_id} channel refs: {channel_refs}")
# #         for ref in channel_refs:
# #             channel_data = included_channels.get(ref["id"])
# #             if channel_data and channel_data["name"] == channel:
# #                 work_items = channel_data.get("work_item_count", 0)
# #                 agent_workloads[agent_id] = work_items
# #                 logger.debug(f"Agent {agent_id} has {work_items} work items in {channel}")
# #                 break
 
# #     if not agent_workloads:
# #         logger.error("No workload data found.")
# #         raise Exception(f"No workload data found for channel '{channel}'.")
 
# #     logger.debug(f"Agent workloads: {agent_workloads}")
# #     least_busy_agent = min(agent_workloads, key=agent_workloads.get)
# #     min_work_items = agent_workloads[least_busy_agent]
 
# #     logger.info(f"Selected agent {least_busy_agent} with {min_work_items} work items")
# #     return least_busy_agent, min_work_items
 
 
# # def assign_ticket(ticket_id):
# #     try:
# #         agent_id, work_items = get_least_busy_agent(channel="support")
# #         url = f"{ZENDESK_API_URL}/tickets/{ticket_id}.json"
# #         headers = {"Content-Type": "application/json"}
# #         auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
# #         payload = {
# #             "ticket": {
# #                 "assignee_id": agent_id,
# #                 "group_id": GROUP_ID
# #             }
# #         }
# #         response = requests.put(url, json=payload, headers=headers, auth=auth)
# #         if response.status_code == 200:
# #             return f"Ticket assigned to agent ID = {agent_id} (work items: {work_items}) successfully!"
# #         else:
# #             return f"Failed to assign ticket: {response.text}"
# #     except Exception as e:
# #         return f"Error during assignment: {str(e)}"
 
 
# # # Webhook endpoint to receive Zendesk updates
# # @app.route('/webhook', methods=['POST'])
# # def webhook():
# #     global current_ticket_id, message_queue
# #     data = request.json
# #     print("*******************",data)
# #     logger.debug(f"Webhook received: {data}")
# #     ticket_id = data.get('ticket_id')
# #     print("**********",ticket_id,current_ticket_id)
# #     # if ticket_id != current_ticket_id:
# #     #     print("Ignoring ticket ID mismatch")
# #     #     return jsonify({"status": "ignored"}), 200
# #     print("**********",data.get('ticket', {}).get('comment', {}).get('body'))
# #     # Extract the latest comment from the webhook payload
# #     comment = data.get('ticket', {}).get('comment', {}).get('body')
# #     author_id = data.get('ticket', {}).get('comment', {}).get('author_id')
# #     print("**********",comment)
# #     if comment:  # Only agent comments
# #         print("*****coment inside*****",comment)
# #         message_queue.append(f"Agent : {comment}")
# #         print("***",message_queue)
# #     return jsonify({"status": "received"}), 200
 
# # # SSE endpoint for real-time updates
# # @app.route('/stream')
# # def stream():
# #     def event_stream():
# #         while True:
# #             with message_lock:
# #                 if message_queue:
# #                     yield f"data: {json.dumps({'response': message_queue.pop(0)})}\n\n"
# #             time.sleep(1)  # Adjust frequency as needed
# #     return Response(event_stream(), mimetype="text/event-stream")
 
# # # Home route to render the UI
# # @app.route('/')
# # def home():
# #     global current_ticket_id, message_queue
# #     current_ticket_id = None
# #     message_queue = []
# #     return render_template('index.html')


# # # API route to handle chatbot input
# # @app.route('/chat', methods=['POST'])
# # def chat():
# #     global current_ticket_id
# #     user_input = request.json.get('message').lower().strip()
# #     if not user_input:
# #         return jsonify({'response': "Please say something!"})

# #     if user_input == "human_handover":  # Check for button trigger
# #         ticket_id, create_response = create_ticket("Customer requested human agent.")
# #         print(create_response)

# #         if ticket_id:
# #             assign_response = assign_ticket(ticket_id)
# #             current_ticket_id = ticket_id
# #             response = f"{create_response} Ticket ID: {ticket_id}. {assign_response}"
# #         else:
# #             response = create_response
# #     else:
# #         response = responses.get(user_input, "I’m not sure how to respond to that. ask for a human agent! by clicking 'Talk to agent' button above")
# #     return jsonify({'response': response})
 

# # if __name__ == "__main__":
# #     ngrok.set_auth_token("2sL0plCt2Nt0XbX5xGcPwPpX2EQ_6NhM4CevXbvjA5BDugjNB")  # Set your ngrok auth token
# #     public_url = ngrok.connect(5000).public_url
# #     print(f"ngrok tunnel opened at: {public_url}")
# #     print(f"Set your Zendesk webhook to: {public_url}/webhook")

# #     app.run(host="0.0.0.0", port=5000)

# from flask import Flask, render_template, request, jsonify, Response
# import requests
# import json
# from threading import Lock
# import time
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)
# from pyngrok import ngrok

# app = Flask(__name__)

# # Zendesk API configuration
# ZENDESK_SUBDOMAIN = "netsmartz3231"
# ZENDESK_EMAIL = "ambikeshjha07@gmail.com"
# ZENDESK_API_TOKEN = "hWL2MYxrucJaGJRkgT3YHPibYasaDQUzXcb9X0Nv"
# ZENDESK_API_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"

# AGENT_IDS = [19035726117532, 19059726748444, 19059774975772, 19103307476764]
# GROUP_ID = 19035713601692

# # Global variables
# current_ticket_id = None
# message_queue = []
# message_lock = Lock()

# # Simple chatbot responses
# responses = {
#     "hi": "Hello! How can I help you today?",
#     "hello": "Hi there! How can I assist you?",
#     "what can you do": "I can answer basic questions or hand this conversation over to a human agent. What do you need?",
#     "how are you": "I’m doing great, thanks for asking! How about you?",
#     "bye": "Goodbye! Let me know if you need me again.",
#     "i want to talk to a human": "Sure, I’ll assign a human agent to you shortly.",
#     "help": "I’m here to help! What do you need assistance with?"
# }

# def create_ticket(message):
#     url = f"{ZENDESK_API_URL}/tickets.json"
#     headers = {"Content-Type": "application/json"}
#     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
#     payload = {
#         "ticket": {
#             "subject": "Chatbot Escalation to Human Agent",
#             "comment": {"body": message},
#             "priority": "normal",
#             "requester": {"name": "Chatbot User", "email": "chatbot.user@example.com"}  # Optional: Set a requester
#         }
#     }
#     response = requests.post(url, json=payload, headers=headers, auth=auth)
#     if response.status_code == 201:
#         ticket_data = response.json()
#         return ticket_data["ticket"]["id"], "Ticket created successfully!"
#     else:
#         return None, f"Failed to create ticket: {response.text}"

# def get_least_busy_agent(channel="support"):
#     url = f"{ZENDESK_API_URL}/agent_availabilities"
#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#         "Zendesk-Api-Version": "2023-02-01"
#     }
#     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

#     agent_ids_str = ",".join(str(agent_id) for agent_id in AGENT_IDS)
#     params = {
#         "filter[agent_id]": agent_ids_str,
#         "filter[channel_status]": f"{channel}:online",
#     }

#     logger.debug(f"Fetching availability: {url} with params {params}")
#     response = requests.get(url, params=params, headers=headers, auth=auth)
#     if response.status_code != 200:
#         logger.error(f"API error: {response.status_code} - {response.text}")
#         raise Exception(f"Failed to fetch agent availability: {response.text}")

#     data = response.json()
#     agents = data.get("data", [])
#     if not agents:
#         raise Exception("No online agents found for channel 'support'.")

#     agent_workloads = {}
#     included_channels = {item["id"]: item["attributes"] for item in data.get("included", []) if item["type"] == "channels"}
#     for agent in agents:
#         agent_id = agent["attributes"]["agent_id"]
#         channel_refs = agent["relationships"]["channels"]["data"]
#         for ref in channel_refs:
#             channel_data = included_channels.get(ref["id"])
#             if channel_data and channel_data["name"] == channel:
#                 work_items = channel_data.get("work_item_count", 0)
#                 agent_workloads[agent_id] = work_items
#                 break

#     if not agent_workloads:
#         raise Exception(f"No workload data found for channel '{channel}'.")

#     least_busy_agent = min(agent_workloads, key=agent_workloads.get)
#     min_work_items = agent_workloads[least_busy_agent]
#     return least_busy_agent, min_work_items

# def assign_ticket(ticket_id):
#     try:
#         agent_id, work_items = get_least_busy_agent(channel="support")
#         url = f"{ZENDESK_API_URL}/tickets/{ticket_id}.json"
#         headers = {"Content-Type": "application/json"}
#         auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
#         payload = {
#             "ticket": {
#                 "assignee_id": agent_id,
#                 "group_id": GROUP_ID
#             }
#         }
#         response = requests.put(url, json=payload, headers=headers, auth=auth)
#         if response.status_code == 200:
#             return f"Ticket assigned to agent ID = {agent_id} (work items: {work_items}) successfully!"
#         else:
#             return f"Failed to assign ticket: {response.text}"
#     except Exception as e:
#         return f"Error during assignment: {str(e)}"

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     global current_ticket_id, message_queue
#     data = request.json
#     logger.debug(f"Webhook received: {data}")
    
#     ticket_id = data.get('ticket_id')
#     if not ticket_id or ticket_id != str(current_ticket_id):  # Ensure ticket_id matches current session
#         logger.debug(f"Ignoring webhook - ticket_id {ticket_id} does not match current_ticket_id {current_ticket_id}")
#         return jsonify({"status": "ignored"}), 200

#     # Extract comment and author_id
#     comment = data.get('ticket', {}).get('comment', {}).get('body')
#     author_id = data.get('ticket', {}).get('comment', {}).get('author_id')

#     if comment:  # Only process agent comments
#         with message_lock:
#             message_queue.append(f"Agent : {comment}")
#     else:
#         logger.debug(f"Skipping comment - author_id {author_id} not in AGENT_IDS or comment missing")
    
#     return jsonify({"status": "received"}), 200

# @app.route('/stream')
# def stream():
#     def event_stream():
#         while True:
#             with message_lock:
#                 if message_queue:
#                     yield f"data: {json.dumps({'response': message_queue.pop(0)})}\n\n"
#             time.sleep(1)
#     return Response(event_stream(), mimetype="text/event-stream")

# @app.route('/')
# def home():
#     global current_ticket_id, message_queue
#     # Only reset if no active ticket
#     if not current_ticket_id:
#         message_queue = []
#     return render_template('index.html')

# @app.route('/chat', methods=['POST'])
# def chat():
#     global current_ticket_id
#     user_input = request.json.get('message', '').lower().strip()
#     if not user_input:
#         return jsonify({'response': "Please say something!"})

#     if user_input == "human_handover":
#         ticket_id, create_response = create_ticket("Customer requested human agent.")
#         if ticket_id:
#             current_ticket_id = ticket_id  # Update current_ticket_id immediately
#             assign_response = assign_ticket(ticket_id)
#             response = f"{create_response} Ticket ID: {ticket_id}. {assign_response}"
#         else:
#             response = create_response
#     else:
#         response = responses.get(user_input, "I’m not sure how to respond to that. Ask for a human agent by clicking 'Talk to agent' button above")
#     return jsonify({'response': response})

# if __name__ == "__main__":
#     ngrok.set_auth_token("2sL0plCt2Nt0XbX5xGcPwPpX2EQ_6NhM4CevXbvjA5BDugjNB")
#     public_url = ngrok.connect(5000).public_url
#     print(f"ngrok tunnel opened at: {public_url}")
#     print(f"Set your Zendesk webhook to: {public_url}/webhook")
#     app.run(host="0.0.0.0", port=5000)

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

AGENT_IDS = [19035726117532, 19059726748444, 19059774975772, 19103307476764]
GROUP_ID = 19035713601692

# Global variables
current_ticket_id = None
message_queue = []
message_lock = Lock()

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

def create_ticket(message):
    url = f"{ZENDESK_API_URL}/tickets.json"
    headers = {"Content-Type": "application/json"}
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    payload = {
        "ticket": {
            "subject": "Chatbot Escalation to Human Agent",
            "comment": {"body": message},
            "priority": "normal",
            "requester": {"name": "Chatbot User", "email": "chatbot.user@example.com"}
        }
    }
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    if response.status_code == 201:
        ticket_data = response.json()
        ticket_id = ticket_data["ticket"]["id"]
        logger.debug(f"Ticket created: {ticket_data}")
        return ticket_id, "Ticket created successfully!"
    else:
        logger.error(f"Failed to create ticket: {response.text}")
        return None, f"Failed to create ticket: {response.text}"

def update_ticket(ticket_id, message):
    url = f"{ZENDESK_API_URL}/tickets/{ticket_id}.json"
    headers = {"Content-Type": "application/json"}
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    payload = {
        "ticket": {
            "comment": {
                "body": message,
                "public": True  # Ensures the comment is visible to the requester
            }
        }
    }
    response = requests.put(url, json=payload, headers=headers, auth=auth)
    if response.status_code == 200:
        logger.debug(f"Comment added to ticket {ticket_id}: {message}")
        return True, "Message sent to agent successfully!"
    else:
        logger.error(f"Failed to update ticket {ticket_id}: {response.text}")
        return False, f"Failed to send message to agent: {response.text}"

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
    global current_ticket_id, message_queue
    data = request.json
    logger.debug(f"Webhook received: {data}")
    
    ticket_id = data.get('ticket_id')
    if not ticket_id or ticket_id != str(current_ticket_id):
        logger.debug(f"Ignoring webhook - ticket_id {ticket_id} does not match current_ticket_id {current_ticket_id}")
        return jsonify({"status": "ignored"}), 200

    comment = data.get('ticket', {}).get('comment', {}).get('body')
    author_id = data.get('ticket', {}).get('comment', {}).get('author_id')

    if comment and author_id:
        author_id = int(author_id)
        if author_id in AGENT_IDS:
            logger.debug(f"Processing agent comment from {author_id}: {comment}")
            with message_lock:
                message_queue.append(f"Agent (ID: {author_id}): {comment}")
        else:
            logger.debug(f"Skipping comment - author_id {author_id} is not an agent (likely requester)")
    else:
        logger.debug(f"Skipping comment - missing author_id or comment: {data}")
    
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
    global current_ticket_id, message_queue
    if not current_ticket_id:
        message_queue = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global current_ticket_id
    user_input = request.json.get('message', '').lower().strip()
    if not user_input:
        return jsonify({'response': "Please say something!"})

    # If a ticket is active, send the message to Zendesk instead of processing locally
    if current_ticket_id:
        success, response = update_ticket(current_ticket_id, user_input)
        if success:
            # Optionally add the user's message to the local queue for display
            with message_lock:
                message_queue.append(f"You: {user_input}")
        return jsonify({'response': response})
    
    # Otherwise, handle with chatbot logic
    if user_input == "human_handover":
        ticket_id, create_response = create_ticket("Customer requested human agent.")
        if ticket_id:
            current_ticket_id = ticket_id
            assign_response = assign_ticket(ticket_id)
            response = f"{create_response} Ticket ID: {ticket_id}. {assign_response}"
        else:
            response = create_response
    else:
        response = responses.get(user_input, "I’m not sure how to respond to that. Ask for a human agent by clicking 'Talk to agent' button above")
    return jsonify({'response': response})

if __name__ == "__main__":
    ngrok.set_auth_token("2sL0plCt2Nt0XbX5xGcPwPpX2EQ_6NhM4CevXbvjA5BDugjNB")
    public_url = ngrok.connect(5000).public_url
    print(f"ngrok tunnel opened at: {public_url}")
    print(f"Set your Zendesk webhook to: {public_url}/webhook")
    app.run(host="0.0.0.0", port=5000)