import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import Editor
import SimpleITK as sitk
import sitkUtils as su
import math
from Resources.atlasSmallIslandCleanup import DustCleanup

#
# LabelAtlasEditor
#

class LabelAtlasEditor(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LabelAtlasEditor"
    self.parent.categories = ["Segmentation"]
    self.parent.dependencies = []
    self.parent.contributors = ["Jessica Forbes (University of Iowa)", "Hans Johnson (University of Iowa)"]
    self.parent.helpText = """
    (1) The Label Merge widget allows a user to utilize a mask or a posterior probability
    map while merging the voxels of different labels in order to ensure that a voxel meets
    a user-defined minimum probability for a specific type, e.g., white matter or cerebrospinal
    fluid. (2) The Label Suggestion widget provides a list of candidate labels for a
    questionable group of voxels based on the neighborhood information attained from intensity
    images. (3) The Automatic Dust Cleanup widget automatically merges large amounts of small,
    disconnected regions to the most similar bordering label via the process employed in the
    Label Suggestion widget. We used the open-source image processing toolkit SimpleITK for
    processing the label atlases. For convenience, we included the 3D Slicer widgets Editor and
    Markups within this all-in-one module to expedite the manual cleaning process when required.
    Assuming that one label represents a single biological structure or densely packed structures,
    small isolated regions should be examined for validity. The open-source software OpenAtlas can
    be used for providing an excellent three-dimensional visualization of the disconnected
    ROIs. This tool identifies errors that are difficult to visually recognize in two-dimensional
    slices, by placing a fiducial point on each disconnected region. Within the Markups widget,
    the user selects a target region from the fiducial points to view and easily modify by using
    Editor or one of the custom widgets that we developed.
    """
    self.parent.acknowledgementText = """
    This project was funded by multiple grants: Huntington's Disease Society of America
    (Human Biology Project Fellowship), BRAINS (R01 NS050568), Validation of Structural/Functional
    MRI Localization (R01 EB000975), 3D Shape Analysis for Computational Anatomy (R01 EB008171),
    Neurobiological Predictors of HD (R01 NS040068), Cognitive and Functional Brain Changes in
    Preclinical HD (R01 NS054893), Algorithms for Functional and Anatomical Brain Analysis
    (P41 RR015241), Enterprise Storage in a Collaborative Neuroimaging Environment (S10 RR023392),
    Core 2b HD (U54 EB005149), and NIPYPE (R03 EB008673).
    """

#
# LabelAtlasEditorWidget
#

class LabelAtlasEditorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = LabelAtlasEditorLogic()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    if False:
        """Developer interface"""
        reloadCollapsibleButton = ctk.ctkCollapsibleButton()
        reloadCollapsibleButton.text = "Advanced - Reload && Test"
        reloadCollapsibleButton.collapsed = False
        self.layout.addWidget(reloadCollapsibleButton)
        reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

        # reload button
        # (use this during development, but remove it when delivering
        #  your module to users)
        self.reloadButton = qt.QPushButton("Reload")
        self.reloadButton.toolTip = "Reload this module."
        self.reloadButton.name = "Module Reload"
        reloadFormLayout.addWidget(self.reloadButton)
        self.reloadButton.connect('clicked()', self.onReload)

        # reload and test button
        # (use this during development, but remove it when delivering
        #  your module to users)
        self.reloadAndTestButton = qt.QPushButton("Reload and Test")
        self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
        reloadFormLayout.addWidget(self.reloadAndTestButton)
        self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #% Cast Label Map to Signed 16-bit Parameters Area %%
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    castParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    castParametersCollapsibleButton.text = "Cast Label Map to Signed 16-bit for use in Editor"
    castParametersCollapsibleButton.setContentsMargins(10, 30, 10, 10)
    self.layout.addWidget(castParametersCollapsibleButton)

    # Layout within the Cast Label Map Parameters Area collapsible button
    castParametersFormLayout = qt.QFormLayout(castParametersCollapsibleButton)

    #
    # input label map selector
    #
    self.inputCastLabelSelector = slicer.qMRMLNodeComboBox()
    self.inputCastLabelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputCastLabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.inputCastLabelSelector.selectNodeUponCreation = True
    self.inputCastLabelSelector.addEnabled = False
    self.inputCastLabelSelector.removeEnabled = False
    self.inputCastLabelSelector.noneEnabled = False
    self.inputCastLabelSelector.showHidden = False
    self.inputCastLabelSelector.showChildNodeTypes = False
    self.inputCastLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.inputCastLabelSelector.setToolTip( "Pick the input label map to the algorithm." )
    castParametersFormLayout.addRow("Input Label Map Volume: ", self.inputCastLabelSelector)
    
    #
    # output label map selector
    #
    self.outputCastLabelSelector = slicer.qMRMLNodeComboBox()
    self.outputCastLabelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputCastLabelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.outputCastLabelSelector.selectNodeUponCreation = True
    self.outputCastLabelSelector.addEnabled = True
    self.outputCastLabelSelector.renameEnabled = True
    self.outputCastLabelSelector.removeEnabled = True
    self.outputCastLabelSelector.noneEnabled = True
    self.outputCastLabelSelector.showHidden = False
    self.outputCastLabelSelector.showChildNodeTypes = False
    self.outputCastLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.outputCastLabelSelector.setToolTip( "Pick the output label map to the algorithm." )
    castParametersFormLayout.addRow("Output Label Map Volume: ", self.outputCastLabelSelector)

    #
    # Cast Apply Button
    #
    self.castApplyButton = qt.QPushButton("Apply")
    self.castApplyButton.toolTip = "Run the algorithm."
    self.castApplyButton.enabled = False
    self.castApplyButton.setStyleSheet("background-color: rgb(230,241,255)")
    castParametersFormLayout.addRow(self.castApplyButton)

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #% Automatic Dust Cleanup Parameters Area %%
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    automaticCleanupParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    automaticCleanupParametersCollapsibleButton.text = "Automatic Dust Cleanup"
    automaticCleanupParametersCollapsibleButton.setContentsMargins(10, 30, 10, 10)
    self.layout.addWidget(automaticCleanupParametersCollapsibleButton)

    # Layout within the Automatic Cleanup Parameters Area collapsible button
    automaticCleanupParametersFormLayout = qt.QFormLayout(automaticCleanupParametersCollapsibleButton)

    #
    # input volume selector for Automatic Cleanup Params
    #
    self.automaticCleanupParamsInputT1VolumeSelector = slicer.qMRMLNodeComboBox()
    self.automaticCleanupParamsInputT1VolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.automaticCleanupParamsInputT1VolumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )
    self.automaticCleanupParamsInputT1VolumeSelector.selectNodeUponCreation = True
    self.automaticCleanupParamsInputT1VolumeSelector.addEnabled = False
    self.automaticCleanupParamsInputT1VolumeSelector.removeEnabled = False
    self.automaticCleanupParamsInputT1VolumeSelector.noneEnabled = False
    self.automaticCleanupParamsInputT1VolumeSelector.showHidden = False
    self.automaticCleanupParamsInputT1VolumeSelector.showChildNodeTypes = False
    self.automaticCleanupParamsInputT1VolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.automaticCleanupParamsInputT1VolumeSelector.setToolTip( "Pick the input to the algorithm." )
    automaticCleanupParametersFormLayout.addRow("Input Intensity Volume 1: ", self.automaticCleanupParamsInputT1VolumeSelector)

    #
    # input volume selector for Automatic Cleanup Params
    #
    self.automaticCleanupParamsInputT2VolumeSelector = slicer.qMRMLNodeComboBox()
    self.automaticCleanupParamsInputT2VolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.automaticCleanupParamsInputT2VolumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )
    self.automaticCleanupParamsInputT2VolumeSelector.selectNodeUponCreation = True
    self.automaticCleanupParamsInputT2VolumeSelector.addEnabled = False
    self.automaticCleanupParamsInputT2VolumeSelector.removeEnabled = False
    self.automaticCleanupParamsInputT2VolumeSelector.noneEnabled = True
    self.automaticCleanupParamsInputT2VolumeSelector.showHidden = False
    self.automaticCleanupParamsInputT2VolumeSelector.showChildNodeTypes = False
    self.automaticCleanupParamsInputT2VolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.automaticCleanupParamsInputT2VolumeSelector.setToolTip( "Pick the input to the algorithm." )
    automaticCleanupParametersFormLayout.addRow("Input Intensity Volume 2 (optional): ", self.automaticCleanupParamsInputT2VolumeSelector)
    
    #
    # input label map selector for Automatic Cleanup Params
    #
    self.automaticCleanupParamsInputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.automaticCleanupParamsInputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.automaticCleanupParamsInputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.automaticCleanupParamsInputSelectorLabel.selectNodeUponCreation = True
    self.automaticCleanupParamsInputSelectorLabel.addEnabled = False
    self.automaticCleanupParamsInputSelectorLabel.removeEnabled = False
    self.automaticCleanupParamsInputSelectorLabel.noneEnabled = False
    self.automaticCleanupParamsInputSelectorLabel.showHidden = False
    self.automaticCleanupParamsInputSelectorLabel.showChildNodeTypes = False
    self.automaticCleanupParamsInputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.automaticCleanupParamsInputSelectorLabel.setToolTip( "Pick the input label map to the algorithm." )
    automaticCleanupParametersFormLayout.addRow("Input Label Map Volume: ", self.automaticCleanupParamsInputSelectorLabel)

    #
    # output label map selector for Automatic Cleanup Params
    #
    self.automaticCleanupParamsOutputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.automaticCleanupParamsOutputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.automaticCleanupParamsOutputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.automaticCleanupParamsOutputSelectorLabel.selectNodeUponCreation = True
    self.automaticCleanupParamsOutputSelectorLabel.addEnabled = True
    self.automaticCleanupParamsOutputSelectorLabel.renameEnabled = True
    self.automaticCleanupParamsOutputSelectorLabel.removeEnabled = True
    self.automaticCleanupParamsOutputSelectorLabel.noneEnabled = True
    self.automaticCleanupParamsOutputSelectorLabel.showHidden = False
    self.automaticCleanupParamsOutputSelectorLabel.showChildNodeTypes = False
    self.automaticCleanupParamsOutputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.automaticCleanupParamsOutputSelectorLabel.setToolTip( "Pick the output label map to the algorithm." )
    automaticCleanupParametersFormLayout.addRow("Output Label Map Volume: ", self.automaticCleanupParamsOutputSelectorLabel)

    self.maximumIslandVoxelCount = ctk.ctkSliderWidget()
    self.maximumIslandVoxelCount.singleStep = 1.0
    self.maximumIslandVoxelCount.minimum = 1.0
    self.maximumIslandVoxelCount.maximum = 1000.0
    self.maximumIslandVoxelCount.value = 1.0
    self.maximumIslandVoxelCount.setToolTip('Integer value of maximum island voxel count to correct')
    automaticCleanupParametersFormLayout.addRow("Maximum island voxel count: ", self.maximumIslandVoxelCount)

    #
    # TextEditBoxWidget for includeLabelsList for Automatic Cleanup Params
    #
    self.includeLabelsList = qt.QTextEdit()
    self.includeLabelsList.setToolTip("Integer list of labels to review (Ex: 3,6,99)")
    self.includeLabelsList.setMaximumHeight(25)
    automaticCleanupParametersFormLayout.addRow("Integer list of labels to review (optional) \n(Ex: 3,6,99)", self.includeLabelsList)

    #
    # TextEditBoxWidget for excludeLabelsList for Automatic Cleanup Params
    #
    self.excludeLabelsList = qt.QTextEdit()
    self.excludeLabelsList.setToolTip("Integer list of labels to exclude from review (Ex: 12,100)")
    self.excludeLabelsList.setMaximumHeight(25)
    automaticCleanupParametersFormLayout.addRow("Integer list of labels to exclude from\nreview (optional) (Ex: 12,100)\n", self.excludeLabelsList)

    #
    # check box to dilate for Automatic Cleanup Params
    #
    self.noDilationCheckBox = qt.QCheckBox()
    self.noDilationCheckBox.checked = 1
    self.noDilationCheckBox.setToolTip("Do not dilate islands when determining connectivity")
    automaticCleanupParametersFormLayout.addRow("Do not dilate islands when \ndetermining connectivity\n", self.noDilationCheckBox)

    #
    # check box to use the Fully Connected in the Connected Component Filter for Automatic Cleanup Params
    #
    self.useFullyConnectedInConnectedComponentFilterCheckBox = qt.QCheckBox()
    self.useFullyConnectedInConnectedComponentFilterCheckBox.checked = 0
    self.useFullyConnectedInConnectedComponentFilterCheckBox.setToolTip("Build islands using 8-neighbor (full) connectivity (default is to build islands using 4-neighbor (face) connectivity)")
    automaticCleanupParametersFormLayout.addRow("Build islands using 8-neighbor (full) \nconnectivity (default is to build islands \nusing 4-neighbor (face) connectivity)\n", self.useFullyConnectedInConnectedComponentFilterCheckBox)

    #
    # check box to force the current label to another label for Automatic Cleanup Params
    #
    self.forceSuspiciousLabelChangeCheckBox = qt.QCheckBox()
    self.forceSuspiciousLabelChangeCheckBox.checked = 0
    self.forceSuspiciousLabelChangeCheckBox.setToolTip("Forces reviewed islands of voxels to change to a different label ")
    automaticCleanupParametersFormLayout.addRow("Force reviewed islands of voxels \nto change to a different label\n", self.forceSuspiciousLabelChangeCheckBox)

    #
    # Apply Button for the Automatic Cleanup widget
    #
    self.automaticCleanupParamsButton = qt.QPushButton("Apply")
    self.automaticCleanupParamsButton.toolTip = "Run the algorithm."
    self.automaticCleanupParamsButton.enabled = True
    self.automaticCleanupParamsButton.setStyleSheet("background-color: rgb(230,241,255)")
    automaticCleanupParametersFormLayout.addRow(self.automaticCleanupParamsButton)

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #% Label Suggestion Parameters Area %%
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    labelParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    labelParametersCollapsibleButton.text = "Label Suggestion"
    labelParametersCollapsibleButton.setContentsMargins(10, 30, 10, 10)
    self.layout.addWidget(labelParametersCollapsibleButton)

    # Layout within the Label Suggestion Parameters Area collapsible button
    labelParametersFormLayout = qt.QFormLayout(labelParametersCollapsibleButton)
    
    #
    # input volume selector for Label Suggestion Params
    #
    self.labelParamsInputT1VolumeSelector = slicer.qMRMLNodeComboBox()
    self.labelParamsInputT1VolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.labelParamsInputT1VolumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )
    self.labelParamsInputT1VolumeSelector.selectNodeUponCreation = True
    self.labelParamsInputT1VolumeSelector.addEnabled = False
    self.labelParamsInputT1VolumeSelector.removeEnabled = False
    self.labelParamsInputT1VolumeSelector.noneEnabled = False
    self.labelParamsInputT1VolumeSelector.showHidden = False
    self.labelParamsInputT1VolumeSelector.showChildNodeTypes = False
    self.labelParamsInputT1VolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.labelParamsInputT1VolumeSelector.setToolTip( "Pick the input to the algorithm." )
    labelParametersFormLayout.addRow("Input Intensity Volume 1: ", self.labelParamsInputT1VolumeSelector)
    
    #
    # input volume selector for Label Suggestion Params
    #
    self.labelParamsInputT2VolumeSelector = slicer.qMRMLNodeComboBox()
    self.labelParamsInputT2VolumeSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.labelParamsInputT2VolumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )
    self.labelParamsInputT2VolumeSelector.selectNodeUponCreation = True
    self.labelParamsInputT2VolumeSelector.addEnabled = False
    self.labelParamsInputT2VolumeSelector.removeEnabled = False
    self.labelParamsInputT2VolumeSelector.noneEnabled = False
    self.labelParamsInputT2VolumeSelector.showHidden = False
    self.labelParamsInputT2VolumeSelector.showChildNodeTypes = False
    self.labelParamsInputT2VolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.labelParamsInputT2VolumeSelector.setToolTip( "Pick the input to the algorithm." )
    labelParametersFormLayout.addRow("Input Intensity Volume 2: ", self.labelParamsInputT2VolumeSelector)
    
    #
    # input label map selector for Label Suggestion Params
    #
    self.labelParamsInputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.labelParamsInputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.labelParamsInputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.labelParamsInputSelectorLabel.selectNodeUponCreation = True
    self.labelParamsInputSelectorLabel.addEnabled = False
    self.labelParamsInputSelectorLabel.removeEnabled = False
    self.labelParamsInputSelectorLabel.noneEnabled = False
    self.labelParamsInputSelectorLabel.showHidden = False
    self.labelParamsInputSelectorLabel.showChildNodeTypes = False
    self.labelParamsInputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.labelParamsInputSelectorLabel.setToolTip( "Pick the input label map to the algorithm." )
    labelParametersFormLayout.addRow("Input Label Map Volume: ", self.labelParamsInputSelectorLabel)

    #
    # output label map selector for Label Suggestion Params
    #
    self.labelParamsOutputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.labelParamsOutputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.labelParamsOutputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.labelParamsOutputSelectorLabel.selectNodeUponCreation = True
    self.labelParamsOutputSelectorLabel.addEnabled = True
    self.labelParamsOutputSelectorLabel.renameEnabled = True
    self.labelParamsOutputSelectorLabel.removeEnabled = True
    self.labelParamsOutputSelectorLabel.noneEnabled = True
    self.labelParamsOutputSelectorLabel.showHidden = False
    self.labelParamsOutputSelectorLabel.showChildNodeTypes = False
    self.labelParamsOutputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.labelParamsOutputSelectorLabel.setToolTip( "Pick the output label map to the algorithm." )
    labelParametersFormLayout.addRow("Output Label Map Volume: ", self.labelParamsOutputSelectorLabel)

    #
    # Add fiducial Button for Label Suggestion Params
    #
    self.labelParamsAddFiducialButton = qt.QPushButton("Add fiducial point")
    self.labelParamsAddFiducialButton.toolTip = "Add the fiducial point."
    self.labelParamsAddFiducialButton.enabled = True
    self.labelParamsAddFiducialButton.setStyleSheet("background-color: rgb(230,241,255)")
    labelParametersFormLayout.addRow("Step 1:", self.labelParamsAddFiducialButton)

    #
    # Calculate Square Diffs of Means Button for Label Suggestion Params
    #
    self.labelParamsApplyButton = qt.QPushButton("Calculate Square Diffs of Means")
    self.labelParamsApplyButton.toolTip = "Run the algorithm."
    self.labelParamsApplyButton.enabled = True
    self.labelParamsApplyButton.setStyleSheet("background-color: rgb(230,241,255)")
    labelParametersFormLayout.addRow("Step 2:", self.labelParamsApplyButton)

    # model and view for stats table for Label Suggestion Params
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    self.view.setMaximumHeight(0)
    labelParametersFormLayout.addWidget(self.view)

    #
    # Apply Button for Label Suggestion Params
    #
    self.labelParamsRelabelButton = qt.QPushButton("Relabel output label map to checked label")
    self.labelParamsRelabelButton.toolTip = "Run the algorithm."
    self.labelParamsRelabelButton.enabled = True
    self.labelParamsRelabelButton.setStyleSheet("background-color: rgb(230,241,255)")
    labelParametersFormLayout.addRow("Step 3:", self.labelParamsRelabelButton)

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    #% Merge Suspicious Label to Target Label Parameters Area %%
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Merge Suspicious Label to Target Label"
    parametersCollapsibleButton.setContentsMargins(10, 30, 10, 10)
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the Parameters Area collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input label map selector
    #
    self.inputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.inputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.inputSelectorLabel.selectNodeUponCreation = True
    self.inputSelectorLabel.addEnabled = False
    self.inputSelectorLabel.removeEnabled = False
    self.inputSelectorLabel.noneEnabled = False
    self.inputSelectorLabel.showHidden = False
    self.inputSelectorLabel.showChildNodeTypes = False
    self.inputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.inputSelectorLabel.setToolTip( "Pick the input label map to the algorithm." )
    parametersFormLayout.addRow("Input Label Map Volume: ", self.inputSelectorLabel)

    self.targetLabel = ctk.ctkSliderWidget()
    self.targetLabel.singleStep = 1.0
    self.targetLabel.minimum = 0.0
    self.targetLabel.maximum = 30000.0
    self.targetLabel.value = 24.0
    self.targetLabel.setToolTip('Set the target label (label to change suspicious label to)')
    parametersFormLayout.addRow("Target Label: ", self.targetLabel)
    
    self.suspiciousLabel = ctk.ctkSliderWidget()
    self.suspiciousLabel.singleStep = 1.0
    self.suspiciousLabel.minimum = 0.0
    self.suspiciousLabel.maximum = 30000.0
    self.suspiciousLabel.value = 999.0
    self.suspiciousLabel.setToolTip('Set the suspicious label (will be changed to target '
                                    'label if connected in largest region')
    parametersFormLayout.addRow("Suspicious Label: ", self.suspiciousLabel)

    #
    # check box to trigger using the posterior parameters
    #
    self.mergeAllIslandCheckBox = qt.QCheckBox()
    self.mergeAllIslandCheckBox.checked = 0
    self.mergeAllIslandCheckBox.setToolTip("If checked, will use posterior image and threshold")
    parametersFormLayout.addRow("Merge suspicious pixels connected to any \ntarget island (not just largest island)", self.mergeAllIslandCheckBox)

    #
    # Posterior Parameters Area
    #
    self.posteriorParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    self.posteriorParametersCollapsibleButton.text = "Posterior parameters"
    self.posteriorParametersCollapsibleButton.collapsed = True
    self.posteriorParametersCollapsibleButton.setContentsMargins(20, 40, 20, 20)
    parametersFormLayout.addRow(self.posteriorParametersCollapsibleButton)

    # Layout within the Parameters Area collapsible button
    self.posteriorParametersFormLayout = qt.QFormLayout(self.posteriorParametersCollapsibleButton)

    # parametersFormLayout.addRow(posteriorParametersFormLayout)

    #
    # check box to trigger using the posterior parameters
    #
    self.enablePosteriorCheckBox = qt.QCheckBox()
    self.enablePosteriorCheckBox.checked = 0
    self.enablePosteriorCheckBox.setToolTip("If checked, will use posterior image and threshold")
    self.posteriorParametersFormLayout.addRow("Enable Posterior Parameters", self.enablePosteriorCheckBox)

    #
    # input posterior volume selector
    #
    self.inputSelectorPosterior = slicer.qMRMLNodeComboBox()
    self.inputSelectorPosterior.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorPosterior.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )
    self.inputSelectorPosterior.selectNodeUponCreation = True
    self.inputSelectorPosterior.addEnabled = False
    self.inputSelectorPosterior.removeEnabled = False
    self.inputSelectorPosterior.noneEnabled = True
    self.inputSelectorPosterior.showHidden = False
    self.inputSelectorPosterior.showChildNodeTypes = False
    self.inputSelectorPosterior.setMRMLScene( slicer.mrmlScene )
    self.inputSelectorPosterior.setStyleSheet("color: rgb(230,241,255)")
    self.inputSelectorPosterior.setToolTip( "Pick the input to the algorithm." )
    self.posteriorParametersFormLayout.addRow("Posterior Volume: ", self.inputSelectorPosterior)

    #
    # input posterior threshold selector
    #
    self.posteriorThreshold = ctk.ctkSliderWidget()
    self.posteriorThreshold.singleStep = 0.01
    self.posteriorThreshold.minimum = 0.0
    self.posteriorThreshold.maximum = 10000.0
    self.posteriorThreshold.value = 0.1
    self.posteriorThreshold.setStyleSheet("color: rgb(230,241,255)")
    self.posteriorThreshold.setToolTip('Set the threshold for the posterior image (only pixels '
                                       'above this threshold will be changed')
    self.posteriorParametersFormLayout.addRow("Minimum threshold for posterior volume: ", self.posteriorThreshold)

    #
    # output label map selector
    #
    self.outputSelectorLabel = slicer.qMRMLNodeComboBox()
    self.outputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelectorLabel.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "1" )
    self.outputSelectorLabel.selectNodeUponCreation = True
    self.outputSelectorLabel.addEnabled = True
    self.outputSelectorLabel.renameEnabled = True
    self.outputSelectorLabel.removeEnabled = True
    self.outputSelectorLabel.noneEnabled = True
    self.outputSelectorLabel.showHidden = False
    self.outputSelectorLabel.showChildNodeTypes = False
    self.outputSelectorLabel.setMRMLScene( slicer.mrmlScene )
    self.outputSelectorLabel.setToolTip( "Pick the output label map to the algorithm." )
    parametersFormLayout.addRow("Output Label Map Volume: ", self.outputSelectorLabel)

    #
    # Adds the Editor Widget
    #
    self.localEditorWidget = Editor.EditorWidget(parent=self.parent, showVolumesFrame=True)
    self.localEditorWidget.setup()
    self.localEditorWidget.enter()

    #
    # Markups Area
    #
    markupsCollapsibleButton = ctk.ctkCollapsibleButton()
    markupsCollapsibleButton.text = "Markups"
    self.layout.addWidget(markupsCollapsibleButton)

    # Layout within the Markups Area collapsible button
    markupsFormLayout = qt.QFormLayout(markupsCollapsibleButton)

    #
    # Adds the Markups widget
    #
    self.localMarkupsWidget = slicer.modules.markups.widgetRepresentation()
    self.localMarkupsWidget.setParent(self.parent)
    markupsFormLayout.addRow(self.localMarkupsWidget)
    self.localMarkupsWidget.show()

    #
    # Models Area
    #
    modelsCollapsibleButton = ctk.ctkCollapsibleButton()
    modelsCollapsibleButton.text = "Models"
    self.layout.addWidget(modelsCollapsibleButton)

    # Layout within the Models Area collapsible button
    modelsFormLayout = qt.QFormLayout(modelsCollapsibleButton)

    #
    # Adds the Models widget
    #
    self.localModelsWidget = slicer.modules.models.widgetRepresentation()
    self.localModelsWidget.setParent(self.parent)
    modelsFormLayout.addRow(self.localModelsWidget)
    self.localModelsWidget.show()

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    self.applyButton.setStyleSheet("background-color: rgb(230,241,255)")
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.castApplyButton.connect('clicked(bool)', self.onCastApplyButton)
    self.inputCastLabelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onCastSelect)
    self.outputCastLabelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onCastSelect)
    self.automaticCleanupParamsButton.connect('clicked(bool)', self.onAutomaticCleanupParamsButton)
    self.labelParamsApplyButton.connect('clicked(bool)', self.onLabelParamsApplyButton)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelectorLabel.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputSelectorPosterior.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelectorLabel.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.enablePosteriorCheckBox.connect('clicked(bool)', self.onEnablePosteriorSelect)
    self.labelParamsAddFiducialButton.connect('clicked(bool)', self.onlabelParamsAddFiducialButton)
    self.labelParamsRelabelButton.connect('clicked(bool)', self.onRelabelApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onCastSelect(self):
    self.castApplyButton.enabled = self.inputCastLabelSelector.currentNode() \
                                   and self.outputCastLabelSelector.currentNode()

  def onSelect(self):
    if not self.enablePosteriorCheckBox.checked:
      self.applyButton.enabled = self.inputSelectorLabel.currentNode() \
                                 and self.outputSelectorLabel.currentNode()
    else:
      self.applyButton.enabled = self.inputSelectorLabel.currentNode() \
                                 and self.inputSelectorPosterior.currentNode() \
                                 and self.outputSelectorLabel.currentNode()

  def onCastApplyButton(self):
    self.logic.runCast(self.inputCastLabelSelector.currentNode(),
                  self.outputCastLabelSelector.currentNode())

  def onAutomaticCleanupParamsButton(self):
    self.automaticCleanupParamsButton.text = "Working..."
    self.automaticCleanupParamsButton.repaint()
    slicer.app.processEvents()
    arguments = {'--inputAtlasPath': self.automaticCleanupParamsInputSelectorLabel.currentNode().GetName(),
                 '--inputT1Path': self.automaticCleanupParamsInputT1VolumeSelector.currentNode().GetName(),
                 '--outputAtlasPath': self.automaticCleanupParamsOutputSelectorLabel.currentNode().GetName(),
                 '--includeLabelsList': str(self.includeLabelsList.toPlainText()),
                 '--excludeLabelsList': str(self.excludeLabelsList.toPlainText()),
                 '--maximumIslandVoxelCount': int(self.maximumIslandVoxelCount.value),
                 '--noDilation': self.noDilationCheckBox.checked,
                 '--useFullyConnectedInConnectedComponentFilter': self.useFullyConnectedInConnectedComponentFilterCheckBox.checked,
                 '--forceSuspiciousLabelChange': self.forceSuspiciousLabelChangeCheckBox.checked
                 }
    if self.automaticCleanupParamsInputT2VolumeSelector.currentNode():
        arguments['--inputT2Path'] = self.automaticCleanupParamsInputT2VolumeSelector.currentNode().GetName()
    else:
        arguments['--inputT2Path'] = None
    print arguments
    localDustCleanupObject = LocalDustCleanup(arguments=arguments)
    localDustCleanupObject.main()
    self.automaticCleanupParamsButton.text = "Apply"

  def onLabelParamsApplyButton(self):
    self.logic.runGetRegionInfo(self.labelParamsInputSelectorLabel.currentNode().GetName(),
                           self.labelParamsInputT1VolumeSelector.currentNode(),
                           self.labelParamsInputT2VolumeSelector.currentNode())
    self.populateStats()

  def onlabelParamsAddFiducialButton(self):
    self.logic.runAddFiducial()

  def onRelabelApplyButton(self):
    self.logic.runRelabelOutputLabelMap(self.labelParamsInputSelectorLabel.currentNode(),
                                        self.labelParamsOutputSelectorLabel.currentNode().GetName(),
                                        self.items)

  def onApplyButton(self):
    self.applyButton.text = "Working..."
    self.applyButton.repaint()
    slicer.app.processEvents()

    print("Merge Apply button selected")

    if not self.enablePosteriorCheckBox.checked:
      self.logic.run(self.inputSelectorLabel.currentNode().GetName(),
              self.outputSelectorLabel.currentNode().GetName(),
              self.targetLabel.value, self.suspiciousLabel.value,
              self.mergeAllIslandCheckBox.checked)
    else:
      self.logic.run(self.inputSelectorLabel.currentNode().GetName(),
              self.outputSelectorLabel.currentNode().GetName(),
              self.targetLabel.value, self.suspiciousLabel.value,
              self.mergeAllIslandCheckBox.checked,
              enablePosterior=True,
              inputPosteriorName=self.inputSelectorPosterior.currentNode().GetName(),
              posteriorThreshold=self.posteriorThreshold.value)
    self.applyButton.text = "Apply"

  def onEnablePosteriorSelect(self):
    self.onSelect()
    if not self.enablePosteriorCheckBox.checked:
      self.inputSelectorPosterior.setStyleSheet("color: rgb(230,241,255)")
      self.posteriorThreshold.setStyleSheet("color: rgb(230,241,255)")
    else:
      self.inputSelectorPosterior.setStyleSheet("color: rgb(0,0,0)")
      self.posteriorThreshold.setStyleSheet("color: rgb(0,0,0)")

  def populateStats(self):
    self.tableColumnNames = ['Label Number', 'Label Name', 'Square Diff of Means']

    if not self.logic:
      return
    displayNode = self.labelParamsInputSelectorLabel.currentNode().GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    labelDict = self.logic.squareRootDiffLabelDict
    for i in sorted(labelDict, key=labelDict.get, reverse=False):
      color = qt.QColor()
      rgb = lut.GetTableValue(i)
      color.setRgb(rgb[0]*255, rgb[1]*255, rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,qt.Qt.DecorationRole)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row, 0, item)
      self.items.append(item)

      # write Label Number column
      item = qt.QStandardItem()
      item.setData(float(i), qt.Qt.DisplayRole)
      item.setToolTip(colorNode.GetColorName(i))
      item.setCheckable(True)
      self.model.setItem(row, 1, item)
      self.items.append(item)

      # write Label Name column
      item = qt.QStandardItem()
      item.setData(colorNode.GetColorName(i), qt.Qt.DisplayRole)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row, 2, item)
      self.items.append(item)

      # write Square Diff of Means column
      item = qt.QStandardItem()
      item.setData(float(self.logic.squareRootDiffLabelDict[i]), qt.Qt.DisplayRole)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row, 3, item)
      self.items.append(item)

      row += 1

    self.view.setMinimumHeight(self.view.rowHeight(0) * 5 + 10)
    self.view.setMaximumHeight(self.view.rowHeight(0) * 5 + 10)
    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    col = 1
    for k in self.tableColumnNames:
      self.view.setColumnWidth(col,10*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1

#
# LabelAtlasEditorLogic
#

class LabelAtlasEditorLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

  def run(self, inputLabelName, outputLabelName, targetLabel, suspiciousLabel, mergeAllIslandsChecked,
          enablePosterior=False, inputPosteriorName=None, posteriorThreshold=None):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running')

    newLabel = self.mergeLabels(inputLabelName, targetLabel, suspiciousLabel, mergeAllIslandsChecked,
                                enablePosterior, inputPosteriorName, posteriorThreshold)

    inputNode = slicer.util.getNode(pattern=inputLabelName)
    inputLabelNodeLUTNodeID = inputNode.GetDisplayNode().GetColorNodeID()

    su.PushLabel(newLabel, outputLabelName, overwrite=True)
    self.setLabelLUT(outputLabelName, inputLabelNodeLUTNodeID)

    return True

  def mergeLabels(self, labelImageName, targetLabel, suspiciousLabel, mergeAllIslandsChecked,
                  enablePosterior, inputPosteriorName, posteriorThreshold):
    labelImage = su.PullFromSlicer(labelImageName)
    targetLabelMask = sitk.BinaryThreshold(labelImage, targetLabel, targetLabel)
    suspiciousLabelMask = sitk.BinaryThreshold(labelImage, suspiciousLabel, suspiciousLabel)
    targetAndSuspiciousMergedLabel = sitk.Add(targetLabelMask, suspiciousLabelMask)
    connectedRegion = sitk.ConnectedComponent(targetAndSuspiciousMergedLabel, True)
    relabeledConnectedRegion = sitk.RelabelComponent(connectedRegion)
    if not enablePosterior:
      if mergeAllIslandsChecked == False:
        newRegion = sitk.BinaryThreshold(relabeledConnectedRegion, 1, 1)
        print('no thresh used')
      else:
        newRegion = sitk.BinaryThreshold(relabeledConnectedRegion, 1)
        print('no thresh used')
    else:
      print('threshold used: ', posteriorThreshold)
      posterior = su.PullFromSlicer(inputPosteriorName)
      thresholdedPosterior = sitk.BinaryThreshold(posterior, posteriorThreshold)
      if mergeAllIslandsChecked == False:
        relabeledMask = sitk.BinaryThreshold(relabeledConnectedRegion, 1, 1)
      else:
        relabeledMask = sitk.BinaryThreshold(relabeledConnectedRegion, 1)
      newRegion = sitk.Multiply(relabeledMask, thresholdedPosterior)
    newLabel = self.relabelImage(labelImage, newRegion, targetLabel)
    return newLabel

  def setLabelLUT(self, nodeName, colorNodeID):
    outputNode = slicer.util.getNode(pattern=nodeName)
    outputLabelDisplayNode = outputNode.GetDisplayNode()
    outputLabelDisplayNode.SetAndObserveColorNodeID(colorNodeID)

  def runCast(self, inputNode, outputNode):
    inputName = inputNode.GetName()
    inputImage = su.PullFromSlicer(inputName)
    outputImage = sitk.Cast(inputImage, sitk.sitkInt16)
    inputLabelNodeLUTNodeID = inputNode.GetDisplayNode().GetColorNodeID()
    outputName = outputNode.GetName()
    su.PushLabel(outputImage, outputName, overwrite=True)
    self.setLabelLUT(outputName, inputLabelNodeLUTNodeID)

    return True

  def runAddFiducial(self):
    fiducialName = 'DustCleanupModuleFiducialNode'

    fiducialNode = slicer.util.getNode(fiducialName)
    if fiducialNode != None:
      slicer.mrmlScene.RemoveNode(fiducialNode)

    markupsLogic = slicer.modules.markups.logic()
    markupsLogic.AddNewFiducialNode(fiducialName)

    placeModePersistence = 0
    markupsLogic.StartPlaceMode(placeModePersistence)

  def runGetRegionInfo(self, inputLabelName, inputT1VolumeNode,
                       inputT2VolumeNode):

    fiducialName = 'DustCleanupModuleFiducialNode'
    fiducialNode = slicer.util.getNode(fiducialName)

    seedList = self.createSeedList(fiducialNode, inputT1VolumeNode)
    inputLabelImage = self.getSitkInt16ImageFromSlicer(inputLabelName)
    suspiciousLabel = self.getLabel(inputLabelImage, seedList)
    self.connectedThresholdOutput = self.runConnectedThresholdImageFilter(suspiciousLabel, seedList, inputLabelImage)

    inputT1VolumeImage = self.getSitkInt16ImageFromSlicer(inputT1VolumeNode.GetName())
    inputT2VolumeImage = self.getSitkInt16ImageFromSlicer(inputT2VolumeNode.GetName())

    dialatedBinaryLabelMap = self.dialateLabelMap(self.connectedThresholdOutput)
    reducedLabelMapImage = sitk.Multiply(dialatedBinaryLabelMap, inputLabelImage)

    reducedLabelMapT1LabelStats = self.getLabelStatsObject(inputT1VolumeImage, reducedLabelMapImage)
    reducedLabelMapT2LabelStats = self.getLabelStatsObject(inputT2VolumeImage, reducedLabelMapImage)
    targetLabels = reducedLabelMapT1LabelStats.GetLabels()

    labelImageWithoutSuspiciousIslandPixels = self.relabelImage(inputLabelImage, self.connectedThresholdOutput, 0)

    T1LabelStats = self.getLabelStatsObject(inputT1VolumeImage, labelImageWithoutSuspiciousIslandPixels)
    T2LabelStats = self.getLabelStatsObject(inputT2VolumeImage, labelImageWithoutSuspiciousIslandPixels)

    self.printLabelStatistics(reducedLabelMapT1LabelStats)
    self.squareRootDiffLabelDict = self.calculateLabelIntensityDifferenceValue(
                              reducedLabelMapT1LabelStats.GetMean(int(suspiciousLabel)),
                              reducedLabelMapT2LabelStats.GetMean(int(suspiciousLabel)),
                              targetLabels, T1LabelStats, T2LabelStats)

    print self.squareRootDiffLabelDict

    return True

  def getLabel(self, inputLabelImage, seedList):

    return int(inputLabelImage.GetPixel(seedList[0][0], seedList[0][1], seedList[0][2]))

  def getLabelStatsObject(self, volumeImage, labelImage):
    labelStatsObject = sitk.LabelStatisticsImageFilter()
    labelStatsObject.Execute(volumeImage, labelImage)

    return labelStatsObject

  def getSitkInt16ImageFromSlicer(self, volumeName):
    volume = su.PullFromSlicer(volumeName)
    castedVolume = sitk.Cast(volume, sitk.sitkInt16)

    return castedVolume

  def runConnectedThresholdImageFilter(self, label, seedList, inputLabelImage):
    myFilter = sitk.ConnectedThresholdImageFilter()
    myFilter.SetConnectivity(1)
    myFilter.SetDebug(False)
    myFilter.SetLower(label)
    myFilter.SetNumberOfThreads(8)
    myFilter.SetReplaceValue(1)
    myFilter.SetUpper(label)
    myFilter.SetSeedList(seedList)
    output = myFilter.Execute(inputLabelImage)
    castedOutput = sitk.Cast(output, sitk.sitkInt16)

    return castedOutput

  def dialateLabelMap(self, inputLabelImage):
    myFilter = sitk.BinaryDilateImageFilter()
    myFilter.SetBackgroundValue(0.0)
    myFilter.SetBoundaryToForeground(False)
    myFilter.SetDebug(False)
    myFilter.SetForegroundValue(1.0)
    myFilter.SetKernelRadius((1, 1, 1))
    myFilter.SetKernelType(2)  # Kernel Type=Box
    myFilter.SetNumberOfThreads(8)
    output = myFilter.Execute(inputLabelImage)
    castedOutput = sitk.Cast(output, sitk.sitkInt16)

    return castedOutput

  def calculateLabelIntensityDifferenceValue(self, averageT1IntensitySuspiciousLabel,
                                             averageT2IntensitySuspiciousLabel,
                                             targetLabels, T1LabelStats, T2LabelStats):
    """
    Calculates a measurement for each label that is on the border of the suspicious label.
    This value is the square root of the sum of the squared difference in the average T1
    intensity values and the squared difference in the average T2 intensity values of the
    two islands in the comparison. The calculated value for each border label will later be
    sorted in ascending order - meaning that the smallest value has the "closest" average
    intensity to the suspicious label.
    """

    squareRootDiffLabelDict = dict()

    for targetLabel in targetLabels:
      if targetLabel == 0:
        continue
      averageT1IntensityTargetLabel = T1LabelStats.GetMean(targetLabel)
      averageT2IntensityTargetLabel = T2LabelStats.GetMean(targetLabel)

      squareDiffAverageT1 = math.pow(averageT1IntensitySuspiciousLabel -
                                     averageT1IntensityTargetLabel, 2)
      squareDiffAverageT2 = math.pow(averageT2IntensitySuspiciousLabel -
                                     averageT2IntensityTargetLabel, 2)
      squareRootDiff = math.sqrt(squareDiffAverageT1 + squareDiffAverageT2)

      squareRootDiffLabelDict[int(targetLabel)] = squareRootDiff

    return squareRootDiffLabelDict

  def runRelabelOutputLabelMap(self, inputLabelNode, outputLabelNodeName, items):
    inputLabelNodeLUTNodeID = inputLabelNode.GetDisplayNode().GetColorNodeID()
    for item in items:
      if item.checkState() == 2:
        print('Changing the suspicious label to', int(item.text()))
        labelImage = self.getSitkInt16ImageFromSlicer(inputLabelNode.GetName())
        relabeledImage = self.relabelImage(labelImage, self.connectedThresholdOutput, int(item.text()))
        su.PushLabel(relabeledImage, outputLabelNodeName, overwrite=True)
        self.setLabelLUT(outputLabelNodeName, inputLabelNodeLUTNodeID)

  def relabelImage(self, labelImage, newRegion, newLabel):
    castedLabelImage = sitk.Cast(labelImage, sitk.sitkInt16)
    castedNewRegion = sitk.Cast(newRegion, sitk.sitkInt16)
    negatedMask = sitk.BinaryNot(castedNewRegion)
    negatedImage = sitk.Mask(castedLabelImage, negatedMask)
    maskTimesNewLabel = sitk.Multiply(castedNewRegion, newLabel)
    relabeledImage = sitk.Add(negatedImage, maskTimesNewLabel)

    return relabeledImage

  def printLabelStatistics(self, labelStatsObject):
    for val in labelStatsObject.GetLabels():
      print 'Label:', int(val)
      print('Count:', labelStatsObject.GetCount(val))
      print('Mean:', labelStatsObject.GetMean(val))
      print('Standard Deviation:', labelStatsObject.GetSigma(val))
      print('Minimum:', labelStatsObject.GetMinimum(val))
      print('Maximum:', labelStatsObject.GetMaximum(val))

  def createSeedList(self, inputFiducialNode, inputVolumeNode):
    seedList = list()
    ras2ijk = self.getRas2ijkMatrix(inputVolumeNode)
    for val in range(0, inputFiducialNode.GetNumberOfFiducials()):
      rasPoint = [0, 0, 0, 0]
      inputFiducialNode.GetNthFiducialWorldCoordinates(val, rasPoint)
      ijkPoint = self.getIJKFromRAS(rasPoint, ras2ijk)
      seedList.append(ijkPoint)

    return seedList[0:1]

  def getRas2ijkMatrix(self, volumeNode):
    ras2ijk = vtk.vtkMatrix4x4()
    volumeNode.GetRASToIJKMatrix(ras2ijk)

    return ras2ijk

  def getIJKFromRAS(self, rasPoint, ras2ijk):
    ijkPoint = [int(round(c)) for c in ras2ijk.MultiplyPoint(rasPoint)[:3]]

    return ijkPoint

class LabelAtlasEditorTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_LabelAtlasEditor1()

  def test_LabelAtlasEditor1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = LabelAtlasEditorLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

class LocalDustCleanup(DustCleanup):
  def main(self):
    labelImage = su.PullFromSlicer(self.inputAtlasPath)
    inputT1VolumeImage = su.PullFromSlicer(self.inputT1Path)
    if self.inputT2Path:
      inputT2VolumeImage = su.PullFromSlicer(self.inputT2Path)
    else:
      inputT2VolumeImage = None
    labelsList = self.getLabelsList(inputT1VolumeImage, labelImage)
    for label in labelsList:
      labelImage = self.relabelCurrentLabel(labelImage, inputT1VolumeImage, inputT2VolumeImage, label)
    self.printIslandStatistics()

    su.PushLabel(labelImage, self.outputAtlasPath, overwrite=True)
    self.setLabelLUT()

  def setLabelLUT(self):
    inputNode = slicer.util.getNode(pattern=self.inputAtlasPath)
    inputLabelNodeLUTNodeID = inputNode.GetDisplayNode().GetColorNodeID()
    outputNode = slicer.util.getNode(pattern=self.outputAtlasPath)
    outputNode.GetDisplayNode().SetAndObserveColorNodeID(inputLabelNodeLUTNodeID)
    