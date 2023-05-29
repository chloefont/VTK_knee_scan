import vtk
import os
import time

# source : https://kitware.github.io/vtk-examples/site/Cxx/IO/ReadSLC/
colors = vtk.vtkNamedColors()
colors.SetColor("view1_bc", [255, 210, 210, 255])
colors.SetColor("view2_bc", [210, 255, 210, 255])
colors.SetColor("view3_bc", [210, 210, 255, 255])
colors.SetColor("view4_bc", [210, 210, 210, 255])
colors.SetColor("skin", [165, 127, 127, 255])
colors.SetColor("bone", [232, 232, 232, 255])
colors.SetColor("sphere", [205, 206, 230, 255])

KNEE_DIST_FILENAME = "skin_distance.vtk"


def write_polydata(polydata, filename):
    '''
    Write a vtkPolyData to a file
    :param polydata: the vtkPolyData to write
    :param filename: the name of the file to write to
    '''
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(filename)
    writer.SetInputData(polydata)
    writer.Write()


def get_camera():
    '''
    Get a camera with a specific position
    :return: the camera (vtkCamera)
    '''
    camera = vtk.vtkCamera()
    camera.SetFocalPoint(0.0, 0.0, 0.0)
    camera.SetPosition(0.0, -1.0, 0.0)
    camera.SetViewUp(0.0, 0.0, -1.0)
    camera.Azimuth(0)
    return camera


def view_1(skin_contour_filter):
    '''
    Get the actor for the first view, by cutting the skin with a plane
    :param skin_contour_filter: the contour filter for the skin
    :return: a skin actor
    '''
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
    cut_filter.SetRadius(0.8)
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
    '''
    Get the actor for the second view, by cutting the skin with a sphere and showing the skin half transparent
    :param skin_contour_filter: the contour filter for the skin
    :return: a skin actor
    '''
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
    volume_actor.GetProperty().SetOpacity(0.5)
    volume_actor.GetProperty().SetColor(colors.GetColor3d("skin"))

    property = vtk.vtkProperty()
    property.SetColor(colors.GetColor3d("skin"))
    volume_actor.SetBackfaceProperty(property)

    return volume_actor


def view_3(skin_contour_filter):
    '''
    Get the actors for the third view, by cutting the skin with a visible sphere
    :param skin_contour_filter: the contour filter for the skin
    :return: a skin actor and a sphere actor
    '''
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

    sphere_sample = vtk.vtkSampleFunction()
    sphere_sample.SetImplicitFunction(sphere)
    sphere_sample.SetModelBounds(-300, 300, -300, 300, -300, 300)
    sphere_sample.SetSampleDimensions(50, 50, 50)
    sphere_sample.ComputeNormalsOff()

    sphere_contour = vtk.vtkContourFilter()
    sphere_contour.SetInputConnection(sphere_sample.GetOutputPort())
    sphere_contour.SetValue(0, 0.0)
    sphere_contour.Update()

    sphere_mapper = vtk.vtkPolyDataMapper()
    sphere_mapper.SetInputConnection(sphere_contour.GetOutputPort())
    sphere_mapper.ScalarVisibilityOff()

    sphere_actor = vtk.vtkActor()
    sphere_actor.SetMapper(sphere_mapper)
    sphere_actor.GetProperty().SetColor(colors.GetColor3d("sphere"))
    sphere_actor.GetProperty().SetOpacity(0.3)

    return [volume_actor, sphere_actor]


def view_4(bone_mapper, skin_mapper):
    '''
    Get the actor for the fourth view, by showing the distance between the skin and the bone
    :param bone_mapper: the mapper for the bone
    :param skin_mapper: the mapper for the skin
    :return: a distance mapper
    '''
    distance_mapper = vtk.vtkPolyDataMapper()
    if not os.path.exists(KNEE_DIST_FILENAME):
        distance_filter = vtk.vtkDistancePolyDataFilter()
        distance_filter.SetInputData(0, bone_mapper.GetInput())
        distance_filter.SetInputData(1, skin_mapper.GetInput())
        distance_filter.SignedDistanceOff()
        distance_filter.Update()
        write_polydata(distance_filter.GetOutput(), KNEE_DIST_FILENAME)
        distance_mapper.SetInputConnection(distance_filter.GetOutputPort())
        distance_mapper.SetScalarRange(distance_filter.GetOutput().GetPointData().GetScalars().GetRange())
    else :
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(KNEE_DIST_FILENAME)
        reader.Update()
        distance_mapper.SetInputData(reader.GetOutput())
        distance_mapper.SetScalarRange(reader.GetOutput().GetPointData().GetScalars().GetRange())


    distance_mapper.SetScalarVisibility(1)

    distance_actor = vtk.vtkActor()
    distance_actor.SetMapper(distance_mapper)
    return distance_actor


def get_renderer(actors, viewport, camera, background_color=colors.GetColor3d("SlateGray")):
    '''
    Get renderer with actors, viewport, camera and background color
    :param actors: the actors to show (list of vtkActor)
    :param viewport: the viewport (list of 4 float)
    :param camera: the camera (vtkCamera)
    :param background_color: the background color (list of 3 float)
    :return: the renderer (vtkRenderer)
    '''
    renderer = vtk.vtkRenderer()
    renderer.SetViewport(viewport)
    renderer.SetBackground(background_color)

    for actor in actors:
        renderer.AddActor(actor)

    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()
    return renderer


def get_contour_filter(reader, iso_value):
    '''
    Get contour filter with reader and iso value
    :param reader: the reader (vtkPolyDataReader)
    :param iso_value: the value of iso surface (float)
    :return: the contour filter (vtkContourFilter)
    '''
    contour_filter = vtk.vtkContourFilter()
    contour_filter.SetInputConnection(reader.GetOutputPort())
    contour_filter.GenerateValues(5, 80.0, 100.0)
    contour_filter.SetValue(0, iso_value)
    contour_filter.Update()
    return contour_filter


def get_mapper(contour_filter):
    '''
    Get mapper with contour filter
    :param contour_filter: the contour filter (vtkContourFilter)
    :return: the mapper (vtkPolyDataMapper)
    '''
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(contour_filter.GetOutputPort())
    mapper.ScalarVisibilityOff()
    return mapper


def get_actor(mapper, color):
    '''
    Get actor with mapper and color
    :param mapper: the mapper of the actor (vtkPolyDataMapper)
    :param color: the color of the actor (tuple)
    :return: the actor (vtkActor)
    '''
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetDiffuse(0.8)
    actor.GetProperty().SetSpecular(0.8)
    actor.GetProperty().SetSpecularPower(120.0)
    actor.GetProperty().SetColor(color)
    return actor


if __name__ == '__main__':
    FILENAME = "data/vw_knee.slc"
    VTK_FILE = "data/vw_knee.vtk"
    BONE_ISO_VALUE = 72
    SKIN_ISO_VALUE = 50

    WIDTH_SIZE = 800
    HEIGHT_SIZE = 800

    # Read file
    reader = vtk.vtkSLCReader()
    reader.SetFileName(FILENAME)
    reader.Update()

    # Get contour filters
    bone_contour_filter = get_contour_filter(reader, BONE_ISO_VALUE)
    skin_contour_filter = get_contour_filter(reader, SKIN_ISO_VALUE)

    outliner = vtk.vtkOutlineFilter()
    outliner.SetInputConnection(reader.GetOutputPort())
    outliner.Update()

    # Get mappers
    bone_mapper = get_mapper(bone_contour_filter)
    skin_mapper = get_mapper(skin_contour_filter)

    outliner_mapper = vtk.vtkPolyDataMapper()
    outliner_mapper.SetInputConnection(outliner.GetOutputPort())

    # Get actors
    bone_actor = get_actor(bone_mapper, colors.GetColor3d("bone"))
    skin_actor = get_actor(skin_mapper, colors.GetColor3d("skin"))

    outliner_actor = vtk.vtkActor()
    outliner_actor.SetMapper(outliner_mapper)
    outliner_actor.GetProperty().SetColor(colors.GetColor3d("Black"))

    # extractVOI is used to fix the problem of subsampling of data and reduce
    # slow interaction and increase loading speed
    # source : https://kitware.github.io/vtk-examples/site/Cxx/IO/ReadSLC/
    extract_VOI = vtk.vtkExtractVOI()
    extract_VOI.SetInputConnection(reader.GetOutputPort())
    extract_VOI.SetSampleRate(2, 2, 2)
    extract_VOI.Update()

    camera = get_camera()

    renderer_top_left = get_renderer([bone_actor, outliner_actor, view_1(skin_contour_filter)], [0, 0.5, 0.5, 1], camera, colors.GetColor3d("view1_bc"))
    renderer_top_right = get_renderer([bone_actor, outliner_actor, view_2(skin_contour_filter)], [0.5, 0.5, 1, 1], camera, colors.GetColor3d("view2_bc"))
    renderer_bottom_left = get_renderer([bone_actor, outliner_actor] + view_3(skin_contour_filter), [0, 0, 0.5, 0.5], camera, colors.GetColor3d("view3_bc"))
    renderer_bottom_right = get_renderer([outliner_actor, view_4(bone_mapper, skin_mapper)], [0.5, 0, 1, 0.5], camera, colors.GetColor3d("view4_bc"))

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer_top_left)
    render_window.AddRenderer(renderer_top_right)
    render_window.AddRenderer(renderer_bottom_left)
    render_window.AddRenderer(renderer_bottom_right)
    render_window.SetSize(WIDTH_SIZE, HEIGHT_SIZE)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
    interactor.SetRenderWindow(render_window)

    for _ in range(0, 720):
        time.sleep(0.01)
        camera.Azimuth(1)
        render_window.Render()

    render_window.SetWindowName("Knee scan")
    render_window.Render()
    interactor.Start()
