import vtk

# source : https://kitware.github.io/vtk-examples/site/Cxx/IO/ReadSLC/

if __name__ == '__main__':
    FILENAME = "data/vw_knee.slc"
    iso_value = 72

    # Using vtkSLCReader to read Volumetric file format( < filename.slc >)
    reader = vtk.vtkSLCReader()
    reader.SetFileName(FILENAME)
    reader.Update()

    # Implementing Marching Cubes Algorithm to create the surface using
    # vtkContourFilter object
    cfilter = vtk.vtkContourFilter()
    cfilter.SetInputConnection(reader.GetOutputPort())

    # Change the range(2nd and 3rd Paramater) based on your
    # requirement.recomended value for 1st parameter is above 1
    # cFilter->GenerateValues(5, 80.0, 100.0);
    cfilter.SetValue(0, iso_value)
    cfilter.Update()

    # Adding the outliner using vtkOutlineFilter object
    outliner = vtk.vtkOutlineFilter()
    outliner.SetInputConnection(reader.GetOutputPort())
    outliner.Update()

    # Visualize
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cfilter.GetOutputPort())
    mapper.SetScalarVisibility(0)

    colors = vtk.vtkNamedColors()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetDiffuse(0.8)
    actor.GetProperty().SetDiffuseColor(colors.GetColor3d("Ivory"))
    actor.GetProperty().SetSpecular(0.8)
    actor.GetProperty().SetSpecularPower(120.0)

    # extractVOI is used to fix the problem of subsampling of data and reduce
    # slow interaction and increase loading speed
    extract_VOI = vtk.vtkExtractVOI()
    extract_VOI.SetInputConnection(reader.GetOutputPort())
    extract_VOI.SetSampleRate(2, 2, 2)
    extract_VOI.Update()

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(640, 512)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("SlateGray"))
    render_window.Render()

    # Pick a good view
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(0.0, 0.0, 0.0)
    camera.SetPosition(0.0, -1.0, 0.0)
    camera.SetViewUp(0.0, 0.0, -1.0)
    camera.Azimuth(-90.0)
    renderer.ResetCamera()
    renderer.ResetCameraClippingRange()

    render_window.SetWindowName("ReadSLC")
    render_window.Render()
    render_window_interactor.Start()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
