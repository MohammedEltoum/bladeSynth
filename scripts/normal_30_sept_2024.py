
#import bpy




import bpy

import numpy as np
    
import os
import random

import bpy


Top_angle=bpy.data.node_groups["Geometry Nodes"].nodes["Transform Geometry.002"].inputs[2]
bottom_angle=bpy.data.node_groups["Geometry Nodes.001"].nodes["Transform Geometry"].inputs[2]



src_dir="C:/Inspec/BladeSYNS/Backgrounds/"

image_list = os.listdir(src_dir)

background=bpy.data.scenes["Scene.001"].node_tree.nodes["Image"]


sun_light=bpy.data.lights["Sun"]
world_light=bpy.data.worlds["World.001"].node_tree.nodes["Background"].inputs[1]
world_light.default_value = 1
sun_light.energy=1000



def randomize_light(sun_light,world_light):
    pp=np.random.uniform(0, 1, 2)
    
    if pp[0]>0.5:
        sun_light.energy=np.random.uniform(200,800, 1)
    else:
        sun_light.energy=900
    if pp[1]>0.5:
        world_light.default_value =np.random.uniform(0.1,1, 1)
    else:
        world_light.default_value = 1


def rotate_obj(angle):
    th=angle*np.pi/180
    Top_angle.default_value[0]=th
    bottom_angle.default_value[0]=th

def randomize_background(src_dir,image_list):
    random_back = random.randint(0, len(image_list)-1)
    random_back=28
    img_back=os.path.join(src_dir, image_list[random_back])
    background.image = bpy.data.images.load(img_back)
    
    return random_back


bb=randomize_background(src_dir,image_list)

view_angle=np.random.uniform(-50,50, 1)
rotate_obj(view_angle)
randomize_light(sun_light,world_light)


bottom=bpy.data.node_groups["Geometry Nodes.001"].nodes["Boolean"]
black=bpy.data.scenes["Scene.001"].node_tree.nodes["Switch"]
mask=bpy.data.node_groups["Geometry Nodes"].nodes["Boolean"]
size=bpy.data.node_groups["Geometry Nodes"].nodes["Ico Sphere"].inputs[0]

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024



def gt():
    black.check = True
    bottom.boolean=False
    mask.boolean = False

def image():
    black.check = False
    bottom.boolean=True
    mask.boolean = True

image()
#gt()

#X_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.004"].inputs[1]

#Y_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.005"].inputs[1]

#Noise_w=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Noise Texture.002"].inputs[1]

loc=bpy.data.node_groups["Geometry Nodes"].nodes["Sample Curve"].inputs[7]

loc.default_value = 0

size.default_value = 0.1


#X_disp_min=0.21
#X_disp_max=0.5

#Y_disp_min=0.6
#Y_disp_max=1.15

#X_disp.default_value = X_disp_min
#Y_disp.default_value = Y_disp_min

#GT_status.default_value=0
scene = bpy.context.scene
image()
loc_min=0
loc_max=0.98

size_min=0.1
size_max=0.25

loc_rand = np.random.uniform(loc_min, loc_max, 1) 
size_rand = np.random.uniform(size_min,size_max,1) 


size.default_value=size_rand

            
loc.default_value=loc_rand

Numper_of_images=77
start_i=1924

for nn in range(start_i,start_i+Numper_of_images):
    image()
    #break
    
    
    loc_rand = np.random.uniform(loc_min, loc_max, 1) 
    size_rand = np.random.uniform(size_min,size_max,1) 
    size.default_value=size_rand      
    loc.default_value=loc_rand
    
    view_angle=np.random.uniform(-50,50, 1)
    rotate_obj(view_angle)
    randomize_light(sun_light,world_light)
    
    b=randomize_background(src_dir,image_list)
    file_name = f"nick_draft_sept_30\\image_{nn}.png"
    file_name_gt = f"nick_draft_sept_30\mask_{nn}.png"
    bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name
    bpy.ops.render.render(write_still=True)
    gt()
    bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name_gt
    bpy.ops.render.render(write_still=True)
# Define the ranges for X_disp and Y_disp
#for s in size_range:
#    size.default_value=s
#    for x in loc_range:

#            #break
#            #Noise_w.default_value=x
#            image()
#            loc.default_value=x
#            file_name = f"nick_v2\\image_{x}_{s}.png"
#            file_name_gt = f"nick_v2\\mask_{x}_{s}.png"
#            bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name
#            bpy.ops.render.render(write_still=True)
#            gt()
#            bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name_gt
#            bpy.ops.render.render(write_still=True)
## Set the render engine to 'CYCLES'
#bpy.context.scene.render.engine = 'CYCLES'


## Render the scene
#bpy.ops.render.render(write_still = True)

#for obj in scene.objects:
#    obj.location.x += 2.0

#GT_status.default_value=0

#file_name="image2.png"
#bpy.ops.image.save_as(save_as_render=True, copy=True, filepath="//..\\..\\..\\..\\Inspec\\BladeSYNS\\img.png" , relative_path=True, show_multiview=False, use_multiview=False)
#bpy.ops.image.save_as(save_as_render=True, copy=True, filepath="//..\\..\\..\\..\\Inspec\\BladeSYNS\\im2.png", relative_path=True, show_multiview=False, use_multiview=False)
image()