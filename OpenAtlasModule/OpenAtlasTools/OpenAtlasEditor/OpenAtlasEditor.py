import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import Editor
import SimpleITK as sitk
import sitkUtils as su

#
# OpenAtlasEditor
#

class OpenAtlasEditor(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "OpenAtlasEditor" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# OpenAtlasEditorWidget
#

class OpenAtlasEditorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    if True:
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

    #
    # Cast Label Map to Signed 16-bit Parameters Area
    #
    castParametersCollapsibleButton = ctk.ctkCollapsibleButton()
    castParametersCollapsibleButton.text = "Cast Label Map to Signed 16-bit for use in Editor Parameters"
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

    #
    # Merge Suspicious Label to Target Label Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Merge Suspicious Label to Target Label Parameters"
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
    self.targetLabel.maximum = 10000.0
    self.targetLabel.value = 24.0
    self.targetLabel.setToolTip('Set the target label (label to change suspicious label to)')
    parametersFormLayout.addRow("Target Label: ", self.targetLabel)
    
    self.suspiciousLabel = ctk.ctkSliderWidget()
    self.suspiciousLabel.singleStep = 1.0
    self.suspiciousLabel.minimum = 0.0
    self.suspiciousLabel.maximum = 10000.0
    self.suspiciousLabel.value = 999.0
    self.suspiciousLabel.setToolTip('Set the suspicious label (will be changed to target '
                                    'label if connected in largest region')
    parametersFormLayout.addRow("Suspicious Label: ", self.suspiciousLabel)

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
    self.posteriorParametersFormLayout.addRow("Posterior threshold for Posterior Image: ", self.posteriorThreshold)

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
    # Adds the Editor Widget
    #
    self.localEditorWidget = Editor.EditorWidget(parent=self.parent, showVolumesFrame=False)
    self.localEditorWidget.setup()
    self.localEditorWidget.enter()

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
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelectorLabel.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputSelectorPosterior.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelectorLabel.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.enablePosteriorCheckBox.connect('clicked(bool)', self.onEnablePosteriorSelect)

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
    logic = OpenAtlasEditorLogic()
    logic.runCast(self.inputCastLabelSelector.currentNode(),
                  self.outputCastLabelSelector.currentNode())

  def onApplyButton(self):
    logic = OpenAtlasEditorLogic()

    print("Merge Apply button selected")

    if not self.enablePosteriorCheckBox.checked:
      logic.run(self.inputSelectorLabel.currentNode().GetName(),
              self.outputSelectorLabel.currentNode().GetName(),
              self.targetLabel.value, self.suspiciousLabel.value)
    else:
      logic.run(self.inputSelectorLabel.currentNode().GetName(),
              self.outputSelectorLabel.currentNode().GetName(),
              self.targetLabel.value, self.suspiciousLabel.value,
              enablePosterior=True,
              inputPosteriorName=self.inputSelectorPosterior.currentNode().GetName(),
              posteriorThreshold=self.posteriorThreshold.value)

  def onEnablePosteriorSelect(self):
    self.onSelect()
    if not self.enablePosteriorCheckBox.checked:
      self.inputSelectorPosterior.setStyleSheet("color: rgb(230,241,255)")
      self.posteriorThreshold.setStyleSheet("color: rgb(230,241,255)")
    else:
      self.inputSelectorPosterior.setStyleSheet("color: rgb(0,0,0)")
      self.posteriorThreshold.setStyleSheet("color: rgb(0,0,0)")

#
# OpenAtlasEditorLogic
#

class OpenAtlasEditorLogic(ScriptedLoadableModuleLogic):
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

  def run(self, inputLabelName, outputLabelName, targetLabel, suspiciousLabel,
          enablePosterior=False, inputPosteriorName=None, posteriorThreshold=None):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running')

    newLabel = self.mergeLabels(inputLabelName, targetLabel, suspiciousLabel,
                                enablePosterior, inputPosteriorName, posteriorThreshold)

    inputNode = slicer.util.getNode(pattern=inputLabelName)
    inputLabelNodeLUTNodeID = inputNode.GetDisplayNode().GetColorNodeID()

    su.PushLabel(newLabel, outputLabelName, overwrite=True)
    self.setLabelLUT(outputLabelName, inputLabelNodeLUTNodeID)

    return True

  def relabel(self, labelImage, newRegion, newLabel):
    newLabelImage = sitk.Cast(labelImage, sitk.sitkInt32) * sitk.Cast((newRegion == 0), sitk.sitkInt32) \
                    + sitk.Cast(newLabel * (newRegion > 0), sitk.sitkInt32)
    newCastedLabelImage = sitk.Cast(newLabelImage, sitk.sitkInt16)
    return newCastedLabelImage

  def mergeLabels(self, labelImageName, targetLabel, suspiciousLabel,
                  enablePosterior, inputPosteriorName, posteriorThreshold):
    labelImage = su.PullFromSlicer(labelImageName)
    targetAndSuspiciousMergedLabel = ((labelImage == targetLabel) + (labelImage == suspiciousLabel))
    connectedRegion = sitk.ConnectedComponent(targetAndSuspiciousMergedLabel, True)
    relabeledConnectedRegion = sitk.RelabelComponent(connectedRegion)
    if not enablePosterior:
      newRegion = (relabeledConnectedRegion == 1)
      print('no thresh used')
    else:
      print('threshold used: ', posteriorThreshold)
      posterior = su.PullFromSlicer(inputPosteriorName)
      thresholdedPosterior = sitk.BinaryThreshold(posterior, posteriorThreshold)
      newRegion = (relabeledConnectedRegion == 1) * thresholdedPosterior
    newLabel = self.relabel(labelImage, newRegion > 0, targetLabel)
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

class OpenAtlasEditorTest(ScriptedLoadableModuleTest):
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
    self.test_OpenAtlasEditor1()

  def test_OpenAtlasEditor1(self):
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
    logic = OpenAtlasEditorLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
