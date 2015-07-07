"""
usage: atlasSmallIslandCleanup.py --inputAtlasPath=<argument> --outputAtlasPath=<argument> --inputT1Path=<argument> --inputT2Path=<argument> [--includeLabelsList=<argument> | --excludeLabelsList=<argument>] --maximumIslandVoxelCount=<argument> [--useFullyConnectedInConnectedComponentFilter] [--forceSuspiciousLabelChange]
atlasSmallIslandCleanup.py -h | --help
"""

import SimpleITK as sitk
import math

class DustCleanup():

  def __init__(self, arguments):
    self.inputAtlasPath = arguments['--inputAtlasPath']
    self.outputAtlasPath = arguments['--outputAtlasPath']
    self.inputT1Path = arguments['--inputT1Path']
    self.inputT2Path = arguments['--inputT2Path']
    self.includeLabelsList = self.evalInputListArg(arguments['--includeLabelsList'])
    self.excludeLabelsList = self.evalInputListArg(arguments['--excludeLabelsList'])
    self.maximumIslandVoxelCount = int(arguments['--maximumIslandVoxelCount'])
    self.useFullyConnectedInConnectedComponentFilter = arguments['--useFullyConnectedInConnectedComponentFilter']
    self.forceSuspiciousLabelChange = arguments['--forceSuspiciousLabelChange']
    self.islandStatistics = {'Total': {'numberOfIslandsCleaned': 0, 'numberOfIslands': 0}}

  def evalInputListArg(self, inputArg):
    if inputArg:
      return map(int, inputArg.split(','))
    else:
      return None

  def main(self):
    labelImage = sitk.Cast(sitk.ReadImage(self.inputAtlasPath), sitk.sitkInt16)
    inputT1VolumeImage = sitk.ReadImage(self.inputT1Path)
    inputT2VolumeImage = sitk.ReadImage(self.inputT2Path)
    labelsList = self.getLabelsList(inputT1VolumeImage, labelImage)
    for label in labelsList:
      labelImage = self.relabelCurrentLabel(labelImage, inputT1VolumeImage, inputT2VolumeImage, label)
    self.printIslandStatistics()
    sitk.WriteImage(labelImage, self.outputAtlasPath)

  def getLabelsList(self, volumeImage, labelImage):
    labelStatsObject = self.getLabelStatsObject(volumeImage, labelImage)
    labelsList = self.getLabelListFromLabelStatsObject(labelStatsObject)
    if self.excludeLabelsList:
      return self.removeLabelsFromLabelsList(labelsList, self.excludeLabelsList)
    if self.includeLabelsList:
      return self.verifyIncludeLabelsList(labelsList, self.includeLabelsList)
    return labelsList

  def removeLabelsFromLabelsList(self, labelsList, excludeList):
    for val in excludeList:
      try:
        labelsList.remove(val)
      except ValueError:
        print "WARNING: Label value", val, "is NOT a valid label in the input atlas:", self.inputAtlasPath
    return labelsList

  def verifyIncludeLabelsList(self, labelsList, includeList):
    verifiedList = list()
    for val in includeList:
      if val in labelsList:
        verifiedList.append(val)
      else:
        print "WARNING: Label value", val, "is NOT a valid label in the input atlas:", self.inputAtlasPath
    return verifiedList

  def printIslandStatistics(self):
    print "-"*50
    print "Label, numberOfIslandsCleaned, numberOfIslands"
    for val in sorted(self.islandStatistics):
      print ','.join([str(val), str(self.islandStatistics[val]['numberOfIslandsCleaned']),
                     str(self.islandStatistics[val]['numberOfIslands'])])

  def relabelCurrentLabel(self, labelImage, inputT1VolumeImage, inputT2VolumeImage, label):
    relabeledConnectedRegion = sitk.Cast(self.thresholdAtlas(labelImage, label), sitk.sitkInt16)
    labelStatsT1WithRelabeledConnectedRegion = self.getLabelStatsObject(inputT1VolumeImage, relabeledConnectedRegion)
    labelStatsT2WithRelabeledConnectedRegion = self.getLabelStatsObject(inputT2VolumeImage, relabeledConnectedRegion)
    labelList = self.getLabelListFromLabelStatsObject(labelStatsT1WithRelabeledConnectedRegion)
    labelList.reverse()

    numberOfIslandsCleaned = 0

    for currentLabel in labelList:
      islandVoxelCount = labelStatsT1WithRelabeledConnectedRegion.GetCount(currentLabel)
      if islandVoxelCount <= self.maximumIslandVoxelCount:
        meanT1Intesity = labelStatsT1WithRelabeledConnectedRegion.GetMean(currentLabel)
        meanT2Intesity = labelStatsT2WithRelabeledConnectedRegion.GetMean(currentLabel)
        targetLabels = self.getTargetLabels(labelImage, relabeledConnectedRegion, inputT1VolumeImage, currentLabel)
        diffDict = self.calculateLabelIntensityDifferenceValue(meanT1Intesity, meanT2Intesity,
                                                               targetLabels, inputT1VolumeImage,
                                                               inputT2VolumeImage, labelImage)
        if self.forceSuspiciousLabelChange:
          diffDict.pop(label)
        sortedLabelList = self.getDictKeysListSortedByValue(diffDict)
        currentLabelBinaryThresholdImage = sitk.BinaryThreshold(relabeledConnectedRegion, currentLabel, currentLabel)
        labelImage = self.relabelImage(labelImage, currentLabelBinaryThresholdImage, sortedLabelList[0])
        numberOfIslandsCleaned += 1
      else:
        break
    self.islandStatistics[label] = {'numberOfIslands': len(labelList), 'numberOfIslandsCleaned': numberOfIslandsCleaned}
    self.islandStatistics['Total']['numberOfIslands'] += len(labelList)
    self.islandStatistics['Total']['numberOfIslandsCleaned'] += numberOfIslandsCleaned
    return labelImage

  def thresholdAtlas(self, labelImage, label):
    binaryThresholdImage = sitk.BinaryThreshold(labelImage, label, label)
    if not self.useFullyConnectedInConnectedComponentFilter:
      connectedRegion = sitk.ConnectedComponent(binaryThresholdImage, fullyConnected=False)
    else:
      connectedRegion = sitk.ConnectedComponent(binaryThresholdImage, fullyConnected=True)
    relabeledConnectedRegion = sitk.RelabelComponent(connectedRegion)
    return relabeledConnectedRegion

  def getLabelStatsObject(self, volumeImage, labelImage):
    labelStatsObject = sitk.LabelStatisticsImageFilter()
    labelStatsObject.Execute(volumeImage, labelImage)

    return labelStatsObject

  def getLabelListFromLabelStatsObject(self, labelStatsObject):
    if sitk.Version().MajorVersion() > 0 or sitk.Version().MinorVersion() >= 9:
      compontentLabels = labelStatsObject.GetLabels()
    else: #if sitk version < 0.9 then use older function call GetValidLabels
      compontentLabels = labelStatsObject.GetValidLabels()
    return list(compontentLabels)

  def getTargetLabels(self, labelImage, relabeledConnectedRegion, inputVolumeImage, currentLabel):
    currentLabelBinaryThresholdImage = sitk.BinaryThreshold(relabeledConnectedRegion, currentLabel, currentLabel)
    castedCurrentLabelBinaryThresholdImage = sitk.Cast(currentLabelBinaryThresholdImage, sitk.sitkInt16)

    dialatedBinaryLabelMap = self.dialateLabelMap(castedCurrentLabelBinaryThresholdImage)
    outsideValue = -1
    reducedLabelMapImage = sitk.Mask(labelImage, dialatedBinaryLabelMap, outsideValue=outsideValue)

    reducedLabelMapT1LabelStats = self.getLabelStatsObject(inputVolumeImage, reducedLabelMapImage)
    targetLabels = self.getLabelListFromLabelStatsObject(reducedLabelMapT1LabelStats)
    targetLabels = self.removeOutsideValueFromTargetLabels(targetLabels, outsideValue)
    return targetLabels

  def removeOutsideValueFromTargetLabels(self, targetLabels, outsideValue):
    if outsideValue in targetLabels:
      targetLabels.remove(outsideValue)
    return targetLabels

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
                                             targetLabels, inputT1VolumeImage,
                                             inputT2VolumeImage, inputLabelImage):
    """
    Calculates a measurement for each label that is on the border of the suspicious label.
    This value is the square root of the sum of the squared difference in the average T1
    intensity values and the squared difference in the average T2 intensity values of the
    two islands in the comparison. The calculated value for each border label will later be
    sorted in ascending order - meaning that the smallest value has the "closest" average
    intensity to the suspicious label.
    """

    squareRootDiffLabelDict = dict()
    labelStatsT1WithInputLabelImage = self.getLabelStatsObject(inputT1VolumeImage, inputLabelImage)
    labelStatsT2WithInputLabelImage = self.getLabelStatsObject(inputT2VolumeImage, inputLabelImage)

    for targetLabel in targetLabels:
      # if targetLabel == 0:
      #   continue
      averageT1IntensityTargetLabel = labelStatsT1WithInputLabelImage.GetMean(targetLabel)
      averageT2IntensityTargetLabel = labelStatsT2WithInputLabelImage.GetMean(targetLabel)
      # print('targetLabel', targetLabel)
      # print('averageT1IntensityTargetLabel', averageT1IntensityTargetLabel)
      # print('averageT1IntensitySuspiciousLabel', averageT1IntensitySuspiciousLabel)
      # print('averageT2IntensityTargetLabel', averageT2IntensityTargetLabel)
      # print('averageT2IntensitySuspiciousLabel', averageT2IntensitySuspiciousLabel)
      squareDiffAverageT1 = math.pow(averageT1IntensitySuspiciousLabel -
                                     averageT1IntensityTargetLabel, 2)
      squareDiffAverageT2 = math.pow(averageT2IntensitySuspiciousLabel -
                                     averageT2IntensityTargetLabel, 2)
      squareRootDiff = math.sqrt(squareDiffAverageT1 + squareDiffAverageT2)

      squareRootDiffLabelDict[int(targetLabel)] = squareRootDiff

    return squareRootDiffLabelDict

  def relabelImage(self, labelImage, newRegion, newLabel):
    castedLabelImage = sitk.Cast(labelImage, sitk.sitkInt16)
    castedNewRegion = sitk.Cast(newRegion, sitk.sitkInt16)
    negatedMask = sitk.BinaryNot(castedNewRegion)
    negatedImage = sitk.Mask(castedLabelImage, negatedMask)
    maskTimesNewLabel = sitk.Multiply(castedNewRegion, newLabel)
    relabeledImage = sitk.Add(negatedImage, maskTimesNewLabel)
    return relabeledImage

  def getDictKeysListSortedByValue(self, val):
    return sorted(val, key=val.get)

if __name__ == '__main__':
  from docopt import docopt
  arguments = docopt(__doc__)
  print arguments
  Object = DustCleanup(arguments)
  Object.main()
