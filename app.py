import streamlit as st
import pandas as pd
import sqlite3
import re
from google import genai  # Correct import

# Initialize Gemini API (replace with your actual API key in st.secrets)

api_key = st.secrets["gemini_api"]
client = genai.Client(api_key=api_key) # Use st.secrets

# --- Part 1: Schema Upload and SQL Generation ---

st.title("LLM-Powered Chatbot with Database Integration (Gemini)")

# Checkbox for demo information
if st.checkbox("Read Me"):
    st.write(
        """
        This app demonstrates a simple demo on LLM with database integration. 
        It uses a schema provided by [Ankit Kumar](https://github.com/ankittkp/Bank-Database-Design). 
        You may download a copy [HERE](https://drive.google.com/file/d/1scTV3Vq_qG6cRxmi4gYO_CtSispqc1gi/view?usp=sharing)
        The database is created using dummy data. Only a few entries are inserted in the database.

        **Example Queries:**

        1. List all branches.
        2. Provide a list of branches and the number of customers at each.
        3. What is the branch with the highest count of customers?
        4. Where is 'petaling jaya' branch located?
        5. Who are you?
        """
    )

# Optional user name input
user_name = st.sidebar.text_input("Your Name (optional):")

# File upload for database schema (text file)
uploaded_file = st.sidebar.file_uploader("Upload Database Schema (Text):", type="txt")

st.write("Instruction: Go to the sidebar and then upload a schema. You may use the [example](https://drive.google.com/file/d/1scTV3Vq_qG6cRxmi4gYO_CtSispqc1gi/view?usp=sharing) provided. Then ask a question about your data.")


if uploaded_file is not None:
    schema = uploaded_file.read().decode("utf-8")

    user_query = st.text_input("Ask a question about your data:")

    if user_query:
        # Agent 1: SQL Generation Agent (using Gemini)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",  # Or your chosen model
                contents=f"""You are Jane, Dr. Yu Yong Poh's PA, who is also SQL expert that generates SQLITE SQL code based on user queries and database schemas. Do not include any explanations or markdown (eg: ' ```sql '). If users ask something not related to the schema, just state 'nothing is found'
                Schema:
                {schema}

                Query: {user_query}"""
            )
            generated_text = response.text

            if not re.search(r"nothing\s+is\s+found", generated_text, re.IGNORECASE): 
                generated_sql = generated_text
                clean_sql = re.sub(r"```sql\s*(.*?)\s*```", r"\1", generated_sql)

                # Agent 2: SQL Executor Agent
                conn = sqlite3.connect('bank11.sqlite')
                cursor = conn.cursor()

                try:
                    cursor.execute(clean_sql)
                    results = cursor.fetchall()

                    st.write("Results:")
                    # st.dataframe(results) # Consider using st.dataframe for better display

                    # Agent 3: Response Generation Agent (using Gemini)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"""You are Jane, Dr. Yu Yong Poh's PA. {'Address the user as ' + user_name if user_name else ''}
                        SQL results:
                        {results}

                        Answer the user's original query: {user_query}"""
                    )
                    generated_text = response.text
                    st.write(generated_text)

                except Exception as e:
                    st.error(f"Error executing SQL: {e}")

                finally:
                    conn.close()

            else:
                # Agent 4: Fallback Response Agent (using Gemini)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"""You are Jane, Dr. Yu Yong Poh's PA. {'Address the user as ' + user_name if user_name else ''}. Referring to user query, politely tell the user that couldn't retrieve any specific information from the database.
                    SQL results:
                    {generated_text}

                    Answer the user's original query: {user_query}"""
                )
                generated_text = response.text
                st.write(generated_text)

        except Exception as e:
            st.error(f"Error calling Gemini API: {e}")
