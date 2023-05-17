import os, bpy, sys, glob, math, re

from math import radians
from PIL import Image, ImageDraw

########################################
#
# Mandatory parameters
# set these paths and then click run script
# examples for windows, linux and mac can be found below
#
########################################

print("")
print("Beginning Library Creation")
print("")

########################################
#
# Set Root Library Directory
#
########################################

#uncomment depending on OS, use '/'
#Windows Format
#library_dir = "C:/Your_STL_Library_Folder/"
#Linux Format
#library_dir = "/home/user/librarian"

########################################
#
# Parameters with sensible defaults
#
########################################

width = 500
height = 500
anim_frames = 16
anim_seconds = 2000
anim_scale = 100

########################################
#
# Program Start
#
########################################

#render settings
scene = bpy.data.scenes["Scene"]
scene.render.resolution_x = width
scene.render.resolution_y = height
scene.render.image_settings.file_format='JPEG'

#this script two materials to be present in the scene
mat = bpy.data.materials.get("Material") #used for the object itself
textmat = bpy.data.materials.get("TextMaterial") #used for the label

pi = 3.14159265

cam_rot = scene.camera.rotation_euler

bpy.ops.object.select_all(action='DESELECT')

#recursively generate and sort list of full file paths starting in root library_dir
file_paths = list(glob.iglob(library_dir + '**/*.stl', recursive=True))
file_paths.sort

# Replace any backslashes with regular slashes for consistency
# Likely not needed on linux systems but shouldn't cause any issues
for i,fp in enumerate(file_paths):
    fp_corrected = re.sub(r'\\', r'/',fp)
    file_paths[i] = fp_corrected

########################################
#
# Library Image/Gif Creation
#
# loop through list of stl filepaths and create a preview image and gif for each
# both use the filepath with stl stripped off (fp_no_ext) with added suffix
#
# preview image: fp_no_ext + ".jpg"
# gif frames: fp_no_ext + "_frame_" + str(index) + ".jpg"
# gif file: fp_no_ext + "_anim.gif"
#
########################################
for i, fp in enumerate(file_paths):
    # Removes .stl file extension from filepath
    fp_no_ext = re.sub(r'\.stl', r'', fp) 
    if (i < 1000): #set this to a low value for testing
        #load model
        bpy.ops.import_mesh.stl(filepath=fp,axis_up='Z')
        ob = bpy.context.active_object
        modelname = ob.name

        #get center of object
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
        ob.location = (0, 0, 0)
                        
        #set material
        ob.data.materials.append(mat)

        #calculate good text position
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        x = ob.location.x
        y = ob.location.y
        z = ob.location.z + max(ob.dimensions.z / 1.2, ob.dimensions.x / 2, ob.dimensions.y / 2)

        #create label
        bpy.ops.object.text_add(location=(x,y,z), radius=1)
        textobject=bpy.context.object
        textobject.data.body = modelname
        
        #position text
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        textobject.location = (x, y, z)

        #align text to camera
        textobject.rotation_euler = cam_rot
        
        #scale text to match model
        obj_size = math.sqrt(ob.dimensions[0]**2 + ob.dimensions[1]**2 + ob.dimensions[2]**2)
        print (obj_size)
        text_size = math.sqrt(textobject.dimensions[0]**2 + textobject.dimensions[1]**2 + textobject.dimensions[2]**2)
        print (text_size)
        scale = obj_size / (text_size * 2)
        print ("scale", scale)
        textobject.scale = (scale, scale, scale)

        #text material
        textobject.data.materials.append(textmat)

        #focus camera on object and make text visible
        ob.select_set(True)
        textobject.select_set(True)
        scene.camera.data.angle = radians(45)
        bpy.ops.view3d.camera_to_view_selected()
        scene.camera.data.angle = radians(50)
        
        #set render properties and render still preview image
        scene.render.resolution_percentage = 100
        bpy.context.scene.render.filepath = fp_no_ext + ".jpg"
        bpy.ops.render.render(use_viewport = True, write_still=True)

        #Delete text
        ob.select_set(False)
        bpy.ops.object.delete() 
        ob.select_set(True)
        
        #reposition camera
        scene.camera.data.angle = radians(45)
        bpy.ops.view3d.camera_to_view_selected()
        scene.camera.data.angle = radians(60)
        loc = scene.camera.location
        camera_z = scene.camera.location[2]
        distance = math.sqrt(loc[0] * loc[0] + loc[1] * loc[1])
    
        #create set number of frames for gif
        animnames = []
        for index in range(anim_frames):
            # rotate camera based on angle
            angle = index * (360 / anim_frames)
            scene.camera.rotation_euler = (radians(45), 0.0, radians(angle))
            scene.camera.location = (math.sin(radians(angle)) * distance, -1 * math.cos(radians(angle)) * distance, camera_z)
            
            #set render properties and render
            scene.render.resolution_percentage = anim_scale
            filename = fp_no_ext + "_frame_" + str(index) + ".jpg"
            animnames.append(filename)
            bpy.context.scene.render.filepath = filename
            bpy.ops.render.render(use_viewport = True, write_still=True)

        #convert frame images to RGB and store in array
        anim = []
        for index in range(anim_frames):
            im = Image.open(animnames[index],mode='r')
            im = im.convert('RGB')
            im = im.quantize()
            anim.append(im)
        
        #create rotation gif using frame image array
        gifim = anim[0]
        gifim.save(fp_no_ext + "_anim.gif", save_all=True, optimize=True, append_images=anim[1:anim_frames], duration=anim_seconds/anim_frames, loop=0)

        #delete individual frame images once gif is created
        for im in animnames:
            if os.path.exists(im):
                os.remove(im)
                
        #delete object
        bpy.ops.object.delete() 

########################################
#        
# HTML Page Creation
#
########################################

#html header
html_top = """
<!doctype html>

<html>
    <head>
        <style>"""

#divider that specifies the directory containing the listed files
css_directory_template = """
<hr class="rounded">
<h1>{0}</h1>
<hr class="rounded">
"""

#template pair that adds both the preview still image and gif on mouse over
css_template= """
        div.img{0} {{
            background-image: url('{1}.jpg');
            width: {2}px;
            height: {3}px;
            display: inline-block;
            border: 1px solid black;
        }}
        div.img{0}:hover {{
            background-image: url('{1}_anim.gif');
            background-size: contain;
        }}"""

#actual element to be added to page referencing template
image_template = """
<div class="img{0}" title="{1}">&nbsp;</div>"""

# create html file and then loop through list of stl files once to add css templates and again to add html elements
with open(library_dir + "stl-model-register.html", "w") as file:
    file.write(html_top)
    #Build underlying CSS entries
    for i, fp in enumerate(file_paths):
        fp_no_ext = re.sub(r'\.stl', r'', fp)
        file.write(css_template.format(i, fp_no_ext, width, height))
    file.write("</style></head><body>")

    #start filepath variables as empty
    #when the current does not equal the previous then a divider is added with new filepath
    fp_dir = ""
    fp_dir_prev = ""
    
    #Add visible elements to page using CSS entries
    for i, fp in enumerate(file_paths):
        #remove file name from filepath (everything between the last / and end)
        fp_dir = re.sub(r'[^/]*$',r'',fp)
        #for each new directory add a divider with the directory path
        if fp_dir != fp_dir_prev:
            file.write(css_directory_template.format(fp_dir))
        #remove stl extension from file path
        fp_no_ext = re.sub(r'\.stl', r'', fp)
        file.write(image_template.format(i, fp_no_ext))
        fp_dir_prev = fp_dir
    file.write("</body></html>")
    
print("")
print("Completed Library Creation")
print("")

########################################
#        
# Program End
#
########################################
