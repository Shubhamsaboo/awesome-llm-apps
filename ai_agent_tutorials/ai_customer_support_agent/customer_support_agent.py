import streamlit as st
from openai import OpenAI
from mem0 import Memory
import os
import json
from datetime import datetime, timedelta

# Set up the Streamlit App
st.title("AI Customer Support Agent with Memory 🛒")
st.caption("Chat with a customer support assistant who remembers your past interactions.")

# Set the OpenAI API key
openai_api_key = st.text_input("Enter OpenAI API Key", type="password")

if openai_api_key:
    os.environ['OPENAI_API_KEY'] = openai_api_key
    
    class CustomerSupportAIAgent:
        def __init__(self):
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "model": "gpt-4o-mini",
                        "host": "localhost",
                        "port": 6333,
                    }
                },
            }
            self.memory = Memory.from_config(config)
            self.client = OpenAI()
            self.app_id = "customer-support"

        def handle_query(self, query, user_id=None):
            relevant_memories = self.memory.search(query=query, user_id=user_id)
            context = "Relevant past information:\n"
            for mem in relevant_memories:
                context += f"- {mem['text']}\n"

            full_prompt = f"{context}\nCustomer: {query}\nSupport Agent:"

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a customer support AI agent for TechGadgets.com, an online electronics store."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            answer = response.choices[0].message.content

            self.memory.add(query, user_id=user_id, metadata={"app_id": self.app_id, "role": "user"})
            self.memory.add(answer, user_id=user_id, metadata={"app_id": self.app_id, "role": "assistant"})

            return answer

        def get_memories(self, user_id=None):
            return self.memory.get_all(user_id=user_id)

        def generate_synthetic_data(self, user_id):
            today = datetime.now()
            order_date = (today - timedelta(days=10)).strftime("%B %d, %Y")
            expected_delivery = (today + timedelta(days=2)).strftime("%B %d, %Y")

            prompt = f"""Generate a detailed customer profile and order history for a TechGadgets.com customer with ID {user_id}. Include:
            1. Customer name and basic info
            2. A recent order of a high-end electronic device (placed on {order_date}, to be delivered by {expected_delivery})
            3. Order details (product, price, order number)
            4. Customer's shipping address
            5. 2-3 previous orders from the past year
            6. 2-3 customer service interactions related to these orders
            7. Any preferences or patterns in their shopping behavior

            Format the output as a JSON object."""

            response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data generation AI that creates realistic customer profiles and order histories. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
            )

            customer_data = json.loads(response.choices[0].message.content)

            # Add generated data to memory
            for key, value in customer_data.items():
                if isinstance(value, list):
                    for item in value:
                        self.memory.add(json.dumps(item), user_id=user_id, metadata={"app_id": self.app_id, "role": "system"})
                else:
                    self.memory.add(f"{key}: {json.dumps(value)}", user_id=user_id, metadata={"app_id": self.app_id, "role": "system"})

            return customer_data

    # Initialize the CustomerSupportAIAgent
    support_agent = CustomerSupportAIAgent()

    # Sidebar for customer ID and memory view
    st.sidebar.title("Enter your Customer ID:")
    previous_customer_id = st.session_state.get("previous_customer_id", None)
    customer_id = st.sidebar.text_input("Enter your Customer ID")

    if customer_id != previous_customer_id:
        st.session_state.messages = []
        st.session_state.previous_customer_id = customer_id
        st.session_state.customer_data = None

    # Add button to generate synthetic data
    if st.sidebar.button("Generate Synthetic Data"):
        if customer_id:
            with st.spinner("Generating customer data..."):
                st.session_state.customer_data = support_agent.generate_synthetic_data(customer_id)
            st.sidebar.success("Synthetic data generated successfully!")
        else:
            st.sidebar.error("Please enter a customer ID first.")

    if st.sidebar.button("View Customer Profile"):
        if st.session_state.customer_data:
            st.sidebar.json(st.session_state.customer_data)
        else:
            st.sidebar.info("No customer data generated yet. Click 'Generate Synthetic Data' first.")

    if st.sidebar.button("View Memory Info"):
        if customer_id:
            memories = support_agent.get_memories(user_id=customer_id)
            if memories:
                st.sidebar.write(f"Memory for customer **{customer_id}**:")
                for mem in memories:
                    st.sidebar.write(f"- {mem['text']}")
            else:
                st.sidebar.info("No memory found for this customer ID.")
        else:
            st.sidebar.error("Please enter a customer ID to view memory info.")

    # Initialize the chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    query = st.chat_input("How can I assist you today?")

    if query and customer_id:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Generate and display response
        answer = support_agent.handle_query(query, user_id=customer_id)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

    elif not customer_id:
        st.error("Please enter a customer ID to start the chat.")

else:
    st.warning("Please enter your OpenAI API key to use the customer support agent.")