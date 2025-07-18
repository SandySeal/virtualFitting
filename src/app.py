
import streamlit as st
from PIL import Image, ImageOps
import os

# --- Configuration ---
st.set_page_config(
    page_title="Virtual Fitting Room",
    page_icon=":shirt:",
    layout="wide"
)

# --- Helper Functions ---
def get_image_path(image_name):
    """Constructs the full path for an image in the 'images' directory."""
    return os.path.join("images", image_name)

def load_image(image_path, size=None):
    """Loads an image from a file path and optionally resizes it."""
    try:
        img = Image.open(image_path)
        if size:
            img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        return img
    except FileNotFoundError:
        st.error(f"Error: Image not found at {image_path}")
        return None

def overlay_image(background_img, overlay_img, position=(0, 0)):
    """Overlays one image on top of another at a specified position."""
    # Create a copy of the background to avoid modifying the original
    background = background_img.copy()
    # Ensure the overlay image has an alpha channel for transparency
    overlay_img = overlay_img.convert("RGBA")
    # Paste the overlay onto the background using the alpha channel as a mask
    background.paste(overlay_img, position, overlay_img)
    return background

# --- Image Assets ---
# Create a directory for images if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# --- UI Layout ---
st.title("Virtual Fitting Room")
st.markdown("""
Welcome to the Virtual Fitting Room! Upload a photo of yourself and select a clothing item to see how it looks.
""")

col1, col2 = st.columns(2)

with col1:
    st.header("Your Photo")

    # --- Avatar Handling ---
    AVATAR_DIR = os.path.join("images", "avatars")
    if not os.path.exists(AVATAR_DIR):
        os.makedirs(AVATAR_DIR)
    
    AVATAR_PATH = os.path.join(AVATAR_DIR, "avatar.png")

    # Check for a saved avatar first
    if 'user_image_path' not in st.session_state and os.path.exists(AVATAR_PATH):
        st.session_state.user_image_path = AVATAR_PATH

    # Uploader for new photos
    uploaded_file = st.file_uploader("Choose a new photo or use your saved avatar...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # When a new file is uploaded, it becomes the current image
        user_image_path = get_image_path(uploaded_file.name)
        with open(user_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.user_image_path = user_image_path
    
    # Display the current user image (either avatar or newly uploaded)
    if 'user_image_path' in st.session_state:
        user_image = load_image(st.session_state.user_image_path)
        if user_image:
            st.image(user_image, caption="This is you!", use_column_width=True)
            
            # --- Save Avatar Button ---
            if st.button("Save as My Avatar"):
                # Save the currently displayed image to the avatar path
                user_image.save(AVATAR_PATH, "PNG")
                st.success("Avatar saved! It will be loaded automatically next time.")

with col2:
    st.header("Choose Your Style")
    
    # --- Dynamic Clothing Loader ---
    def load_clothing_data():
        """Loads clothing data from the CSV file."""
        try:
            import pandas as pd
            df = pd.read_csv("clothing_data.csv")
            return {row['name']: row['image_file'] for index, row in df.iterrows()}
        except FileNotFoundError:
            st.error("Error: clothing_data.csv not found.")
            return {}
        except Exception as e:
            st.error(f"An error occurred while loading clothing data: {e}")
            return {}

    clothing_options = load_clothing_data()

    if clothing_options:
        selected_clothing_name = st.selectbox("Select a piece of clothing:", list(clothing_options.keys()))
        
        if selected_clothing_name:
            clothing_image_path = os.path.join("images", "clothing", clothing_options[selected_clothing_name])
            clothing_image = load_image(clothing_image_path)
            if clothing_image:
                st.image(clothing_image, caption=f"Selected: {selected_clothing_name}", use_container_width =True)
    else:
        st.warning("No clothing items found. Please add items to clothing_data.csv")


# --- Fitting Area ---
if 'user_image_path' in st.session_state and selected_clothing_name:
    st.header("Your New Look!")
    
    # Load images again to ensure we have fresh copies
    user_image = load_image(st.session_state.user_image_path)
    clothing_image_path = os.path.join("images", "clothing", clothing_options[selected_clothing_name])
    clothing_image = load_image(clothing_image_path)

    if user_image and clothing_image:
        # --- Interactive Overlay Logic ---
        user_width, user_height = user_image.size

        st.sidebar.header("Adjust Clothing")
        scale = st.sidebar.slider("Size", 0.1, 5.0, 1.0, 0.05)
        x_offset = st.sidebar.slider("Horizontal Position", -user_width // 2, user_width // 2, 0)
        y_offset = st.sidebar.slider("Vertical Position", -user_height // 2, user_height // 2, 0)

        # Resize clothing based on scale
        clothing_width = int(clothing_image.width * scale)
        clothing_height = int(clothing_image.height * scale)
        clothing_image_resized = clothing_image.resize((clothing_width, clothing_height), Image.Resampling.LANCZOS)
        
        # Calculate position based on offsets
        position_x = (user_width - clothing_width) // 2 + x_offset
        position_y = (user_height - clothing_height) // 2 + y_offset
        
        # Create the final image
        final_image = overlay_image(user_image, clothing_image_resized, (position_x, position_y))
        
        st.image(final_image, caption="Here's your virtual try-on!", use_container_width=True)

        # --- Download Button ---
        # To download the image, we need to convert it to bytes
        from io import BytesIO
        buf = BytesIO()
        final_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Download Your New Look",
            data=byte_im,
            file_name="virtual_look.png",
            mime="image/png"
        )

# --- Instructions and Tips ---
st.sidebar.title("How to Use")
st.sidebar.info("""
1.  **Upload Your Photo:** Click the 'Browse files' button and select a clear, front-facing photo of yourself.
2.  **Choose Clothing:** Select an item from the dropdown menu to see it on your photo.
3.  **View & Download:** See the result in the 'Your New Look!' section and download it if you like.
""")

st.sidebar.title("About")
st.sidebar.info("This is a simple virtual fitting room application built with Streamlit and Python.")

