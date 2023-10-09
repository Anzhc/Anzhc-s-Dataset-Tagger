import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QVBoxLayout, QWidget, QFileDialog, QLabel, QScrollArea, QSlider, QHBoxLayout, QGridLayout, QPushButton, QFrame, QGroupBox, QTabWidget, QLayout, QTextEdit, QCheckBox, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QRect, QSize, QPoint
from PyQt5.QtGui import QPixmap
import traceback
from datetime import datetime
from sortedcontainers import SortedDict

from scrollarea import CustomScrollArea
from layout import FlowLayout


class ImageBrowser(QMainWindow):

    def __init__(self):
        super().__init__()

        self.image_frames = {}  # Dictionary to store image frames
        self.edited_tags = {}
        self.single_selection_mode = False
        self.selected_tags_for_removal = set()
        self.selected_tags = set()
        self.tag_buttons_dict = SortedDict()
        self.editing_tags_buttons = []

        # Initialize the timer
        self.timer = QTimer()
        self.timer.setSingleShot(True)

        self.folder_path = ""
        self.thumbnail_size = 200
        self.selected_images = set()
        self.original_pixmaps = {}  # Dictionary to store original images
        self.selected_positive_tags = set()
        self.selected_negative_tags = set()
        self.image_tags = {}
        self.current_image_path = None

        main_layout = QVBoxLayout()

        # Top Section: Folder selection, save button, etc.
        top_section = QHBoxLayout()
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)
        top_section.addWidget(self.folder_button)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_all_tags)
        top_section.addWidget(self.save_button)
        main_layout.addLayout(top_section)

        # Middle Section: Splitter for Image Gallery and Tag/Edit Area
        splitter = QSplitter(Qt.Horizontal)
        self.images_panel = QWidget()
        self.images_layout = QGridLayout()
        self.images_layout.setSpacing(0)
        self.images_panel.setLayout(self.images_layout)
        self.scroll_area = CustomScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.images_panel)
        splitter.addWidget(self.scroll_area)

        # Right Part (Tag Selector and Sub-Menu)
        self.tag_edit_area = QWidget()
        self.tag_edit_layout = QVBoxLayout()
        tag_selector = self.create_tag_selector(
        )  # Call the create_tag_selector method
        self.tag_edit_layout.addWidget(tag_selector)  # Add it to the layout
        self.tag_edit_area.setLayout(self.tag_edit_layout)
        splitter.addWidget(self.tag_edit_area)

        splitter.setSizes([self.width() // 2, self.width() // 2])
        main_layout.addWidget(splitter)

        # Thumbnail size slider
        self.thumbnail_slider = QSlider(Qt.Horizontal)
        self.thumbnail_slider.setMinimum(50)
        self.thumbnail_slider.setMaximum(2000)
        self.thumbnail_slider.setValue(self.thumbnail_size)
        self.thumbnail_slider.valueChanged.connect(
            self.load_images)  # Connect to load_images
        self.thumbnail_slider.setTracking(True)  # Update only when released
        main_layout.addWidget(self.thumbnail_slider)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Anzhc's Dataset Tagger")
        self.show()

        self.positive_tags_buttons = []
        self.negative_tags_buttons = []

    def create_tag_selector(self):
        # Create the sub-menu tabs widget
        self.sub_menu_tabs = QTabWidget()
        self.sub_menu_tabs.setDocumentMode(True)  # Makes tabs look smaller
        self.sub_menu_tabs.setUsesScrollButtons(
            True)  # Allows scrolling if many tabs

        # Tag Cloud Tab
        tag_cloud_widget = QWidget()
        tag_cloud_layout = QVBoxLayout()

        # Splitter for Positive and Negative Tags
        tag_splitter = QSplitter(Qt.Vertical)

        # Positive Tags
        positive_tags_group = QGroupBox("Positive Tags")
        positive_tags_group_layout = QVBoxLayout()
        self.positive_tags_layout = FlowLayout(
        )  # Create FlowLayout for positive tags

        # Add QLineEdit for positive tags filter
        self.positive_tag_filter_edit = QLineEdit()
        self.positive_tag_filter_edit.setPlaceholderText("Filter tags...")
        self.positive_tag_filter_edit.textChanged.connect(
            self.populate_tag_clouds)
        positive_tags_group_layout.addWidget(self.positive_tag_filter_edit)

        # Add FlowLayout to the group layout
        positive_tags_container = QWidget()
        positive_tags_container.setLayout(self.positive_tags_layout)
        positive_tags_scroll = QScrollArea()
        positive_tags_scroll.setWidget(positive_tags_container)
        positive_tags_scroll.setWidgetResizable(True)
        positive_tags_group_layout.addWidget(positive_tags_scroll)

        positive_tags_group.setLayout(positive_tags_group_layout)
        tag_splitter.addWidget(positive_tags_group)

        # Negative Tags
        negative_tags_group = QGroupBox("Negative Tags")
        negative_tags_group_layout = QVBoxLayout()
        self.negative_tags_layout = FlowLayout(
        )  # Create FlowLayout for negative tags

        # Add QLineEdit for negative tags filter
        self.negative_tag_filter_edit = QLineEdit()
        self.negative_tag_filter_edit.setPlaceholderText("Filter tags...")
        self.negative_tag_filter_edit.textChanged.connect(
            self.populate_tag_clouds)
        negative_tags_group_layout.addWidget(self.negative_tag_filter_edit)

        self.positive_tag_filter_edit.textChanged.connect(
            self.update_positive_tag_cloud_visibility)
        self.negative_tag_filter_edit.textChanged.connect(
            self.update_negative_tag_cloud_visibility)

        # Add FlowLayout to the group layout
        negative_tags_container = QWidget()
        negative_tags_container.setLayout(self.negative_tags_layout)
        negative_tags_scroll = QScrollArea()
        negative_tags_scroll.setWidget(negative_tags_container)
        negative_tags_scroll.setWidgetResizable(True)
        negative_tags_group_layout.addWidget(negative_tags_scroll)

        negative_tags_group.setLayout(negative_tags_group_layout)
        tag_splitter.addWidget(negative_tags_group)

        tag_cloud_layout.addWidget(tag_splitter)
        tag_cloud_widget.setLayout(tag_cloud_layout)
        self.sub_menu_tabs.addTab(tag_cloud_widget, "Tag Cloud")

        # Placeholder tabs
        self.sub_menu_tabs.addTab(self.create_mass_edit_tab(), "Mass Edit")
        self.sub_menu_tabs.addTab(self.create_tag_editing_tab(), "Tag Edit")
        self.sub_menu_tabs.addTab(self.create_tag_removal_tab(), "Tag Removal")

        # Utility Buttons Section
        utility_buttons_layout = QHBoxLayout()

        # Button to clear tag selection
        clear_tags_button = QPushButton("Remove Tag Selection")
        clear_tags_button.clicked.connect(self.clear_tag_selection)
        utility_buttons_layout.addWidget(clear_tags_button)

        # Button to select all visible images
        select_visible_button = QPushButton("Select All Visible Images")
        select_visible_button.clicked.connect(self.select_all_visible_images)
        utility_buttons_layout.addWidget(select_visible_button)

        deselect_visible_images_button = QPushButton("Deselect Visible Images")
        deselect_visible_images_button.clicked.connect(
            self.deselect_visible_images)
        utility_buttons_layout.addWidget(deselect_visible_images_button)

        # Add the utility buttons layout to the tag cloud layout
        tag_cloud_layout.addLayout(utility_buttons_layout)

        return self.sub_menu_tabs

    def create_tag_editing_tab(self):
        tag_editing_tab = QWidget()
        main_layout = QHBoxLayout()  # Horizontal layout

        # Create Tag Cloud for Edit
        tag_cloud_widget = QWidget()
        tag_cloud_layout = QVBoxLayout()
        tags_group = QGroupBox("Tags")
        self.tags_edit_layout = FlowLayout()

        tags_group.setLayout(self.tags_edit_layout)
        tags_scroll = QScrollArea()
        tags_container = QWidget()
        tags_container.setLayout(self.tags_edit_layout)
        tags_scroll.setWidget(tags_container)
        tags_scroll.setWidgetResizable(True)
        tag_cloud_layout.addWidget(tags_scroll)
        tag_cloud_widget.setLayout(tag_cloud_layout)

        # Right side vertical layout for existing tag editing features
        layout = QVBoxLayout()

        # Upper window to display the current tags (read-only)
        self.current_tags_text_edit = QTextEdit()
        self.current_tags_text_edit.setReadOnly(True)
        layout.addWidget(self.current_tags_text_edit)

        # Lower window for editing tags (input field)
        self.edit_tags_text_edit = QTextEdit()
        layout.addWidget(self.edit_tags_text_edit)

        # Buttons
        buttons_layout = QHBoxLayout()
        copy_button = QPushButton("Copy from Existing")
        copy_button.clicked.connect(self.copy_existing_tags)
        buttons_layout.addWidget(copy_button)

        apply_button = QPushButton("Apply Tag Edit")
        apply_button.clicked.connect(lambda: self.apply_tag_edit(
            self.current_image_path, self.edit_tags_text_edit.toPlainText()))
        buttons_layout.addWidget(apply_button)

        revert_button = QPushButton("Revert to Original Tags")
        revert_button.clicked.connect(self.revert_to_original_tags)
        buttons_layout.addWidget(revert_button)

        # Checkboxes
        self.single_selection_checkbox = QCheckBox("Single Selection Mode")
        layout.addWidget(self.single_selection_checkbox)
        self.single_selection_checkbox.stateChanged.connect(
            self.toggle_single_selection_mode)

        self.auto_copy_tags_checkbox = QCheckBox("Auto Copy")
        layout.addWidget(self.auto_copy_tags_checkbox)

        self.auto_save_checkbox = QCheckBox(
            "Auto-Save Tags on Selection Change")
        layout.addWidget(self.auto_save_checkbox)

        layout.addLayout(buttons_layout)

        # Adding the QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(
            tag_cloud_widget)  # Add tag cloud widget to the splitter

        right_side_widget = QWidget(
        )  # Create a widget to contain the right side components
        right_side_widget.setLayout(layout)
        splitter.addWidget(
            right_side_widget)  # Add the right-side widget to the splitter

        main_layout.addWidget(splitter)  # Add the splitter to the main layout
        tag_editing_tab.setLayout(main_layout)
        self.edit_tags_text_edit.textChanged.connect(
            self.update_tag_button_states)

        for button in self.tag_buttons_dict.values():
            self.tags_edit_layout.addWidget(button['edit'])
            button['edit'].setVisible(True)
        print(
            f"Added {len(self.tag_buttons_dict)} buttons to the tags edit layout."
        )

        return tag_editing_tab

    def create_tag_removal_tab(self):
        tag_removal_tab = QWidget()
        layout = QVBoxLayout()

        # Line Edit for Tag Filtering
        self.tag_removal_filter_edit = QLineEdit()
        self.tag_removal_filter_edit.setPlaceholderText("Filter tags...")
        self.tag_removal_filter_edit.textChanged.connect(
            self.update_removal_tag_cloud_visibility)
        layout.addWidget(self.tag_removal_filter_edit)

        # Tag Cloud for Removal Selection
        tag_cloud_widget = QWidget()
        tag_cloud_layout = QVBoxLayout()
        tags_group = QGroupBox("Tags to Remove")
        self.tags_removal_layout = FlowLayout()

        tags_group.setLayout(self.tags_removal_layout)
        tags_scroll = QScrollArea()
        tags_container = QWidget()
        tags_container.setLayout(self.tags_removal_layout)
        tags_scroll.setWidget(tags_container)
        tags_scroll.setWidgetResizable(True)
        tag_cloud_layout.addWidget(tags_scroll)
        tag_cloud_widget.setLayout(tag_cloud_layout)
        layout.addWidget(tag_cloud_widget)

        # Button to Remove Selected Tags
        remove_tags_button = QPushButton("Remove Selected Tags")
        remove_tags_button.clicked.connect(
            self.remove_selected_tags_from_dataset)
        layout.addWidget(remove_tags_button)

        tag_removal_tab.setLayout(layout)
        return tag_removal_tab

    def create_mass_edit_tab(self):
        mass_edit_tab = QWidget()
        layout = QVBoxLayout()

        # Label and text edit for displaying the selected tags
        selected_tags_label = QLabel("Selected Tags:")
        self.selected_tags_text_edit = QTextEdit()
        self.selected_tags_text_edit.setReadOnly(True)
        layout.addWidget(selected_tags_label)
        layout.addWidget(self.selected_tags_text_edit)

        # Label and text edit for entering the new tags
        new_tags_label = QLabel("New Tags:")
        self.new_tags_text_edit = QTextEdit()
        layout.addWidget(new_tags_label)
        layout.addWidget(self.new_tags_text_edit)

        # Button to apply the mass edit
        apply_mass_edit_button = QPushButton("Apply Mass Edit")
        apply_mass_edit_button.clicked.connect(self.apply_mass_edit)
        layout.addWidget(apply_mass_edit_button)

        mass_edit_tab.setLayout(layout)
        return mass_edit_tab

    def select_folder(self):
        self.clear_tags()  # Clear the tag data
        self.folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder")
        self.original_pixmaps = {}  # Clear existing original images
        self.load_images()
        self.load_tags()
        self.initialize_all_tag_buttons()
        self.populate_tag_clouds()

    def load_images(self):
        self.thumbnail_size = self.thumbnail_slider.value()
        if not self.folder_path:
            return
        # Clear existing widgets
        for i in reversed(range(self.images_layout.count())):
            widget = self.images_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.image_frames.clear()  # Clear existing frames

        # Load images and reapply selection state
        image_files = [
            f for f in os.listdir(self.folder_path)
            if os.path.isfile(os.path.join(self.folder_path, f))
            and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        ]

        for image_file in image_files:
            image_path = os.path.join(self.folder_path, image_file)

            # Check if the corresponding .txt file exists
            tag_file_path = os.path.splitext(image_path)[0] + '.txt'
            if not os.path.exists(tag_file_path):
                # If the .txt file doesn't exist, create it with no content
                open(tag_file_path, 'a').close()

        max_columns = self.scroll_area.viewport().width() // (
            self.thumbnail_size + 20)  # Number of columns
        row, col = 0, 0
        for image_file in image_files:
            image_path = os.path.join(self.folder_path, image_file)
            if image_path not in self.original_pixmaps:  # Load original image if not already loaded
                self.original_pixmaps[image_path] = QPixmap(image_path)
            pixmap = self.original_pixmaps[image_path].scaled(
                self.thumbnail_size, self.thumbnail_size, Qt.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(pixmap)
            frame = QFrame()
            frame.setFrameShape(QFrame.Box)
            frame.setLineWidth(2)
            frame.setFixedSize(self.thumbnail_size + 10,
                               self.thumbnail_size + 10)
            layout = QVBoxLayout()
            layout.addWidget(label, alignment=Qt.AlignCenter)
            frame.setLayout(layout)
            frame.setObjectName(image_path)
            frame.mousePressEvent = lambda e, path=image_path: self.select_image(
                path)
            self.images_layout.addWidget(frame, row, col)
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
            self.image_frames[image_path] = frame  # Store the frame

            # Reapply selection state
            if image_path in self.selected_images:
                frame.setStyleSheet("border: 6px solid grey;")
        self.filter_gallery()

    def select_image(self, image_path):
        image_key = os.path.basename(image_path)
        if self.auto_save_checkbox.isChecked() and self.current_image_path:
            # Get the edited tags from the input field
            edited_tags = self.edit_tags_text_edit.toPlainText()

            # Get the current tags for the previously selected image
            current_tags = self.get_tags_for_image(self.current_image_path)

            # Compare with the current tags, and if different, apply the changes
            if edited_tags != current_tags:
                self.apply_tag_edit(self.current_image_path, edited_tags)

        # Update the current image path with the new selection
        self.current_image_path = image_path

        # Update the current image and its corresponding tags
        self.current_image = image_path
        self.current_tags = self.image_tags[
            image_key]  # Fetch tags directly from self.image_tags
        if self.single_selection_mode and len(self.selected_images) > 0:
            # Deselect all other images
            for other_image_path in list(self.selected_images):
                if other_image_path != image_path:
                    self.deselect_image(other_image_path)
        # Check if the auto copy tags checkbox is checked
        if self.auto_copy_tags_checkbox.isChecked():
            # Copy the existing tags to the input field
            existing_tags_string = ', '.join(self.current_tags)
            self.edit_tags_text_edit.setText(existing_tags_string)
        frame = self.findChild(QFrame, image_path)
        if image_path in self.selected_images:
            frame.setStyleSheet("")
            self.selected_images.remove(image_path)
        else:
            frame.setStyleSheet("border: 6px solid grey;")
            self.selected_images.add(image_path)
        print(f"Selecting image: {image_path}")
        tags_string = ', '.join(self.current_tags)
        self.current_tags_text_edit.setText(tags_string)
        print(
            f"Text set to widget: {self.current_tags_text_edit.toPlainText()}")

    def load_tags(self):
        if not self.folder_path:
            return

        for image_file in os.listdir(self.folder_path):
            if image_file.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                tag_file_path = os.path.join(
                    self.folder_path,
                    os.path.splitext(image_file)[0] + ".txt")
                if os.path.exists(tag_file_path):
                    with open(tag_file_path, "r") as file:
                        tag_line = file.read().strip()
                        tags = [tag.strip() for tag in tag_line.split(',')
                                ]  # Strip whitespace from each tag
                        self.image_tags[image_file] = set(
                            tags)  # Store as a set to remove duplicates

    def populate_tag_clouds(self):
        # Get the filters
        positive_filter = self.positive_tag_filter_edit.text()
        negative_filter = self.negative_tag_filter_edit.text()
        removal_filter = self.tag_removal_filter_edit.text()

        # Show/Hide buttons based on filters
        try:
            for tag, buttons in self.tag_buttons_dict.items():
                # Check if tag contains the filter text
                show_positive = positive_filter in tag
                show_negative = negative_filter in tag
                show_removal = removal_filter in tag

                # Update button visibility for positive, negative, and removal buttons
                if "positive" in buttons:
                    buttons["positive"].setVisible(show_positive)
                    buttons["positive"].setChecked(
                        tag in self.selected_positive_tags)
                else:
                    print(f"Missing positive button for tag: {tag}")

                if "negative" in buttons:
                    buttons["negative"].setVisible(show_negative)
                    buttons["negative"].setChecked(
                        tag in self.selected_negative_tags)
                else:
                    print(f"Missing negative button for tag: {tag}")

                if "removal" in buttons:
                    buttons["removal"].setVisible(show_removal)
                else:
                    print(f"Missing removal button for tag: {tag}")
        except Exception as e:
            print("Exception occurred:", e)
            print(traceback.format_exc())

    def toggle_tag(self, tag, state, negative=False):
        if state:
            if negative:
                self.selected_negative_tags.add(tag)
            else:
                self.selected_positive_tags.add(tag)
                self.selected_tags.add(tag)  # Add the selected tag
        else:
            if negative:
                self.selected_negative_tags.remove(tag)
            else:
                self.selected_positive_tags.remove(tag)
                self.selected_tags.discard(tag)  # Remove the deselected tag
        self.filter_gallery(
        )  # Call to filter the gallery based on selected tags
        self.update_selected_tags_display()

    def should_show_image(self, image_path):
        image_tags = self.image_tags.get(os.path.basename(image_path), set())

        # If any positive tags are selected, the image must have at least one of them
        if self.selected_positive_tags and not any(
                tag in image_tags for tag in self.selected_positive_tags):
            return False

        # If any negative tags are selected, the image must not have any of them
        if self.selected_negative_tags and any(
                tag in image_tags for tag in self.selected_negative_tags):
            return False

        return True

    def filter_gallery(self):
        row, col = 0, 0
        max_columns = self.scroll_area.viewport().width() // (
            self.thumbnail_size + 20)  # Number of columns

        for image_path, frame in self.image_frames.items():
            # Determine if the image should be shown based on the tags
            should_show = self.should_show_image(image_path)

            if should_show:
                # If the image should be shown, position it at the current row and column
                self.images_layout.addWidget(frame, row, col)
                col += 1
                if col >= max_columns:
                    col = 0
                    row += 1

            # Show or hide the frame
            frame.setVisible(should_show)

    def clear_tag_selection(self):
        # Clear selected positive tags
        for button in self.positive_tags_buttons:
            button.setChecked(False)
        self.selected_positive_tags.clear()

        # Clear selected negative tags
        for button in self.negative_tags_buttons:
            button.setChecked(False)
        self.selected_negative_tags.clear()

        # Refresh the gallery
        self.filter_gallery()

    def select_all_visible_images(self):
        for image_path, frame in self.image_frames.items():
            if frame.isVisible():
                frame.setStyleSheet("border: 6px solid grey;")
                self.selected_images.add(image_path)

    def deselect_visible_images(self):
        for image_path, frame in self.image_frames.items():
            if frame.isVisible():
                frame.setStyleSheet("")
                self.selected_images.discard(image_path)

    def deselect_image(self, image_path):
        # Remove the image path from the set of selected images
        if image_path in self.selected_images:
            self.selected_images.remove(image_path)

        # Update the border of the corresponding frame in the main gallery
        frame = self.image_frames.get(image_path)
        if frame:
            frame.setStyleSheet("")  # Resetting the border style

    def copy_existing_tags(self):
        # Copy the content from the current tags text edit to the editable text edit
        self.edit_tags_text_edit.setPlainText(
            self.current_tags_text_edit.toPlainText())

    def update_tags(self, image_path, new_tags_set):
        # Use the base filename as the key
        image_file = os.path.basename(image_path)

        # Update the in-memory tag data for the specified image
        self.image_tags[image_file] = new_tags_set

        # Recount all the tags
        all_tags = {}
        for tags in self.image_tags.values():
            for tag in tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1

        # Convert the set to a comma-separated string
        new_tags_string = ', '.join(new_tags_set)

        # Set the text of the current tags text edit
        self.current_tags_text_edit.setText(new_tags_string)

        # Refresh the tag editing tab to reflect the changes
        #self.refresh_tag_editing_tab()

        # Refresh the tag clouds to reflect the changes
        self.refresh_all_tag_clouds()

    def revert_to_original_tags(self):
        # Check if only one image is selected
        if len(self.selected_images) != 1:
            return

        # Get the path of the selected image
        image_path = next(iter(self.selected_images))

        # Retrieve the original tags from the file or from memory
        original_tags = self.load_original_tags(image_path)

        # Set the original tags in the current tags text edit
        self.current_tags_text_edit.setPlainText(original_tags)

        # Update the editable tags text edit to match the original
        self.edit_tags_text_edit.setPlainText(original_tags)

        # Remove the edited tags from the edited_tags dictionary
        self.edited_tags.pop(image_path, None)

    def load_selected_image_tags(self):
        # Clear any existing content
        self.current_tags_text_edit.clear()
        self.edit_tags_text_edit.clear()

        # Check if exactly one image is selected
        if len(self.selected_images) == 1:
            image_path = next(iter(self.selected_images))
            tag_file_path = os.path.splitext(
                image_path
            )[0] + ".txt"  # Assuming tags are stored in .txt files with the same name as the image

            # Check if the tag file exists
            if os.path.exists(tag_file_path):
                with open(tag_file_path, 'r', encoding='utf-8') as file:
                    tags = file.read()
                    self.current_tags_text_edit.setPlainText(tags)

    def save_all_tags(self):
        for image_path, new_tags in self.edited_tags.items():
            image_file_name = os.path.basename(image_path)
            tag_file_name = os.path.splitext(image_file_name)[0] + '.txt'
            tag_file_path = os.path.join(self.folder_path, tag_file_name)

            # Convert the set of tags to a string
            new_tags_string = ', '.join(new_tags)

            try:
                with open(tag_file_path, 'w') as file:
                    file.write(new_tags_string)
            except Exception as e:
                print(f"Error saving tags for {image_file_name}: {e}")

        # Clear the edited_tags dictionary since changes have been saved
        self.edited_tags.clear()

    def load_original_tags(self, image_path):
        tag_file_path = os.path.splitext(image_path)[0] + ".txt"
        with open(tag_file_path, 'r', encoding='utf-8') as file:
            original_tags = file.read()
        return original_tags

    def get_tags_for_image(self, image_path):
        # Get the base name of the image to use as the key
        image_key = os.path.basename(image_path)

        # Check if updated tags are available for the image
        if image_key in self.edited_tags:
            print(
                f"Retrieved tags for {image_key} from edited_tags: {self.edited_tags[image_key]}"
            )  # Add this line
            return self.edited_tags[image_key]

        tag_file_path_base = os.path.splitext(image_key)[
            0]  # Remove the extension
        tag_file_path = os.path.join(self.folder_path,
                                     tag_file_path_base + ".txt")

        if os.path.exists(tag_file_path):
            with open(tag_file_path, 'r') as file:
                tags = file.read().strip()
                tags_set = set(tag.strip() for tag in tags.split(',')
                               if tag.strip())  # Convert to a set
                return tags_set

        return set()  # Return an empty set if no tags are found

    def toggle_single_selection_mode(self):
        if self.single_selection_checkbox.isChecked():
            self.single_selection_mode = True
        else:
            self.single_selection_mode = False

    def add_tag_to_edit(self, tag):

        existing_tags = self.edit_tags_text_edit.toPlainText()

        if existing_tags:
            updated_tags = existing_tags + ", " + tag
        else:
            updated_tags = tag

        self.edit_tags_text_edit.setPlainText(updated_tags)

    def refresh_tag_editing_tab(self):
        # 1. Extract all unique tags from self.image_tags
        all_tags = set()
        for tags in self.image_tags.values():
            all_tags.update(tags)

        # 2. Sort the tags (optional, but can be useful for display)
        sorted_tags = sorted(all_tags)

        # 3. Populate the tag cloud in the editing tab
        # Clear existing buttons from the layout
        for i in reversed(range(self.tags_edit_layout.count())):
            widget = self.tags_edit_layout.itemAt(i).widget()
            if widget is not None:
                try:
                    widget.clicked.disconnect()  # Try to disconnect signals
                except TypeError:
                    pass  # Ignore the error if no connections to disconnect

                widget.deleteLater()

        # Add the buttons for each tag to the layout
        for tag in sorted_tags:
            tag_button = QPushButton(tag)
            tag_button.setCheckable(True)  # Allow the button to be checked
            tag_button.clicked.connect(
                lambda _, tag=tag: self.add_tag_to_edit(tag))
            self.tags_edit_layout.addWidget(tag_button)

        # Update the state of the tag buttons to match the current tags
        self.update_tag_button_states()

    def update_tag_button_states(self):
        # Get the current tags in the text field
        current_tags = set(
            self.edit_tags_text_edit.toPlainText().strip().split(', '))

        # Update the state of each tag button
        for i in range(self.tags_edit_layout.count()):
            widget = self.tags_edit_layout.itemAt(i).widget()
            if widget is not None:
                widget.setChecked(widget.text() in current_tags)

    def toggle_tag_for_removal(self, tag, state):
        if state:
            self.selected_tags_for_removal.add(tag)
        else:
            self.selected_tags_for_removal.discard(tag)

    def remove_selected_tags_from_dataset(self):
        print(f"remove_selected_tags_from_dataset called at {datetime.now()}")
        if not self.selected_tags_for_removal:
            return

        # Create a set to track removed tags
        removed_tags = set()

        # Iterate through the image tags in memory and remove the selected tags
        for image_file, tags in self.image_tags.items():
            # Get the original tags
            original_tags = tags.copy()

            # Update the tags in-memory
            tags.difference_update(self.selected_tags_for_removal)

            # Update the edited_tags dictionary using image_key
            image_key = os.path.splitext(image_file)[0]
            self.edited_tags[image_key] = tags

            # Track the removed tags
            removed_tags.update(original_tags - tags)

        # Refresh the tag clouds to reflect the changes
        self.refresh_all_tag_clouds()

    def apply_tag_edit(self, image_path, new_tags):
        # Check if image_path is None or an empty string
        if not image_path:
            print("No image selected. Cannot apply tag edit.")
            return

        new_tags_list = [
            tag.strip() for tag in new_tags.split(',') if tag.strip()
        ]
        new_tags_set = set(new_tags_list)

        image_file = os.path.basename(image_path)
        existing_tags = self.image_tags.get(image_file, set())

        if existing_tags != new_tags_set:
            self.edited_tags[image_file] = new_tags_set

            # Update the original tags display
            self.current_tags_text_edit.setText(', '.join(new_tags_set))

            # Update the in-memory tag data
            self.update_tags(image_path, new_tags_set)

            # Determine which tags were added and which were removed
            added_tags = new_tags_set - existing_tags
            removed_tags = existing_tags - new_tags_set

            # Update the tag clouds to reflect the changes
            self.update_tag_cloud(added_tags, removed_tags)

    def update_selected_tags_display(self):
        selected_tags = ', '.join(self.selected_positive_tags)
        self.selected_tags_text_edit.setText(selected_tags)

    def apply_mass_edit(self):
        selected_tags = set(
            tag.strip() for tag in
            self.selected_tags_text_edit.toPlainText().strip().split(','))
        new_tags = set(
            tag.strip()
            for tag in self.new_tags_text_edit.toPlainText().strip().split(
                ','))

        # Tracks added and removed tags globally
        added_tags_global = set()
        removed_tags_global = set()

        for image_path, frame in self.image_frames.items():
            if frame.isVisible():
                # Get the base name of the image to use as the key
                image_key = os.path.basename(image_path)
                existing_tags = self.image_tags.get(image_key, set()).copy()

                # Determine the tags to be removed (only those not in the new tags)
                removed_tags = selected_tags.intersection(
                    existing_tags) - new_tags
                # Determine the tags to be added (only those not in the existing tags)
                added_tags = new_tags - existing_tags

                # Update the global tracking
                added_tags_global.update(added_tags)
                removed_tags_global.update(removed_tags)

                # Update the tags
                existing_tags.difference_update(removed_tags)
                existing_tags.update(added_tags)

                # Convert the set to a comma-separated string for apply_tag_edit
                new_tags_string = ', '.join(existing_tags)

                # Call apply_tag_edit with the image path and new tags string
                self.apply_tag_edit(image_path, new_tags_string)

        # Update the tag clouds with the added and removed tags
        self.update_tag_cloud(added_tags_global, removed_tags_global)
        self.refresh_all_tag_clouds()

    def clear_tags(self):
        self.image_tags.clear()
        self.edited_tags.clear()
        self.selected_positive_tags.clear()
        self.selected_negative_tags.clear()

        # Clear existing tag buttons from layouts and dictionary
        for layout in [
                self.positive_tags_layout, self.negative_tags_layout,
                self.tags_removal_layout
        ]:
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

        self.tag_buttons_dict.clear()

    def update_positive_tag_filter(self, text):
        self.positive_tag_filter = text
        self.refresh_all_tag_clouds()

    def update_negative_tag_filter(self, text):
        self.negative_tag_filter = text
        self.refresh_all_tag_clouds()

    def initialize_single_tag_button(self, tag, count):
        # Create the buttons
        positive_tag_button = QPushButton(f"{tag} ({count})")
        positive_tag_button.setCheckable(True)
        positive_tag_button.clicked.connect(
            lambda state, t=tag: self.toggle_tag(t, state))

        negative_tag_button = QPushButton(f"{tag} ({count})")
        negative_tag_button.setCheckable(True)
        negative_tag_button.clicked.connect(
            lambda state, t=tag: self.toggle_tag(t, state, negative=True))

        removal_tag_button = QPushButton(f"{tag} ({count})")
        removal_tag_button.setCheckable(True)
        removal_tag_button.clicked.connect(
            lambda state, t=tag: self.toggle_tag_for_removal(t, state))

        edit_tag_button = QPushButton(tag)
        edit_tag_button.setCheckable(True)
        edit_tag_button.clicked.connect(
            lambda _, t=tag: self.add_tag_to_edit(t))

        # Create the buttons dictionary
        buttons = {
            "positive": positive_tag_button,
            "negative": negative_tag_button,
            "removal": removal_tag_button,
            "edit": edit_tag_button
        }

        return buttons

    def initialize_all_tag_buttons(self):
        # Calculate all_tags based on the current state of image_tags
        all_tags = self.calculate_tag_counts()

        # Create the buttons and add them to a temporary dictionary
        temp_buttons_dict = {}
        for tag, count in all_tags.items():
            buttons = self.initialize_single_tag_button(tag, count)
            temp_buttons_dict[tag] = buttons

        # Sort the temporary dictionary by the count of each tag in descending order
        sorted_tags = sorted(temp_buttons_dict.items(),
                             key=lambda item: -all_tags.get(item[0], 0))

        # Create a new SortedDict using the sorted tags
        self.tag_buttons_dict = SortedDict(lambda tag: -all_tags.get(tag, 0))
        for tag, buttons in sorted_tags:
            self.tag_buttons_dict[tag] = buttons
        self.refresh_all_tag_clouds()

    def toggle_tag_in_edit(self, tag, state):
        current_tags = self.edit_tags_text_edit.toPlainText().strip().split(
            ', ')
        if state:  # Add the tag if it was toggled on
            current_tags.append(tag)
        else:  # Remove the tag if it was toggled off
            current_tags = [t for t in current_tags if t != tag]
        self.edit_tags_text_edit.setText(', '.join(current_tags))

    def update_tag_cloud(self, added_tags, removed_tags):
        # Extract all unique tags from self.image_tags
        all_tags = self.calculate_tag_counts()

        # Handle the added tags
        for tag in added_tags:
            count = all_tags[tag]
            buttons = self.initialize_single_tag_button(tag, count)
            self.tag_buttons_dict[tag] = buttons
            for layout_key, layout in zip(
                ['positive', 'negative', 'removal', 'edit'], [
                    self.positive_tags_layout, self.negative_tags_layout,
                    self.tags_removal_layout, self.tags_edit_layout
                ]):
                layout.addWidget(buttons[layout_key])

        # Handle the removed tags
        for tag in removed_tags:
            buttons = self.tag_buttons_dict[tag]
            for button in buttons.values():
                button.setParent(None)
                button.deleteLater()
            del self.tag_buttons_dict[tag]

        # Now we'll rebuild all the layouts according to the sorted order
        for layout_key, layout in zip(
            ['positive', 'negative', 'removal', 'edit'], [
                self.positive_tags_layout, self.negative_tags_layout,
                self.tags_removal_layout, self.tags_edit_layout
            ]):
            # Clear the existing widgets in the layout
            for _ in range(layout.count()):
                widget = layout.itemAt(0).widget()
                layout.removeWidget(widget)

            # Add widgets back according to the sorted order
            for tag, buttons in self.tag_buttons_dict.items():
                button = buttons[layout_key]
                layout.addWidget(button)

    def refresh_all_tag_clouds(self):
        # Extract all unique tags from self.image_tags
        all_tags = self.calculate_tag_counts()

        # Create a temporary dictionary to store the new buttons
        new_tag_buttons_dict = SortedDict(lambda tag: -all_tags.get(tag, 0))

        # Check each tag in the dictionary
        for tag, buttons in self.tag_buttons_dict.items():
            if tag not in all_tags:
                # The tag has been removed
                # Remove the buttons from the layout and delete them
                buttons['positive'].setParent(None)
                buttons['negative'].setParent(None)
                buttons['removal'].setParent(None)
                buttons['positive'].deleteLater()
                buttons['negative'].deleteLater()
                buttons['removal'].deleteLater()
            else:
                # The tag still exists
                # Update the count in the button text
                count = all_tags[tag]
                buttons['positive'].setText(f"{tag} ({count})")
                buttons['negative'].setText(f"{tag} ({count})")
                buttons['removal'].setText(f"{tag} ({count})")
                # Add the existing buttons to the new sorted dictionary
                new_tag_buttons_dict[tag] = buttons

        # Any tags left in the all_tags dictionary are new tags
        # Add buttons for the new tags
        for tag, count in all_tags.items():
            if tag not in new_tag_buttons_dict and tag in self.tag_buttons_dict:
                self.initialize_single_tag_button(tag, count)
                new_tag_buttons_dict[tag] = self.tag_buttons_dict[tag]

        # Assign the new sorted dictionary to the tag_buttons_dict attribute
        self.tag_buttons_dict = new_tag_buttons_dict

        # Rebuild the layouts according to the sorted order
        for tag, buttons in self.tag_buttons_dict.items():
            self.positive_tags_layout.addWidget(buttons['positive'])
            self.negative_tags_layout.addWidget(buttons['negative'])
            self.tags_removal_layout.addWidget(buttons['removal'])

    def delete_tag_button(self, button, tag):
        # Disconnect any signals from the button
        try:
            button.clicked.disconnect()
        except TypeError:
            pass  # No connections to disconnect

        # Remove the button from the layouts
        self.positive_tags_layout.removeWidget(button)
        self.negative_tags_layout.removeWidget(button)
        self.tags_removal_layout.removeWidget(button)
        self.tags_edit_layout.removeWidget(button)

        # Delete the button
        button.deleteLater()

        # Remove the button's reference from the dictionary
        if tag in self.tag_buttons_dict:
            del self.tag_buttons_dict[tag]

    def calculate_tag_counts(self, specific_tag=None):
        all_tags = {}
        for tags_set in self.image_tags.values():
            for tag in tags_set:
                if specific_tag is not None and tag != specific_tag:
                    continue
                all_tags[tag] = all_tags.get(tag, 0) + 1
        return all_tags

    def update_positive_tag_cloud_visibility(self):
        filter_text = self.positive_tag_filter_edit.text()
        for tag, buttons in self.tag_buttons_dict.items():
            buttons['positive'].setVisible(filter_text in tag)

    def update_negative_tag_cloud_visibility(self):
        filter_text = self.negative_tag_filter_edit.text()
        for tag, buttons in self.tag_buttons_dict.items():
            buttons['negative'].setVisible(filter_text in tag)

    def update_removal_tag_cloud_visibility(self):
        filter_text = self.tag_removal_filter_edit.text()
        for tag, buttons in self.tag_buttons_dict.items():
            buttons['removal'].setVisible(filter_text in tag)

    def update_tag_cloud(self, added_tags, removed_tags):
        # Extract all unique tags from self.image_tags
        all_tags = self.calculate_tag_counts()

        # Update the tag cloud for the added tags
        for tag in added_tags:
            count = all_tags.get(tag, 0)
            if count == 0:
                continue  # Skip if the tag does not exist in all_tags
            buttons = self.initialize_single_tag_button(tag, count)
            self.tag_buttons_dict[tag] = buttons
            self.positive_tags_layout.addWidget(buttons['positive'])
            self.negative_tags_layout.addWidget(buttons['negative'])
            self.tags_removal_layout.addWidget(buttons['removal'])
            # Handle the edit layout here if needed

        # Update the tag cloud for the removed tags
        for tag in removed_tags:
            if tag in self.tag_buttons_dict:  # Check if the tag exists in the dictionary
                buttons = self.tag_buttons_dict[tag]
                buttons['positive'].setParent(None)
                buttons['negative'].setParent(None)
                buttons['removal'].setParent(None)
                # Handle the edit layout here if needed
                del self.tag_buttons_dict[tag]

        # Re-arrange the widgets in the layout based on the sorted order
        for layout in [
                self.positive_tags_layout, self.negative_tags_layout,
                self.tags_removal_layout, self.tags_edit_layout
        ]:  # Include tags_edit_layout
            layout_key = None
            if layout == self.positive_tags_layout:
                layout_key = 'positive'
            elif layout == self.negative_tags_layout:
                layout_key = 'negative'
            elif layout == self.tags_removal_layout:
                layout_key = 'removal'
            elif layout == self.tags_edit_layout:
                layout_key = 'edit'  # Handle the edit layout key here

            # Clear the existing widgets in the layout
            for _ in range(layout.count()):
                widget = layout.itemAt(0).widget()
                layout.removeWidget(widget)

            # Add widgets back according to the sorted order
            for tag, buttons in self.tag_buttons_dict.items():
                button = buttons[layout_key]
                layout.addWidget(button)
