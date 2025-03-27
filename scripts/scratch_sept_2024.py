import bpy

import numpy as np
    
import os
import random

import bpy

bottom=bpy.data.node_groups["Geometry Nodes"].nodes["Boolean"]
black=bpy.data.scenes["Scene.001"].node_tree.nodes["Switch"]
mask=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Value.001"].outputs[0]


#size=bpy.data.node_groups["Geometry Nodes"].nodes["Ico Sphere"].inputs[0]
X_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.004"].inputs[1]

Y_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.005"].inputs[1]

Scratch_length=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.006"].inputs[1]

Noise_scale=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Group"].inputs[0]

Scratch_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Vector Math.001"].inputs[1]

Scratch_disp.default_value[0] = np.random.uniform(0.1,0.45, 1)  # Horizontal
Scratch_disp.default_value[1]=np.random.uniform(0.06,0.6, 1) # Vertical
Noise_scale.default_value=np.random.uniform(0,10.2, 1)

Scratch_length_min=10.5
Scratch_length_max=30.5

Scratch_length.default_value = np.random.uniform(Scratch_length_min,Scratch_length_max, 1)



src_dir="C:/Inspec/BladeSYNS/Backgrounds/"

image_list = os.listdir(src_dir)

background=bpy.data.scenes["Scene.001"].node_tree.nodes["Image"]

def randomize_background(src_dir,image_list):
    random_back = random.randint(0, len(image_list)-1)
    img_back=os.path.join(src_dir, image_list[random_back])
    background.image = bpy.data.images.load(img_back)
    
    return random_back


bb=randomize_background(src_dir,image_list)






Top_angle=bpy.data.node_groups["Geometry Nodes"].nodes["Transform Geometry"].inputs[2]
bottom_angle=bpy.data.node_groups["Geometry Nodes.001"].nodes["Transform Geometry"].inputs[2]




def rotate_obj(angle):
    th=angle*np.pi/180
    Top_angle.default_value[0]=th
    bottom_angle.default_value[0]=th
    
    
    
view_angle=np.random.uniform(-50,50, 1)
rotate_obj(view_angle)


sun_light=bpy.data.lights["Sun.001"]
world_light=bpy.data.worlds["World.001"].node_tree.nodes["Background"].inputs[1]
world_light.default_value = 1
sun_light.energy=1000



def randomize_light(sun_light,world_light):
    pp=np.random.uniform(0, 1, 2)
    
    if pp[0]>0.5:
        sun_light.energy=np.random.uniform(200,700, 1)
    else:
        sun_light.energy=900
    if pp[1]>0.5:
        world_light.default_value =np.random.uniform(0.1,0.9, 1)
    else:
        world_light.default_value = 1

randomize_light(sun_light,world_light)

def gt():
    black.check = True
    bottom.boolean=False
    mask.default_value = 1 

def image():
    black.check = False
    bottom.boolean=True
    mask.default_value = 0 

image()
X_disp_min=0.21
X_disp_max=0.5

Y_disp_min=0.6
Y_disp_max=1.15



#X_disp.default_value = X_disp_min
#Y_disp.default_value = Y_disp_min


scene = bpy.context.scene

Numper_of_images=2000

for nn in range(0,Numper_of_images):
    image()
    #break
    
    
    Scratch_disp.default_value[0] = np.random.uniform(0.1,0.45, 1)  # Horizontal
    Scratch_disp.default_value[1]=np.random.uniform(0.06,0.6, 1) # Vertical
    Noise_scale.default_value=np.random.uniform(0,10.2, 1)

    Scratch_length.default_value = np.random.uniform(Scratch_length_min,Scratch_length_max, 1)


    
    view_angle=np.random.uniform(-50,50, 1)
    rotate_obj(view_angle)
    randomize_light(sun_light,world_light)
    
    b=randomize_background(src_dir,image_list)
    file_name = f"scratch_draft_sept_16\\image_{nn}_background_{b}.png"
    file_name_gt = f"scratch_draft_sept_16\\mask_{nn}__background_{b}.png"
    bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name
    bpy.ops.render.render(write_still=True)
    gt()
    bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name_gt
    bpy.ops.render.render(write_still=True)
# Define the ranges for X_disp and Y_disp
#x_range = np.linspace(X_disp_min,X_disp_max,40) # Replace -10 and 11 with desired limits
#y_range = np.linspace(Y_disp_min,Y_disp_max,40)   # Replace -5 and 6 with desired limits

#for x in x_range:
#    for y in y_range:
#        image()
#        #break
#        X_disp.default_value=x
#        Y_disp.default_value=y
#        
#        file_name = f"Dents_v1\\image_{x}_{y}.png"
#        file_name_gt = f"Dents_v1\\mask_{x}_{y}.png"
#        bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name
#        bpy.ops.render.render(write_still=True)
#        gt()
#        bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name_gt
#        bpy.ops.render.render(write_still=True)


image()
