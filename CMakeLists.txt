cmake_minimum_required(VERSION 2.8.9)

project(LabelAtlasEditor)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/BRAINSia/LabelAtlasEditor")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (University of Iowa), Hans Johnson (University of Iowa)")
set(EXTENSION_DESCRIPTION "Label atlases are utilized in medical imaging to segment an image into anatomical regions. Atlases often contain inaccuracies that will be propagated throughout the study if not identified and corrected. This Slicer module allows a user to visualize and efficiently edit errors in label atlases. ")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/LabelAtlasEditor.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/LabelAtlasEditor/Screenshots/1.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(LabelAtlasEditor)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
