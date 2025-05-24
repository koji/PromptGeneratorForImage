# chat_column.py
import streamlit as st
# Assuming BASE_PROMPT is imported or defined elsewhere if not passed explicitly
# from prompt import BASE_PROMPT # Or pass it as an argument


def render_chat_column(st, llm_client, model_option, max_tokens, BASE_PROMPT):
    """Renders the chat history, input, and LLM prompt generation column."""

    st.header("💬 Chat & Prompt Generation")

    # --- Display Chat History ---
    # (This part remains the same)
    for message in st.session_state.messages:
        avatar = '🤖' if message["role"] == "assistant" else '🦔'
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # --- Chat Input and LLM Call ---
    if prompt := st.chat_input("Enter topic to generate image prompt..."):
        if len(prompt.strip()) == 0:
            st.warning("Please enter a topic.", icon="⚠️")
        elif len(prompt) > 4000:  # Example length limit
            st.error("Input is too long (max 4000 chars).", icon="🚨")
        else:
            # Add user message to history and display FIRST
            # It's important to add the user message *before* sending it to the API
            st.session_state.messages.append(
                {"role": "user", "content": prompt})
            with st.chat_message("user", avatar='🦔'):
                st.markdown(prompt)

            # Generate and display assistant response
            try:
                with st.chat_message("assistant", avatar="🤖"):
                    response_placeholder = st.empty()
                    response_placeholder.markdown("Generating prompt... ▌")
                    full_response = ""

                    # --- MODIFICATION START ---
                    # Construct messages for API including the conversation history

                    # 1. Start with the system prompt
                    messages_for_api = [
                        {"role": "system", "content": BASE_PROMPT}]

                    # 2. Add all messages from the session state (history)
                    #    This now includes the user message we just added above.
                    messages_for_api.extend(st.session_state.messages)

                    # 3. Filter out any potential empty messages (just in case)
                    #    This step might be less critical now but is good practice.
                    messages_for_api = [
                        m for m in messages_for_api if m.get("content")]
                    # --- MODIFICATION END ---

                    stream_kwargs = {
                        "model": model_option,
                        "messages": messages_for_api,  # <--- Now contains history!
                        "max_tokens": max_tokens,
                        "stream": True,
                    }
                    # Using OpenAI client for chat completions
                    response_stream = llm_client.chat.completions.create(
                        **stream_kwargs)

                    # --- (Rest of the streaming and response handling code remains the same) ---
                    for chunk in response_stream:
                        chunk_content = ""
                        try:
                            if chunk.choices and chunk.choices[0].delta:
                                chunk_content = chunk.choices[0].delta.content or ""
                        except (AttributeError, IndexError):
                            chunk_content = ""  # Handle potential errors gracefully

                        if chunk_content:
                            full_response += chunk_content
                            response_placeholder.markdown(full_response + "▌")

                    # Final response display
                    response_placeholder.markdown(full_response)

                # Add assistant response to history
                # Check if the last message isn't already the assistant's response to avoid duplicates if rerun happens unexpectedly
                if not st.session_state.messages or st.session_state.messages[-1]['role'] != 'assistant':
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response})
                elif st.session_state.messages[-1]['role'] == 'assistant':
                    # If last message is assistant, update it (useful if streaming was interrupted/retried)
                    st.session_state.messages[-1]['content'] = full_response

                # No longer updating image prompt text area here (based on previous request)

                # Rerun might still cause subtle issues with message duplication if not handled carefully,
                # The check above helps mitigate this. Consider removing rerun if it causes problems.
                # st.rerun() # Keeping rerun commented out for now based on potential issues

            except Exception as e:
                st.error(
                    f"Error during LLM response generation: {str(e)}", icon="🚨")
                # Clean up potentially failed message
                # Ensure we only pop if the *last* message is the user's (meaning the assistant failed)
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    # Maybe add a placeholder error message for the assistant instead of popping user?
                    # For now, let's not pop the user's message. The error message itself indicates failure.
                    pass
                # Or if the assistant message was partially added:
                elif st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and not full_response:
                    st.session_state.messages.pop()
