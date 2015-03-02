import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import Editor

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
    # Markups Area
    #
    markupsCollapsibleButton = ctk.ctkCollapsibleButton()
    markupsCollapsibleButton.text = "Markups"
    self.layout.addWidget(markupsCollapsibleButton)

    # Layout within the dummy collapsible button
    markupsFormLayout = qt.QFormLayout(markupsCollapsibleButton)

    #
    # Adds the Markups widget
    #
    self.localMarkupsWidget = slicer.modules.markups.widgetRepresentation()
    self.localMarkupsWidget.setParent(self.parent)
    markupsFormLayout.addRow(self.localMarkupsWidget)
    self.localMarkupsWidget.show()

    #
    # Adds the Editor Widget
    #
    self.localEditorWidget = Editor.EditorWidget(parent=self.parent, showVolumesFrame=False)
    self.localEditorWidget.setup()
    self.localEditorWidget.enter()

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = True

  def onApplyButton(self):
    logic = OpenAtlasEditorLogic()
    print("Apply button selected")
    logic.run()


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

  def run(self):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running')

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
