import streamlit as st
from streamlit_image_comparison import image_comparison
import time
from PIL import Image
from ui_components.methods.common_methods import delete_frame, drawing_mode, promote_image_variant, save_uploaded_image, \
    create_timings_row_at_frame_number, move_frame, calculate_desired_duration_of_individual_clip, \
            calculate_desired_duration_of_individual_clip, apply_image_transformations, \
                ai_frame_editing_element, clone_styling_settings, zoom_inputs,add_key_frame
from ui_components.methods.file_methods import generate_pil_image, save_or_host_file
from ui_components.methods.ml_methods import trigger_restyling_process
from ui_components.methods.video_methods import create_or_get_single_preview_video
from ui_components.widgets.cropping_element import manual_cropping_element, precision_cropping_element
from ui_components.widgets.frame_clip_generation_elements import current_individual_clip_element, current_preview_video_element, update_animation_style_element
from ui_components.widgets.frame_time_selector import single_frame_time_selector, update_frame_time, single_frame_time_duration_setter
from ui_components.widgets.frame_selector import frame_selector_widget
from ui_components.widgets.image_carousal import display_image
from ui_components.widgets.prompt_finder import prompt_finder_element
from ui_components.widgets.add_key_frame_element import add_key_frame_element
from ui_components.widgets.styling_element import styling_element
from ui_components.widgets.compare_to_other_variants import compare_to_other_variants
from ui_components.widgets.animation_style_element import animation_style_element
from streamlit_option_menu import option_menu
from utils import st_memory


import math
from ui_components.constants import WorkflowStageType
from utils.constants import ImageStage

from utils.data_repo.data_repo import DataRepo


def frame_styling_page(mainheader2, project_uuid: str):
    data_repo = DataRepo()

    timing_details = data_repo.get_timing_list_from_project(project_uuid)
    
    project_settings = data_repo.get_project_setting(project_uuid)

    if "strength" not in st.session_state:
        st.session_state['strength'] = project_settings.default_strength
        st.session_state['prompt_value'] = project_settings.default_prompt
        st.session_state['model'] = project_settings.default_model.uuid
        st.session_state['custom_pipeline'] = project_settings.default_custom_pipeline
        st.session_state['negative_prompt_value'] = project_settings.default_negative_prompt
        st.session_state['guidance_scale'] = project_settings.default_guidance_scale
        st.session_state['seed'] = project_settings.default_seed
        st.session_state['num_inference_steps'] = project_settings.default_num_inference_steps
        st.session_state['transformation_stage'] = project_settings.default_stage
        st.session_state['show_comparison'] = "Don't show"
    
    if "current_frame_uuid" not in st.session_state:
        timing = data_repo.get_timing_list_from_project(project_uuid)[0]
        st.session_state['current_frame_uuid'] = timing.uuid
    
    
    if 'frame_styling_view_type' not in st.session_state:
        st.session_state['frame_styling_view_type'] = "Individual View"
        st.session_state['frame_styling_view_type_index'] = 0


    if st.session_state['change_view_type'] == True:  
        st.session_state['change_view_type'] = False
        # round down st.session_state['which_image']to nearest 10

    
    if st.session_state['frame_styling_view_type'] == "List View":
        st.markdown(
            f"#### :red[{st.session_state['main_view_type']}] > **:green[{st.session_state['frame_styling_view_type']}]** > :orange[{st.session_state['page']}]")
    else:
        st.markdown(
            f"#### :red[{st.session_state['main_view_type']}] > **:green[{st.session_state['frame_styling_view_type']}]** > :orange[{st.session_state['page']}] > :blue[Frame #{st.session_state['current_frame_index']}]")

    project_settings = data_repo.get_project_setting(project_uuid)

    if st.session_state['frame_styling_view_type'] == "Individual View":
        with st.sidebar:
            frame_selector_widget()
                
        if st.session_state['page'] == "Motion":




            idx = st.session_state['current_frame_index'] - 1
                                    
            st.session_state['show_comparison'] = st_memory.radio("Show:", options=["Other Variants", "Preview Video in Context"], horizontal=True, project_settings=project_settings, key="show_comparison_radio_motion")

            if st.session_state['show_comparison'] == "Other Variants":
                compare_to_other_variants(timing_details, project_uuid, data_repo,stage="Motion")

            elif st.session_state['show_comparison'] == "Preview Video in Context":
                current_preview_video_element(st.session_state['current_frame_uuid'])
            
            

            st.markdown("***")

            with st.expander("🎬 Choose Animation Style & Create Variants", expanded=True):

                update_animation_style_element(st.session_state['current_frame_uuid'], horizontal=True)

                animation_style_element(st.session_state['current_frame_uuid'], project_settings)


        elif st.session_state['page'] == "Styling":
            # carousal_of_images_element(project_uuid, stage=WorkflowStageType.STYLED.value)
            comparison_values = [
                "Other Variants", "Source Frame", "Previous & Next Frame", "None"]
            
            st.session_state['show_comparison'] = st_memory.radio("Show comparison to:", options=comparison_values, horizontal=True, project_settings=project_settings, key="show_comparison_radio")
            

            if st.session_state['show_comparison'] == "Other Variants":
                compare_to_other_variants(timing_details, project_uuid, data_repo,stage="Styling")
                
            elif st.session_state['show_comparison'] == "Source Frame":
                if timing_details[st.session_state['current_frame_index']- 1].primary_image:
                    img2 = timing_details[st.session_state['current_frame_index'] - 1].primary_image_location
                else:
                    img2 = 'https://i.ibb.co/GHVfjP0/Image-Not-Yet-Created.png'
                
                img1 = timing_details[st.session_state['current_frame_index'] - 1].source_image.location if timing_details[st.session_state['current_frame_index'] - 1].source_image else 'https://i.ibb.co/GHVfjP0/Image-Not-Yet-Created.png'
                
                image_comparison(starting_position=50,
                                    img1=img1,
                                    img2=img2, make_responsive=False, label1=WorkflowStageType.SOURCE.value, label2=WorkflowStageType.STYLED.value)
                
            elif st.session_state['show_comparison'] == "Previous & Next Frame":

                mainimages1, mainimages2, mainimages3 = st.columns([1, 1, 1])

                with mainimages1:
                    if st.session_state['current_frame_index'] - 2 >= 0:
                        previous_image = data_repo.get_timing_from_frame_number(project_uuid, frame_number=st.session_state['current_frame_index'] - 2)
                        st.info(f"Previous image")
                        display_image(
                            timing_uuid=previous_image.uuid, stage=WorkflowStageType.STYLED.value, clickable=False)

                        if st.button(f"Preview Interpolation From #{st.session_state['current_frame_index']-1} to #{st.session_state['current_frame_index']}", key=f"Preview Interpolation From #{st.session_state['current_frame_index']-1} to #{st.session_state['current_frame_index']}", use_container_width=True):
                            prev_frame_timing = data_repo.get_prev_timing(st.session_state['current_frame_uuid'])
                            create_or_get_single_preview_video(prev_frame_timing.uuid)
                            prev_frame_timing = data_repo.get_timing_from_uuid(prev_frame_timing.uuid)
                            st.video(prev_frame_timing.timed_clip.location)

                with mainimages2:
                    st.success(f"Current image")
                    display_image(
                        timing_uuid=st.session_state['current_frame_uuid'], stage=WorkflowStageType.STYLED.value, clickable=False)

                with mainimages3:
                    if st.session_state['current_frame_index'] + 1 <= len(timing_details):
                        next_image = data_repo.get_timing_from_frame_number(project_uuid, frame_number=st.session_state['current_frame_index'])
                        st.info(f"Next image")
                        display_image(timing_uuid=next_image.uuid, stage=WorkflowStageType.STYLED.value, clickable=False)

                        if st.button(f"Preview Interpolation From #{st.session_state['current_frame_index']} to #{st.session_state['current_frame_index']+1}", key=f"Preview Interpolation From #{st.session_state['current_frame_index']} to #{st.session_state['current_frame_index']+1}", use_container_width=True):
                            create_or_get_single_preview_video(
                                st.session_state['current_frame_uuid'])
                            current_frame = data_repo.get_timing_from_uuid(st.session_state['current_frame_uuid'])
                            st.video(current_frame.timed_clip.location)

            elif st.session_state['show_comparison'] == "None":
                display_image(
                    timing_uuid=st.session_state['current_frame_uuid'], stage=WorkflowStageType.STYLED.value, clickable=False)

            st.markdown("***")

            if 'styling_view_index' not in st.session_state:
                st.session_state['styling_view_index'] = 0
                st.session_state['change_styling_view_type'] = False
                
            styling_views = ["Generate Variants", "Crop, Move & Rotate Image", "Inpainting & BG Removal","Draw On Image"]
                                                                                                    
            st.session_state['styling_view'] = option_menu(None, styling_views, icons=['magic', 'crop', "paint-bucket", 'pencil'], menu_icon="cast", default_index=st.session_state['styling_view_index'], key="styling_view_selector", orientation="horizontal", styles={
                                                                    "nav-link": {"font-size": "15px", "margin": "0px", "--hover-color": "#eee"}, "nav-link-selected": {"background-color": "#66A9BE"}})
                                    
            if st.session_state['styling_view_index'] != styling_views.index(st.session_state['styling_view']):
                st.session_state['styling_view_index'] = styling_views.index(st.session_state['styling_view'])                                                       

            if st.session_state['styling_view'] == "Generate Variants":

                with st.expander("🛠️ Generate Variants + Prompt Settings", expanded=True):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        styling_element(st.session_state['current_frame_uuid'], view_type="Single")
                    with col2:
                        detail1, detail2 = st.columns([1, 1])
                        with detail1:
                            st.session_state['individual_number_of_variants'] = st.number_input(
                                f"How many variants?", min_value=1, max_value=100, key=f"number_of_variants_{st.session_state['current_frame_index']}")

                        with detail2:
                            st.write("")
                            st.write("")

                            # TODO: add custom model validation such for sd img2img the value of strength can only be 1
                            if st.button(f"Generate variants", key=f"new_variations_{st.session_state['current_frame_index']}", help="This will generate new variants based on the settings to the left."):
                                for i in range(0, st.session_state['individual_number_of_variants']):
                                    trigger_restyling_process(
                                        st.session_state['current_frame_uuid'], 
                                        st.session_state['model'], 
                                        st.session_state['prompt'], 
                                        st.session_state['strength'], 
                                        st.session_state['negative_prompt'], 
                                        st.session_state['guidance_scale'], 
                                        st.session_state['seed'], 
                                        st.session_state['num_inference_steps'], 
                                        st.session_state['transformation_stage'], 
                                        st.session_state["promote_new_generation"], 
                                        st.session_state['custom_models'], 
                                        st.session_state['adapter_type'], 
                                        True, 
                                        st.session_state['low_threshold'], 
                                        st.session_state['high_threshold']
                                    )
                                st.experimental_rerun()

                        st.markdown("***")

                        st.info(
                            "You can restyle multiple frames at once in the List view.")

                        st.markdown("***")

                        open_copier = st.checkbox(
                            "Copy styling settings from another frame")
                        if open_copier is True:
                            copy1, copy2 = st.columns([1, 1])
                            with copy1:
                                which_frame_to_copy_from = st.number_input("Which frame would you like to copy styling settings from?", min_value=1, max_value=len(
                                    timing_details), value=st.session_state['current_frame_index'], step=1)
                                if st.button("Copy styling settings from this frame"):
                                    clone_styling_settings(which_frame_to_copy_from - 1, st.session_state['current_frame_uuid'])
                                    st.experimental_rerun()

                            with copy2:
                                display_image(
                                    idx=which_frame_to_copy_from, stage=WorkflowStageType.STYLED.value, clickable=False, timing_details=timing_details)
                                st.caption("Prompt:")
                                st.caption(
                                    timing_details[which_frame_to_copy_from].prompt)
                                if timing_details[which_frame_to_copy_from].model is not None:
                                    st.caption("Model:")
                                    st.caption(
                                        timing_details[which_frame_to_copy_from].model.name)
                                    
                with st.expander("🔍 Prompt Finder"):
                    prompt_finder_element(project_uuid)
            
            elif st.session_state['styling_view'] == "Crop, Move & Rotate Image":
                with st.expander("🤏 Crop, Move & Rotate Image", expanded=True):
                    
                    selector1, selector2, selector3 = st.columns([1, 1, 1])
                    with selector1:
                        which_stage = st.radio("Which stage to work on?", ["Styled Key Frame", "Unedited Key Frame"], key="which_stage", horizontal=True)
                    with selector2:
                        how_to_crop = st_memory.radio("How to crop:", options=["Precision Cropping","Manual Cropping"], project_settings=project_settings, key="how_to_crop",horizontal=True)
                                            
                    if which_stage == "Styled Key Frame":
                        stage_name = WorkflowStageType.STYLED.value
                    elif which_stage == "Unedited Key Frame":
                        stage_name = WorkflowStageType.SOURCE.value
                                            
                    if how_to_crop == "Manual Cropping":
                        manual_cropping_element(stage_name, st.session_state['current_frame_uuid'])
                    elif how_to_crop == "Precision Cropping":
                        precision_cropping_element(stage_name, project_uuid)
                                
            elif st.session_state['styling_view'] == "Inpainting & BG Removal":

                with st.expander("🌌 Inpainting, Background Removal & More", expanded=True):
                    
                    which_stage_to_inpaint = st.radio("Which stage to work on?", ["Styled Key Frame", "Unedited Key Frame"], horizontal=True, key="which_stage_inpainting")
                    if which_stage_to_inpaint == "Styled Key Frame":
                        inpainting_stage = WorkflowStageType.STYLED.value
                    elif which_stage_to_inpaint == "Unedited Key Frame":
                        inpainting_stage = WorkflowStageType.SOURCE.value
                    
                    ai_frame_editing_element(st.session_state['current_frame_uuid'], inpainting_stage)

            elif st.session_state['styling_view'] == "Draw On Image":
                with st.expander("📝 Draw On Image", expanded=True):

                    which_stage_to_draw_on = st.radio("Which stage to work on?", ["Styled Key Frame", "Unedited Key Frame"], horizontal=True, key="which_stage_drawing")
                    if which_stage_to_draw_on == "Styled Key Frame":
                        drawing_mode(timing_details,project_settings,project_uuid, stage=WorkflowStageType.STYLED.value)
                    elif which_stage_to_draw_on == "Unedited Key Frame":
                        drawing_mode(timing_details,project_settings,project_uuid, stage=WorkflowStageType.SOURCE.value)
                        

    elif st.session_state['frame_styling_view_type'] == "List View":
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 1
        
        if not('index_of_current_page' in st.session_state and st.session_state['index_of_current_page']):
            st.session_state['index_of_current_page'] = 1

        items_per_page = 10
        num_pages = math.ceil(len(timing_details) / items_per_page) + 1
        
        st.markdown("---")

        header_col_1, header_col_2, header_col_3 = st.columns([1, 5, 1])
        with header_col_1:
            st.session_state['current_page'] = st.radio("Select Page:", options=range(
                1, num_pages), horizontal=True, index=st.session_state['index_of_current_page'] - 1, key="page_selection_radio")
        with header_col_3:
            shift_frames_setting = st.toggle("Shift Frames", help="If set to True, this will shift the frames after your adjustment forward or backwards.")
        if st.session_state['current_page'] != st.session_state['index_of_current_page']:
            st.session_state['index_of_current_page'] = st.session_state['current_page']
            st.experimental_rerun()

        st.markdown("---")

        start_index = (st.session_state['current_page'] - 1) * items_per_page         
        end_index = min(start_index + items_per_page,
                        len(timing_details))

        
                                                                                
        if st.session_state['page'] == "Styling":
            with st.sidebar:                            
                styling_element(st.session_state['current_frame_uuid'], view_type="List")

            timing_details = data_repo.get_timing_list_from_project(project_uuid)

            for i in range(start_index, end_index):

                
                display_number = i + 1
                                       
                st.subheader(f"Frame {display_number}")
                image1, image2, image3 = st.columns([2, 3, 2])

                with image1:
                    display_image(
                        timing_uuid=timing_details[i].uuid, stage=WorkflowStageType.SOURCE.value, clickable=False)

                with image2:
                    display_image(
                        timing_uuid=timing_details[i].uuid, stage=WorkflowStageType.STYLED.value, clickable=False)

                with image3:
                    time1, time2 = st.columns([1, 1])
                    with time1:
                        single_frame_time_selector(timing_details[i].uuid, 'sidebar', shift_frames=shift_frames_setting)
                        single_frame_time_duration_setter(timing_details[i].uuid,'sidebar',shift_frames=shift_frames_setting)

                    with time2:
                        st.write("") 

                    if st.button(f"Jump to single frame view for #{display_number}"):
                        st.session_state['prev_frame_index'] = display_number
                        st.session_state['current_frame_uuid'] = timing_details[st.session_state['current_frame_index'] - 1].uuid
                        st.session_state['frame_styling_view_type'] = "Individual View"
                        st.session_state['change_view_type'] = True
                        st.experimental_rerun()
                    
                    st.markdown("---")
                    btn1, btn2, btn3 = st.columns([2, 1, 1])
                    with btn1:
                        if st.button("Delete this keyframe", key=f'{i}'):
                            delete_frame(timing_details[i].uuid)
                            st.experimental_rerun()
                    with btn2:
                        if st.button("⬆️", key=f"Promote {display_number}"):
                            move_frame("Up", timing_details[i].uuid)
                            st.experimental_rerun()
                    with btn3:
                        if st.button("⬇️", key=f"Demote {display_number}"):
                            move_frame("Down", timing_details[i].uuid)
                            st.experimental_rerun()

                st.markdown("***")
            
            # Display radio buttons for pagination at the bottom
            st.markdown("***")

        # Update the current page in session state
        elif st.session_state['page'] == "Motion":

            
            
                                
            num_timing_details = len(timing_details)

            timing_details = data_repo.get_timing_list_from_project(project_uuid)       

            for idx in range(start_index, end_index):                      
                st.header(f"Frame {idx+1}")                        
                timing1, timing2, timing3 = st.columns([1, 1, 1])

                with timing1:
                    frame1, frame2,frame3 = st.columns([2,1,2])
                    with frame1:
                        if timing_details[idx].primary_image_location:
                            st.image(
                                timing_details[idx].primary_image_location)
                    with frame2:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.write("")
                        st.write("")
                        st.info("     ➜")
                    with frame3:                                                
                        if idx+1 < num_timing_details and timing_details[idx+1].primary_image_location:
                            st.image(timing_details[idx+1].primary_image_location)
                        elif idx+1 == num_timing_details:
                            st.write("")
                            st.write("")
                            st.write("")
                            st.write("")                            
                            st.markdown("<h1 style='text-align: center; color: black; font-family: Arial; font-size: 50px; font-weight: bold;'>FIN</h1>", unsafe_allow_html=True)

                    single_frame_time_selector(timing_details[idx].uuid, 'motion', shift_frames=shift_frames_setting)

                    single_frame_time_duration_setter(timing_details[idx].uuid,'motion',shift_frames=shift_frames_setting)

                    update_animation_style_element(timing_details[idx].uuid)


                if timing_details[idx].aux_frame_index != len(timing_details) - 1:
                    with timing2:
                        current_individual_clip_element(timing_details[idx].uuid)
                    with timing3:
                        current_preview_video_element(timing_details[idx].uuid)
                
                st.markdown("***")
    
    st.markdown("***")

    with st.expander("➕ Add Key Frame", expanded=True):

        selected_image, inherit_styling_settings, how_long_after, which_stage_for_starting_image = add_key_frame_element(timing_details, project_uuid)

        if st.button(f"Add key frame",type="primary",use_container_width=True):
            
            add_key_frame(selected_image, inherit_styling_settings, how_long_after, which_stage_for_starting_image)
            st.experimental_rerun()

