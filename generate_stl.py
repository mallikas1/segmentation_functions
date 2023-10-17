"""
Convert segmentations to stls.

required:
nifti_folder: folder containing nifti segmentation files
save_dir: directory where for each scan a subfolder is created with all the stls in it. 
"""

import os
import glob
import vtk
import SimpleITK as sitk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk


def generate_stl(name_nifti_folder, save_dir):
    files = glob.glob(rf"{name_nifti_folder}/*.nii.gz")

    for seg_file in files:
        stl_path = seg_file.replace(name_nifti_folder, save_dir)
        stl_path = stl_path.replace('.nii.gz', '')
        if not os.path.exists(stl_path):
            os.makedirs(stl_path)

        print("Generating stls for :",  seg_file)
        # read all the labels present in the file
        multi_label_image =sitk.ReadImage(seg_file)
        origin = multi_label_image.GetOrigin()
        spacing = multi_label_image.GetSpacing()
        direction = multi_label_image.GetDirection()
        img_npy = sitk.GetArrayFromImage(multi_label_image)
        arraym = img_npy.copy()		
        labels = np.unique(img_npy)
        
        # if you have tags or want to give the stls a specific name uncomment the
        # following two statements and comment line 44

        # tags = ['bkg', 'Pelvis', 'Femur', ...]
        # for label, tag in zip(labels, tags):
        for label in labels:
            if int(label) != 0:
                tag = label # since there is no predefined tag
                array = (img_npy == label)*label
                # array to vtkImageData
                flatten_array = array.ravel()
                shape = np.array(array.shape)
                vtk_data_array = numpy_to_vtk(
                    num_array=
                    flatten_array,  # ndarray contains the fitting result from the points. It is a 3D array
                    deep=True,
                    array_type=vtk.VTK_FLOAT)
                # convert vessel array to poly and save as STL
                img_vtk = vtk.vtkImageData()
                img_vtk.SetDimensions(shape[::-1])
                img_vtk.SetSpacing(spacing)
                img_vtk.SetOrigin(origin)
                img_vtk.SetDirectionMatrix(direction) #-1, 0, 0, 0, -1, 0, 0, 0, 1)
                img_vtk.GetPointData().SetScalars(vtk_data_array)
                # apply marching cube surface generation
                surf = vtk.vtkDiscreteMarchingCubes()
                surf.SetInputData(img_vtk)
                surf.SetValue(0, int(label)) 
                # use surf.GenerateValues function if more than one contour is available in the file
                surf.Update()
                #smoothing the mesh
                smoother= vtk.vtkWindowedSincPolyDataFilter()
                if vtk.VTK_MAJOR_VERSION <= 5:
                    smoother.SetInput(surf.GetOutput())
                else:
                    smoother.SetInputConnection(surf.GetOutputPort())
                # increase this integer set number of iterations if smoother surface wanted
                smoother.SetNumberOfIterations(30)
                smoother.NonManifoldSmoothingOn()
                smoother.NormalizeCoordinatesOn() 
                #The positions can be translated and scaled such that they fit within a range of [-1, 1] prior to the smoothing computation
                smoother.GenerateErrorScalarsOn()
                smoother.Update()
                # save the output
                writer = vtk.vtkSTLWriter()
                writer.SetInputConnection(smoother.GetOutputPort())
                writer.SetFileTypeToASCII()
                # file name need to be changed
                # save as the .stl file, can be changed to other surface mesh file
                writer.SetFileName(stl_path + '/' + str(tag) + '.stl')
                writer.Write()






