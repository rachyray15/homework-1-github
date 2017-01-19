def handleButton():
    createModelsLogic = slicer.modules.createmodels.logic()
    node = createModelsLogic.CreateCoordinate(20,2)
    node.SetName('Node')
    model = slicer.vtkMRMLLinearTransformNode()
    model.SetName('PreModelToRas')
    slicer.mrmlScene.AddNode(model)
    transformation = vtk.vtkTransform()
    transformation.PreMultiply()
    transformation.Translate(300, 0, 0)
    transformation.Update()
    model.SetAndObserveTransformToParent(transformation)
    node.SetAndObserveTransformNodeID(model.GetID())
    print('Button Clicked')
b = qt.QPushButton('translate')
b.connect('clicked()', handleButton)
b.show()
