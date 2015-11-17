cmake_minimum_required(VERSION 2.8.9)

project(LabelAtlasEditor)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://brainsia.github.io/LabelAtlasEditor")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Jessica Forbes (University of Iowa), Hans Johnson (University of Iowa)")
set(EXTENSION_DESCRIPTION "This module is for editing label atlases and automatically cleaning small islands of disconnected voxels.")
set(EXTENSION_ICONURL "https://github.com/BRAINSia/LabelAtlasEditor/blob/master/LabelAtlasEditor/Resources/Icons/LabelAtlasEditor.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/BRAINSia/LabelAtlasEditor/blob/master/automaticDustCleaningWidget.png https://github.com/BRAINSia/LabelAtlasEditor/blob/master/labelSuggestionWidget.png https://github.com/BRAINSia/LabelAtlasEditor/blob/master/mergeWidget.png https://github.com/BRAINSia/LabelAtlasEditor/blob/master/LabelAtlasEditor.png")

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
