"""
usage: atlasDustCleanup.py --inputAtlasPath=<argument> --outputAtlasPath=<argument> --inputT1Path=<argument> --inputT2Path=<argument> --label=<argument> --maximumIslandVoxelCount=<argument>
atlasDustCleanup.py -h | --help
"""

import SimpleITK as sitk
import math

class DustCleanup():

  def __init__(self, arguments):
    self.inputAtlasPath = arguments['--inputAtlasPath']
    self.outputAtlasPath = arguments['--outputAtlasPath']
    self.inputT1Path = arguments['--inputT1Path']
    self.inputT2Path = arguments['--inputT2Path']
    self.label = int(arguments['--label'])
    self.maximumIslandVoxelCount = int(arguments['--maximumIslandVoxelCount'])

  def main(self):
    inputLabelImage = sitk.Cast(sitk.ReadImage(self.inputAtlasPath), sitk.sitkInt16)
    relabeledConnectedRegion = self.thresholdAtlas(inputLabelImage)
    inputT1VolumeImage = sitk.ReadImage(self.inputT1Path),
    inputT2VolumeImage = sitk.ReadImage(self.inputT2Path)
    labelStatsT1 = self.getLabelStatsObject(inputT1VolumeImage, relabeledConnectedRegion)
    labelStatsT2 = self.getLabelStatsObject(inputT2VolumeImage, relabeledConnectedRegion)
    labelList = self.getLabelListFromLabelStatsObject(labelStatsT1)
    labelList.reverse()
    print labelList[0:2]

    for currentLabel in labelList[0:2]:
      islandVoxelCount = labelStatsT1.GetCount(currentLabel)
      print islandVoxelCount
      if islandVoxelCount <= self.maximumIslandVoxelCount:
        meanT1Intesity = labelStatsT1.GetMean(currentLabel)
        meanT2Intesity = labelStatsT2.GetMean(currentLabel)
        targetLabels = self.getTargetLabels(inputLabelImage, inputT1VolumeImage, currentLabel)
        diffDict = self.calculateLabelIntensityDifferenceValue(meanT1Intesity, meanT2Intesity,
                                                               targetLabels, labelStatsT1, labelStatsT2)
        print diffDict

  def thresholdAtlas(self, inputLabelImage):
    binaryThresholdImage = sitk.BinaryThreshold(inputLabelImage, self.label, self.label)
    connectedRegion = sitk.ConnectedComponent(binaryThresholdImage, True)
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

  def getTargetLabels(self, inputLabelImage, inputVolumeImage, currentLabel):
    currentLabelBinaryThresholdImage = sitk.BinaryThreshold(inputLabelImage, currentLabel, currentLabel)
    castedCurrentLabelBinaryThresholdImage = sitk.Cast(currentLabelBinaryThresholdImage, sitk.sitkInt16)

    dialatedBinaryLabelMap = self.dialateLabelMap(castedCurrentLabelBinaryThresholdImage)
    reducedLabelMapImage = sitk.Multiply(dialatedBinaryLabelMap, inputLabelImage)

    reducedLabelMapT1LabelStats = self.getLabelStatsObject(inputVolumeImage, reducedLabelMapImage)
    targetLabels = reducedLabelMapT1LabelStats.GetLabels()
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


if __name__ == '__main__':
  from docopt import docopt
  arguments = docopt(__doc__)
  print arguments
  Object = DustCleanup(arguments)
  Object.main()
