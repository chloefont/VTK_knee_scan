import vtk

# source : https://kitware.github.io/vtk-examples/site/Cxx/IO/ReadSLC/
colors = vtk.vtkNamedColors()
colors.SetColor("view1_bc", [255, 210, 210, 255])
colors.SetColor("view2_bc", [210, 255, 210, 255])
colors.SetColor("view3_bc", [210, 210, 255, 255])
colors.SetColor("view4_bc", [210, 210, 210, 255])
colors.SetColor("skin", [165, 127, 127, 255])
colors.SetColor("bone", [232, 232, 232, 255])


def view_1(skin_contour_filter):
    cut_plane = vtk.vtkPlane()
    cut_plane.SetOrigin(0, 0, 0)
    cut_plane.SetNormal(0, 0, 1)

    cutter = vtk.vtkCutter()
    cutter.SetCutFunction(cut_plane)
    cutter.GenerateValues(19, 0, 200) # TODO mettre tous les cms
    cutter.SetInputConnection(skin_contour_filter.GetOutputPort())
    cutter.Update()

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(cutter.GetOutputPort())
    stripper.Update()

    cut_filter = vtk.vtkTubeFilter()
    cut_filter.SetInputConnection(stripper.GetOutputPort())
    cut_filter.SetRadius(0.5)
    #cut_filter.SetNumberOfSides(50)
    cut_filter.Update()

    cut_mapper = vtk.vtkPolyDataMapper()
    cut_mapper.SetInputConnection(cut_filter.GetOutputPort())
    cut_mapper.SetScalarVisibility(0)

    cut_actor = vtk.vtkActor()
    cut_actor.SetMapper(cut_mapper)
    cut_actor.GetProperty().SetColor(colors.GetColor3d("skin"))
    return cut_actor


def view_2(skin_contour_filter):
    sphere = vtk.vtkSphere()
    sphere.SetRadius(50)
    sphere.SetCenter(70, 40, 100)

    clipper = vtk.vtkClipPolyData()
    clipper.SetInputConnection(skin_contour_filter.GetOutputPort())
    clipper.SetClipFunction(sphere)
    clipper.SetValue(0.5)
    clipper.Update()

    volume_mapper = vtk.vtkPolyDataMapper()
    volume_mapper.SetInputConnection(clipper.GetOutputPort())
    volume_mapper.SetScalarVisibility(0)

    volume_actor = vtk.vtkActor()
    volume_actor.SetMapper(volume_mapper)
    volume_actor.GetProperty().SetColor(colors.GetColor3d("skin"))
    volume_actor.GetProperty().SetOpacity(0.5)

    return volume_actor



def create_renderer(actors, viewport, background_color=colors.GetColor3d("SlateGray")):
    renderer = vtk.vtkRenderer()
    renderer.SetViewport(viewport)
    renderer.SetBackground(background_color)
    for actor in actors:
        renderer.AddActor(actor)
    return renderer


if __name__ == '__main__':
    FILENAME = "data/vw_knee.slc"
    VTK_FILE = "data/vw_knee.vtk"
    bone_iso_value = 72
    skin_iso_value = 50



    # Using vtkSLCReader to read Volumetric file format( < filename.slc >)
    reader = vtk.vtkSLCReader()
    reader.SetFileName(FILENAME)
    reader.Update()

    # Implementing Marching Cubes Algorithm to create the surface using
    # vtkContourFilter object
    bone_contour_filter = vtk.vtkContourFilter()
    bone_contour_filter.SetInputConnection(reader.GetOutputPort())

    skin_contour_filter = vtk.vtkContourFilter()
    skin_contour_filter.SetInputConnection(reader.GetOutputPort())

    # Change the range(2nd and 3rd Parameter) based on your
    # requirement.recomended value for 1st parameter is above 1
    bone_contour_filter.GenerateValues(5, 80.0, 100.0);
    bone_contour_filter.SetValue(0, bone_iso_value)
    bone_contour_filter.Update()

    #skin_contour_filter.GenerateValues(5, 80.0, 100.0);
    skin_contour_filter.SetValue(0, skin_iso_value)
    skin_contour_filter.Update()

    # Adding the outliner using vtkOutlineFilter object
    outliner = vtk.vtkOutlineFilter()
    outliner.SetInputConnection(reader.GetOutputPort())
    outliner.Update()

    # Visualize
    bone_mapper = vtk.vtkPolyDataMapper()
    bone_mapper.SetInputConnection(bone_contour_filter.GetOutputPort())
    bone_mapper.SetScalarVisibility(0)

    skin_mapper = vtk.vtkPolyDataMapper()
    skin_mapper.SetInputConnection(skin_contour_filter.GetOutputPort())
    skin_mapper.SetScalarVisibility(0)

    bone_actor = vtk.vtkActor()
    bone_actor.SetMapper(bone_mapper)
    bone_actor.GetProperty().SetDiffuse(0.8)
    bone_actor.GetProperty().SetDiffuseColor(colors.GetColor3d("bone"))
    bone_actor.GetProperty().SetSpecular(0.8)
    bone_actor.GetProperty().SetSpecularPower(120.0)

    skin_actor = vtk.vtkActor()
    skin_actor.SetMapper(skin_mapper)
    skin_actor.GetProperty().SetDiffuse(0.8)
    skin_actor.GetProperty().SetDiffuseColor(colors.GetColor3d("skin"))
    skin_actor.GetProperty().SetSpecular(0.8)
    skin_actor.GetProperty().SetSpecularPower(120.0)

    # extractVOI is used to fix the problem of subsampling of data and reduce
    # slow interaction and increase loading speed
    extract_VOI = vtk.vtkExtractVOI()
    extract_VOI.SetInputConnection(reader.GetOutputPort())
    extract_VOI.SetSampleRate(2, 2, 2)
    extract_VOI.Update()

    renderer_top_left = create_renderer([bone_actor, view_1(skin_contour_filter)], [0, 0.5, 0.5, 1], colors.GetColor3d("view1_bc"))
    renderer_top_right = create_renderer([bone_actor, view_2(skin_contour_filter)], [0.5, 0.5, 1, 1], colors.GetColor3d("view2_bc"))
    renderer_bottom_left = create_renderer([bone_actor, skin_actor], [0, 0, 0.5, 0.5], colors.GetColor3d("view3_bc"))
    renderer_bottom_right = create_renderer([bone_actor, skin_actor], [0.5, 0, 1, 0.5], colors.GetColor3d("view4_bc"))

    #renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer_top_left)
    render_window.AddRenderer(renderer_top_right)
    render_window.AddRenderer(renderer_bottom_left)
    render_window.AddRenderer(renderer_bottom_right)
    render_window.SetSize(640, 512)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)


    render_window.Render()

    # Pick a good view
    camera = renderer_top_left.GetActiveCamera()
    camera.SetFocalPoint(0.0, 0.0, 0.0)
    camera.SetPosition(0.0, -1.0, 0.0)
    camera.SetViewUp(0.0, 0.0, -1.0)
    camera.Azimuth(-90.0)
    renderer_top_left.ResetCamera()
    renderer_top_left.ResetCameraClippingRange()

    render_window.SetWindowName("ReadSLC")
    render_window.Render()
    render_window_interactor.Start()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
