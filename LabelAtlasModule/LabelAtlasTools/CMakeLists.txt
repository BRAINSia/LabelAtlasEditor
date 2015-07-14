cmake_minimum_required(VERSION 2.8.9)

project(LabelAtlasTools)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/LabelAtlasTools")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (University of Iowa), William Lorensen, Hans Johnson (University of Iowa)")
set(EXTENSION_DESCRIPTION "Label atlases are utilized in medical imaging to segment an image into anatomical regions. Atlases often contain inaccuracies that will be propagated throughout the study if not identified and corrected. Open Atlas is a  collection of software tools developed by William Lorensen to support community-driven atlas editing. This Slicer module allows a user to visualize and efficiently edit errors recognized by the Open Atlas tools. ")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/LabelAtlasTools.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/LabelAtlasTools/Screenshots/1.png")

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
