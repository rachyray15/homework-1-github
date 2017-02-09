import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy


#
# Danielle
#

class Danielle(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Danielle"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # replace with "Firstname Lastname (Organization)"
        self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
        self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # replace with organization, grant and thanks.


#
# DanielleWidget
#

class DanielleWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        #
        # Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # input volume selector
        #
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.showChildNodeTypes = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.setToolTip("Pick the input to the algorithm.")
        parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

        #
        # output volume selector
        #
        self.outputSelector = slicer.qMRMLNodeComboBox()
        self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.outputSelector.selectNodeUponCreation = True
        self.outputSelector.addEnabled = True
        self.outputSelector.removeEnabled = True
        self.outputSelector.noneEnabled = True
        self.outputSelector.showHidden = False
        self.outputSelector.showChildNodeTypes = False
        self.outputSelector.setMRMLScene(slicer.mrmlScene)
        self.outputSelector.setToolTip("Pick the output to the algorithm.")
        parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

        #
        # threshold value
        #
        self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
        self.imageThresholdSliderWidget.singleStep = 0.1
        self.imageThresholdSliderWidget.minimum = -100
        self.imageThresholdSliderWidget.maximum = 100
        self.imageThresholdSliderWidget.value = 0.5
        self.imageThresholdSliderWidget.setToolTip(
            "Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
        parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

        #
        # check box to trigger taking screen shots for later use in tutorials
        #
        self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
        self.enableScreenshotsFlagCheckBox.checked = 0
        self.enableScreenshotsFlagCheckBox.setToolTip(
            "If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
        parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.enabled = False
        parametersFormLayout.addRow(self.applyButton)

        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

    def onApplyButton(self):
        logic = RachelLogic()
        enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
        imageThreshold = self.imageThresholdSliderWidget.value
        logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold,
                  enableScreenshotsFlag)


#
# RachelLogic
#

class RachelLogic(ScriptedLoadableModuleLogic):
    def averageDistancePoints(self, pointsA, pointsB, aToBMatrix):
        average = 0.0
        numbersSoFar = 0
        N = pointsA.GetNumberOfPoints()

        for i in range(N):
            numbersSoFar = numbersSoFar + 1
            a = pointsA.GetPoint(i)
            pointA_Reference = numpy.array(a)
            pointA_Reference = numpy.append(pointA_Reference, 1)
            pointA_Ras = aToBMatrix.MultiplyFloatPoint(pointA_Reference)
            b = pointsB.GetPoint(i)
            pointB_Ras = numpy.array(b)
            pointB_Ras = numpy.append(pointB_Ras, 1)
            distance = numpy.linalg.norm(pointA_Ras - pointB_Ras)
            average = average + (distance - average) / numbersSoFar

        return average

    def hasImageData(self, volumeNode):
        """This is an example logic method that
        returns true if the passed in volume
        node has valid image data
        """
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        """Validates if the output is not the same as input
        """
        if not inputVolumeNode:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID() == outputVolumeNode.GetID():
            logging.debug(
                'isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def takeScreenshot(self, name, description, type=-1):
        # show the message even if not taking a screen shot
        slicer.util.delayDisplay(
            'Take screenshot: ' + description + '.\nResult is available in the Annotations module.', 3000)

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly
            type = slicer.qMRMLScreenShotDialog.FullLayout

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        qimage = qpixMap.toImage()
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage, imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

    def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
        """
        Run the actual algorithm
        """

        if not self.isValidInputOutputData(inputVolume, outputVolume):
            slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
            return False

        logging.info('Processing started')

        # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
        cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(),
                     'ThresholdValue': imageThreshold, 'ThresholdType': 'Above'}
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

        # Capture screenshot
        if enableScreenshots:
            self.takeScreenshot('RachelTest-Start', 'MyScreenshot', -1)

        logging.info('Processing completed')

        return True


class RachelTest(ScriptedLoadableModuleTest):
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
        self.test_Rachel1()

    def test_Rachel1(self):
        referenceToRas = slicer.vtkMRMLLinearTransformNode()
        referenceToRas.SetName('ReferenceToRas')
        slicer.mrmlScene.AddNode(referenceToRas)

        referencePoints = vtk.vtkPoints()
        rasPoints = vtk.vtkPoints()

        alphaFids = slicer.vtkMRMLMarkupsFiducialNode()
        alphaFids.SetName('ReferencePoints')
        slicer.mrmlScene.AddNode(alphaFids)

        betaFids = slicer.vtkMRMLMarkupsFiducialNode()
        betaFids.SetName('RasPoints')
        slicer.mrmlScene.AddNode(betaFids)
        betaFids.GetDisplayNode().SetSelectedColor(1, 1, 0)

        N = 15
        Sigma = 2
        Scale = 50
        fromNormCoordinates = numpy.random.rand(N, 3)
        noise = numpy.random.normal(0.0, Sigma, N * 3)

        dn = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
        a = dn.GetArray()
        a.SetNumberOfTuples(N)
        for i in range(N):
            x = (fromNormCoordinates[i, 0] - 0.5) * Scale
            y = (fromNormCoordinates[i, 1] - 0.5) * Scale
            z = (fromNormCoordinates[i, 2] - 0.5) * Scale
            alphaFids.AddFiducial(x, y, z)
            referencePoints.InsertNextPoint(x, y, z)
            xx = x + noise[i * 3]
            yy = y + noise[i * 3 + 1]
            zz = z + noise[i * 3 + 2]
            betaFids.AddFiducial(xx, yy, zz)
            rasPoints.InsertNextPoint(xx, yy, zz)

            createModelsLogic = slicer.modules.createmodels.logic()
            rasCoordinateModel = createModelsLogic.CreateCoordinate(25, 2)
            rasCoordinateModel.SetName('RasCoordinateModel')
            referenceCoordinateModel = createModelsLogic.CreateCoordinate(20, 2)
            referenceCoordinateModel.SetName('ReferenceCoordinateModel')
            rasCoordinateModel.GetDisplayNode().SetColor(1, 0, 0)
            referenceCoordinateModel.GetDisplayNode().SetColor(0, 0, 1)

            referenceCoordinateModel.SetAndObserveTransformNodeID(referenceToRas.GetID())

            landmarkTransform = vtk.vtkLandmarkTransform()
            landmarkTransform.SetSourceLandmarks(referencePoints)
            landmarkTransform.SetTargetLandmarks(rasPoints)
            landmarkTransform.SetModeToRigidBody()
            landmarkTransform.Update()

            referenceToRasMatrix = vtk.vtkMatrix4x4()
            landmarkTransform.GetMatrix(referenceToRasMatrix)

            det = referenceToRasMatrix.Determinant()
            if det < 1e-8:
                print 'Unstable registration. Check input for collinear points.'

            targetPoint_Reference = numpy.array([0, 0, 0, 1])
            targetPoint_Ras = referenceToRasMatrix.MultiplyFloatPoint(targetPoint_Reference)
            distance_TRE = numpy.linalg.norm(targetPoint_Reference - targetPoint_Ras)
            print "TRE: " + str(distance_TRE)

            referenceToRas.SetMatrixTransformToParent(referenceToRasMatrix)

            logic = RachelLogic()
            average_FRE = logic.averageDistancePoints(referencePoints, rasPoints, referenceToRasMatrix)

            print "FRE: " + str(average_FRE)

            a.SetComponent(i, 0, i)
            a.SetComponent(i, 1, distance_TRE)
            a.SetComponent(i, 2, 0)

        #code for homework due February 9

        lns = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
        lns.InitTraversal()
        ln = lns.GetNextItemAsObject()
        ln.SetViewArrangement(24)

        cvns = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
        cvns.InitTraversal()
        cvn = cvns.GetNextItemAsObject()

        cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())

        cn.AddArray('plot', dn.GetID())

        cn.SetProperty('default', 'title', 'TRE as a Function of Number of Points')
        cn.SetProperty('default', 'xAxisLabel', '# of Points')
        cn.SetProperty('default', 'yAxisLabel', 'TRE')

        cvn.SetChartNodeID(cn.GetID())

        self.delayDisplay('Test passed!')