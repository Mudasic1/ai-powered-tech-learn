import streamlit as st
import requests
import json
from datetime import datetime
import time
import random

# Set page configuration
st.set_page_config(
    page_title="TechLearn - Computer Science & Technology Assistant",
    page_icon="💻",
    layout="wide"
)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "topics" not in st.session_state:
    st.session_state.topics = set()

if "feedback_data" not in st.session_state:
    st.session_state.feedback_data = []

# Function to call free public API with multiple options and retries
def query_free_api(prompt, conversation_history):
    # List of free APIs to try
    api_endpoints = [
        {
            "url": "https://api-inference.huggingface.co/models/google/flan-t5-large",
            "json_path": "0.generated_text"
        },
        {
            "url": "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
            "json_path": "generated_text"
        },
        {
            "url": "https://api-inference.huggingface.co/models/bigscience/bloom-560m",
            "json_path": "0.generated_text"
        }
    ]
    
    # Prepare conversation history as context
    context = ""
    for msg in conversation_history[-3:]:  # Use last 3 messages for context
        role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
        context += role_prefix + msg["content"] + "\n"
    
    # Format the full input with context and current prompt
    # Focus specifically on computer science and technology
    cs_prefix = "As a computer science and technology tutor, answer the following: "
    full_input = f"{context}User: {cs_prefix}{prompt}\nAssistant:"
    
    # Try each API with retry logic
    max_retries = 3
    for api in api_endpoints:
        for attempt in range(max_retries):
            try:
                payload = {"inputs": full_input, "parameters": {"max_length": 500}}
                response = requests.post(api["url"], json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Parse the response using the provided json path
                    json_path = api["json_path"].split(".")
                    current = result
                    for path in json_path:
                        if path.isdigit():
                            path = int(path)
                        if isinstance(current, list) and isinstance(path, int) and path < len(current):
                            current = current[path]
                        elif isinstance(current, dict) and path in current:
                            current = current[path]
                        else:
                            raise KeyError("Invalid JSON path")
                    
                    if current and isinstance(current, str):
                        # Clean up response - remove any duplicate "Assistant:" prefixes
                        if current.startswith("Assistant:"):
                            current = current[len("Assistant:"):].strip()
                        return current
                
                # If we've reached the rate limit or server is busy, wait and retry
                if response.status_code in [429, 503]:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
                # If error, wait briefly and continue to next attempt or API
                time.sleep(1)
                continue
    
    # If all APIs fail, fall back to a static response
    # Craft a response based on the prompt content for computer science topics
    cs_keywords = {
        "python": "Python is a high-level, interpreted programming language known for its readability and versatility. It's widely used in web development, data analysis, AI, and automation.",
        "java": "Java is a class-based, object-oriented programming language designed for portability and cross-platform applications. It's commonly used for Android apps, enterprise software, and web applications.",
        "algorithm": "Algorithms are step-by-step procedures for solving problems or performing tasks. Key considerations include time complexity, space complexity, and correctness.",
        "data structure": "Data structures are specialized formats for organizing and storing data. Common examples include arrays, linked lists, stacks, queues, trees, and graphs.",
        "machine learning": "Machine learning is a field of AI that enables systems to learn from data and improve without explicit programming. Key approaches include supervised learning, unsupervised learning, and reinforcement learning.",
        "web": "Web development involves creating websites and web applications. It typically includes frontend (HTML, CSS, JavaScript) and backend (server-side logic and databases) components.",
        "network": "Computer networking involves the practice of connecting computers and devices to share resources and communicate. Key concepts include TCP/IP, routing, and network security.",
        "database": "Databases are organized collections of data stored and accessed electronically. Common types include relational databases (SQL) and non-relational databases (NoSQL).",
        "security": "Cybersecurity involves protecting systems, networks, and programs from digital attacks. Important practices include encryption, authentication, and regular security updates."
    }
    
    # Check if any keywords are in the prompt
    prompt_lower = prompt.lower()
    for keyword, explanation in cs_keywords.items():
        if keyword in prompt_lower:
            return explanation
    
    # Default response if no keywords match
    return "I'm currently experiencing high demand. Here's a general response about computer science and technology: Computer science is the study of computation, automation, and information. Technology refers to the application of scientific knowledge for practical purposes. Both fields are rapidly evolving and offer numerous career opportunities in software development, data science, cybersecurity, and more."

# Function to extract computer science and technology topics from text
def extract_cs_topics(text):
    # Computer science and technology specific topics
    cs_tech_topics = [
        "programming", "python", "java", "javascript", "html", "css", "c++", "c#",
        "algorithms", "data structures", "machine learning", "artificial intelligence",
        "web development", "mobile development", "databases", "sql", "nosql",
        "networking", "cybersecurity", "cryptography", "operating systems", "linux",
        "windows", "macos", "cloud computing", "aws", "azure", "google cloud",
        "devops", "agile", "git", "version control", "api", "microservices",
        "software engineering", "hardware", "robotics", "iot", "blockchain",
        "virtual reality", "augmented reality", "data science", "big data",
        "deep learning", "neural networks", "computer vision", "nlp"
    ]
    
    # Convert text to lowercase for comparison
    text_lower = text.lower()
    
    # Find matching topics
    found_topics = []
    for topic in cs_tech_topics:
        if topic in text_lower:
            # Capitalize appropriately (handle acronyms like IoT, AWS, etc.)
            if topic.upper() in ["AWS", "API", "SQL", "IOT", "NLP", "CSS", "HTML"]:
                found_topics.append(topic.upper())
            else:
                # Title case multi-word topics
                found_topics.append(" ".join(word.capitalize() for word in topic.split()))
    
    return found_topics[:3]  # Return at most 3 topics

# Function to save conversation
def save_conversation():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cs_conversation_{timestamp}.json"
    
    data = {
        "messages": st.session_state.messages,
        "topics": list(st.session_state.topics),
        "feedback": st.session_state.feedback_data
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    
    return filename

# UI Components
st.title("💻 TechLearn - Computer Science & Technology Assistant")
st.markdown("Ask me anything about programming, algorithms, databases, machine learning, web development, and other tech topics!")

# Sidebar for settings and features
with st.sidebar:
    st.header("Learning Tools")
    
    # Learning Mode
    st.subheader("Learning Mode")
    learning_mode = st.selectbox(
        "Select how you'd like to learn:",
        ["Standard", "Socratic Method", "Beginner-Friendly", "Advanced Technical"]
    )
    
    # Topic Explorer
    st.subheader("CS Topics Discussed")
    if st.session_state.topics:
        for topic in sorted(st.session_state.topics):
            st.write(f"• {topic}")
    else:
        st.write("No topics discussed yet.")
    
    # Quick Topic Buttons
    st.subheader("Quick Topics")
    col1, col2 = st.columns(2)
    
    if col1.button("Python Basics"):
        st.session_state.messages.append({"role": "user", "content": "Explain Python basics for beginners"})
        st.rerun()
        
    if col2.button("Data Structures"):
        st.session_state.messages.append({"role": "user", "content": "Explain common data structures in computer science"})
        st.rerun()
        
    if col1.button("Web Dev Stack"):
        st.session_state.messages.append({"role": "user", "content": "Explain the modern web development stack"})
        st.rerun()
        
    if col2.button("ML Concepts"):
        st.session_state.messages.append({"role": "user", "content": "Explain basic machine learning concepts"})
        st.rerun()
    
    # Conversation Management
    st.subheader("Conversation")
    if st.button("Save Conversation"):
        filename = save_conversation()
        st.success(f"Conversation saved as {filename}")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.topics = set()
        st.session_state.feedback_data = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Add feedback buttons for assistant messages
        if message["role"] == "assistant" and "feedback" not in message:
            cols = st.columns([1, 1, 4])
            message_index = st.session_state.messages.index(message)
            
            # Thumbs up button
            if cols[0].button("👍", key=f"thumbs_up_{message_index}"):
                message["feedback"] = "helpful"
                st.session_state.feedback_data.append({
                    "message_index": message_index,
                    "feedback": "helpful",
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()
            
            # Thumbs down button
            if cols[1].button("👎", key=f"thumbs_down_{message_index}"):
                message["feedback"] = "not_helpful"
                st.session_state.feedback_data.append({
                    "message_index": message_index,
                    "feedback": "not_helpful",
                    "timestamp": datetime.now().isoformat()
                })
                st.rerun()

# Input and response
if prompt := st.chat_input("What would you like to learn about computer science or technology?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant thinking indicator
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            # Modify prompt based on learning mode
            modified_prompt = prompt
            if learning_mode == "Socratic Method":
                modified_prompt = f"Using the Socratic method, help me understand this computer science concept: {prompt}"
            elif learning_mode == "Beginner-Friendly":
                modified_prompt = f"Explain this technology concept in simple terms for beginners: {prompt}"
            elif learning_mode == "Advanced Technical":
                modified_prompt = f"Provide a detailed technical explanation of this computer science topic: {prompt}"
            
            # Get response from free API
            response = query_free_api(modified_prompt, st.session_state.messages[:-1])
            
            # Extract and store CS/tech topics
            new_topics = extract_cs_topics(prompt + " " + response)
            for topic in new_topics:
                if topic:  # Basic validation
                    st.session_state.topics.add(topic)
            
            # Display response
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
