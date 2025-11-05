import streamlit as st
from rembg import remove
from PIL import Image
import io
import zipfile

st.set_page_config(
    page_title="Background Remover",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Background Remover")
st.write("Upload images to automatically remove backgrounds with advanced options")

tab1, tab2 = st.tabs(["Single Image", "Batch Processing"])

with tab1:
    st.subheader("Process a Single Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png", "webp"],
        help="Supported formats: JPG, JPEG, PNG, WebP (animated formats not supported)",
        key="single"
    )
    
    if uploaded_file is not None:
        resize_width = 800
        resize_height = 600
        crop_width = 500
        crop_height = 500
        alpha_fg_threshold = 240
        alpha_bg_threshold = 10
        alpha_erode_size = 10
        bg_color = "#FFFFFF"
        
        with st.expander("⚙️ Advanced Settings", expanded=False):
            col_set1, col_set2 = st.columns(2)
            
            with col_set1:
                st.write("**Preprocessing**")
                resize_image = st.checkbox("Resize image", value=False)
                if resize_image:
                    resize_width = st.number_input("Width (pixels)", min_value=100, max_value=4000, value=800)
                    resize_height = st.number_input("Height (pixels)", min_value=100, max_value=4000, value=600)
                
                crop_image = st.checkbox("Crop image", value=False)
                if crop_image:
                    st.info("Crop settings will be applied from center")
                    crop_width = st.number_input("Crop Width (pixels)", min_value=50, max_value=4000, value=500)
                    crop_height = st.number_input("Crop Height (pixels)", min_value=50, max_value=4000, value=500)
            
            with col_set2:
                st.write("**Background Removal Settings**")
                use_alpha_matting = st.checkbox("Use alpha matting (better edges)", value=False)
                
                if use_alpha_matting:
                    st.write("Fine-tune alpha matting:")
                    alpha_fg_threshold = st.slider(
                        "Foreground threshold",
                        min_value=0,
                        max_value=255,
                        value=240,
                        help="Higher values = more aggressive foreground detection"
                    )
                    alpha_bg_threshold = st.slider(
                        "Background threshold",
                        min_value=0,
                        max_value=255,
                        value=10,
                        help="Lower values = more aggressive background removal"
                    )
                    alpha_erode_size = st.slider(
                        "Erode size",
                        min_value=0,
                        max_value=30,
                        value=10,
                        help="Edge refinement strength"
                    )
                
                replace_bg = st.checkbox("Replace transparent background with color", value=False)
                if replace_bg:
                    bg_color = st.color_picker("Background color", value="#FFFFFF")
                
                output_format = st.selectbox("Output format", ["PNG", "JPEG", "WebP"], index=0)
        
        col1, col2 = st.columns(2)
        
        try:
            with col1:
                st.subheader("Original Image")
                original_image = Image.open(uploaded_file)
                
                if getattr(original_image, 'n_frames', 1) > 1:
                    st.warning("⚠️ Animated images are not supported. Only the first frame will be processed.")
                    original_image.seek(0)
                
                processed_input = original_image.copy()
            
            if resize_image:
                processed_input = processed_input.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
            
            if crop_image:
                width, height = processed_input.size
                left = max(0, (width - crop_width) // 2)
                top = max(0, (height - crop_height) // 2)
                right = min(width, left + crop_width)
                bottom = min(height, top + crop_height)
                processed_input = processed_input.crop((left, top, right, bottom))
            
                st.image(processed_input, use_container_width=True)
            
            with col2:
                st.subheader("Background Removed")
                
                with st.spinner("Removing background..."):
                    buf = io.BytesIO()
                    processed_input.save(buf, format="PNG")
                    buf.seek(0)
                    input_data = buf.read()
                    
                    if use_alpha_matting:
                        output_data = remove(
                            input_data,
                            alpha_matting=True,
                            alpha_matting_foreground_threshold=alpha_fg_threshold,
                            alpha_matting_background_threshold=alpha_bg_threshold,
                            alpha_matting_erode_size=alpha_erode_size
                        )
                    else:
                        output_data = remove(input_data)
                    
                    output_image = Image.open(io.BytesIO(output_data))  # type: ignore[arg-type]
                    
                    if replace_bg:
                        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        background = Image.new('RGB', output_image.size, bg_rgb)
                        if output_image.mode == 'RGBA':
                            background.paste(output_image, mask=output_image.split()[3])
                        else:
                            background.paste(output_image)
                        output_image = background
                    
                    st.image(output_image, use_container_width=True)
                    
                    download_buf = io.BytesIO()
                    if output_format == "PNG":
                        output_image.save(download_buf, format="PNG")
                        mime_type = "image/png"
                        file_ext = "png"
                    elif output_format == "JPEG":
                        if output_image.mode == 'RGBA':
                            output_image = output_image.convert('RGB')
                        output_image.save(download_buf, format="JPEG", quality=95)
                        mime_type = "image/jpeg"
                        file_ext = "jpg"
                    else:
                        output_image.save(download_buf, format="WebP", quality=95)
                        mime_type = "image/webp"
                        file_ext = "webp"
                    
                    download_buf.seek(0)
                    
                    st.download_button(
                        label=f"⬇️ Download Image ({output_format})",
                        data=download_buf,
                        file_name=f"removed_background.{file_ext}",
                        mime=mime_type,
                        use_container_width=True
                    )
        except Exception as e:
            st.error(f"❌ Error processing image: {str(e)}")
            st.info("Please upload a valid image file (JPG, JPEG, PNG, or WebP)")
    else:
        st.info("👆 Upload an image to get started")

with tab2:
    st.subheader("Process Multiple Images")
    
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Upload multiple images to process them all at once (animated formats not supported)",
        key="batch"
    )
    
    if uploaded_files:
        batch_alpha_fg = 240
        batch_alpha_bg = 10
        batch_alpha_erode = 10
        batch_bg_color = "#FFFFFF"
        
        with st.expander("⚙️ Batch Settings", expanded=False):
            batch_use_alpha = st.checkbox("Use alpha matting for all images", value=False, key="batch_alpha")
            
            if batch_use_alpha:
                st.write("Alpha matting settings:")
                batch_alpha_fg = st.slider(
                    "Foreground threshold",
                    min_value=0,
                    max_value=255,
                    value=240,
                    key="batch_fg"
                )
                batch_alpha_bg = st.slider(
                    "Background threshold",
                    min_value=0,
                    max_value=255,
                    value=10,
                    key="batch_bg_thresh"
                )
                batch_alpha_erode = st.slider(
                    "Erode size",
                    min_value=0,
                    max_value=30,
                    value=10,
                    key="batch_erode"
                )
            
            batch_replace_bg = st.checkbox("Replace backgrounds with color", value=False, key="batch_bg")
            if batch_replace_bg:
                batch_bg_color = st.color_picker("Background color", value="#FFFFFF", key="batch_color")
            batch_output_format = st.selectbox("Output format", ["PNG", "JPEG", "WebP"], index=0, key="batch_format")
        
        st.write(f"**{len(uploaded_files)} images uploaded**")
        
        if st.button("🚀 Process All Images", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_images_data = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                try:
                    original_image = Image.open(uploaded_file)
                    
                    if getattr(original_image, 'n_frames', 1) > 1:
                        st.warning(f"⚠️ {uploaded_file.name} is animated. Only processing first frame.")
                        original_image.seek(0)
                    
                    buf = io.BytesIO()
                    original_image.save(buf, format="PNG")
                    buf.seek(0)
                    input_data = buf.read()
                    
                    if batch_use_alpha:
                        output_data = remove(
                            input_data,
                            alpha_matting=True,
                            alpha_matting_foreground_threshold=batch_alpha_fg,
                            alpha_matting_background_threshold=batch_alpha_bg,
                            alpha_matting_erode_size=batch_alpha_erode
                        )
                    else:
                        output_data = remove(input_data)
                    
                    output_image = Image.open(io.BytesIO(output_data))  # type: ignore[arg-type]
                    
                    if batch_replace_bg:
                        bg_rgb = tuple(int(batch_bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                        background = Image.new('RGB', output_image.size, bg_rgb)
                        if output_image.mode == 'RGBA':
                            background.paste(output_image, mask=output_image.split()[3])
                        else:
                            background.paste(output_image)
                        output_image = background
                    
                    img_bytes_for_zip = io.BytesIO()
                    img_bytes_for_preview = io.BytesIO()
                    
                    if batch_output_format == "PNG":
                        output_image.save(img_bytes_for_zip, format="PNG")
                        output_image.save(img_bytes_for_preview, format="PNG")
                        file_ext = "png"
                    elif batch_output_format == "JPEG":
                        output_copy_zip = output_image.copy()
                        output_copy_preview = output_image.copy()
                        if output_copy_zip.mode == 'RGBA':
                            output_copy_zip = output_copy_zip.convert('RGB')
                        if output_copy_preview.mode == 'RGBA':
                            output_copy_preview = output_copy_preview.convert('RGB')
                        output_copy_zip.save(img_bytes_for_zip, format="JPEG", quality=95)
                        output_copy_preview.save(img_bytes_for_preview, format="PNG")
                        file_ext = "jpg"
                    else:
                        output_image.save(img_bytes_for_zip, format="WebP", quality=95)
                        output_image.save(img_bytes_for_preview, format="PNG")
                        file_ext = "webp"
                    
                    img_bytes_for_zip.seek(0)
                    img_bytes_for_preview.seek(0)
                    
                    processed_images_data.append({
                        'name': uploaded_file.name,
                        'zip_bytes': img_bytes_for_zip.read(),
                        'preview_image': Image.open(img_bytes_for_preview),
                        'file_ext': file_ext
                    })
                    
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            status_text.text("✅ All images processed!")
            
            if processed_images_data:
                st.subheader("Preview Processed Images")
                cols = st.columns(min(3, len(processed_images_data)))
                for idx, img_data in enumerate(processed_images_data):
                    with cols[idx % 3]:
                        st.image(img_data['preview_image'], caption=img_data['name'], use_container_width=True)
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for img_data in processed_images_data:
                        base_name = img_data['name'].rsplit('.', 1)[0]
                        zip_file.writestr(
                            f"{base_name}_no_bg.{img_data['file_ext']}",
                            img_data['zip_bytes']
                        )
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label=f"📦 Download All Images (ZIP)",
                    data=zip_buffer,
                    file_name="processed_images.zip",
                    mime="application/zip",
                    use_container_width=True
                )
    else:
        st.info("👆 Upload multiple images to process them in batch")
