# image_column.py
import streamlit as st
import utils  # Import utils to use the generation function
import time  # Import time for unique keys if needed


def render_image_column(st, image_client):
    """Renders the image prompt editing and generation column."""

    st.header("🖼️ Image Generation")

    if not image_client:
        st.warning(
            "Together API Key not configured. Cannot generate images.", icon="⚠️")
        # Keep the text area visible even if client is missing

    # --- Editable Text Area for Image Prompt ---
    # This part remains mostly the same
    prompt_for_image_area = st.text_area(
        "Editable Image Prompt:",
        value=st.session_state.get(
            "current_image_prompt_text", ""),  # Use .get for safety
        height=150,  # Adjusted height slightly
        key="image_prompt_input_area",  # Key is crucial for statefulness
        help="Edit or enter the prompt for image generation."
    )
    # Update session state based on text area input (Streamlit does this automatically via key)
    # Make sure this state is explicitly updated IF the text area content changes
    # Streamlit handles this via the key, but we read it directly when needed.
    st.session_state.current_image_prompt_text = prompt_for_image_area

    # --- Generate Button ---
    is_disabled = (not image_client) or (
        len(st.session_state.current_image_prompt_text.strip()) == 0)

    if st.button("Generate Image ✨", key="generate_image_main_col", use_container_width=True,
                 disabled=is_disabled):
        prompt_to_use = st.session_state.current_image_prompt_text
        if len(prompt_to_use.strip()) > 0:  # Double check prompt isn't empty
            with st.spinner("Generating image via Together API..."):
                image_bytes = utils.generate_image_from_prompt(
                    image_client, prompt_to_use)

            if image_bytes:
                # --- MODIFICATION START ---
                # Create a dictionary holding the prompt and image bytes
                new_image_data = {
                    "prompt": prompt_to_use,
                    "image": image_bytes
                }
                # Prepend the new image data to the list (newest first)
                st.session_state.generated_images_list.insert(
                    0, new_image_data)
                # --- MODIFICATION END ---
                # No need to set latest_generated_image anymore
                # Show success message immediately
                st.success("Image generated!")
                # Rerun to update the display list below
                st.rerun()
            else:
                st.error("Image generation failed.")
                # No need to clear latest_generated_image
        else:
            st.warning(
                "Please enter a prompt in the text area above before generating.", icon="⚠️")

    # --- Display Generated Images (Below Button) ---
    st.markdown("---")  # Add a visual separator

    if not st.session_state.generated_images_list:
        if image_client and len(st.session_state.current_image_prompt_text.strip()) > 0:
            st.markdown(
                "Click the 'Generate Image' button above to create an image.")
        elif image_client:
            st.markdown("Enter a prompt above and click 'Generate Image'.")
        # If no client, the warning at the top handles it.

    else:
        st.subheader("Generated Images")
        # Iterate through the list and display each image with its prompt
        for index, image_data in enumerate(st.session_state.generated_images_list):
            st.image(
                image_data["image"],
                use_container_width=True
            )
            # Display the prompt used for this specific image
            st.caption(f"Prompt: {image_data['prompt']}")
            st.download_button(
                label="Download Image 💾",
                data=image_data["image"],
                # More unique filename
                file_name=f"generated_image_{index}_{int(time.time())}.png",
                mime="image/png",
                # Ensure unique key for each button
                key=f"dl_img_{index}_{int(time.time())}",
                use_container_width=True
            )
            st.divider()  # Add space between images

    # --- Old Display Logic (Commented out / Removed) ---
    # if st.session_state.get("latest_generated_image"):
    #     st.success("Image generated!")
    #     st.image(st.session_state.latest_generated_image,
    #              caption="Latest Generated Image",
    #              use_container_width=True)
    #     st.download_button(...)
    # elif not is_disabled:
    #     st.markdown(...)
    # elif len(...) == 0 and image_client:
    #      st.markdown(...)
