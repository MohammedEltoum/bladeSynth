import bpy

import numpy as np

import os      
import random

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024


bottom=bpy.data.node_groups["Geometry Nodes"].nodes["Boolean"]
black=bpy.data.scenes["Scene.001"].node_tree.nodes["Switch"]
mask=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Value.001"].outputs[0]
#X_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.004"].inputs[1]

#Y_disp=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Math.005"].inputs[1]

Noise_w=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Noise Texture.002"].inputs[1]
Noise_coordinates=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Mapping.007"].inputs[1]

Corrosion_color=bpy.data.materials["Steel - Satin.001"].node_tree.nodes["Color Ramp.005"].color_ramp.elements[2]
Corrosion_color.position = 0.2

Top_angle=bpy.data.node_groups["Geometry Nodes"].nodes["Transform Geometry"].inputs[2]
bottom_angle=bpy.data.node_groups["Geometry Nodes.001"].nodes["Transform Geometry"].inputs[2]

sun_light=bpy.data.lights["Sun.001"]
world_light=bpy.data.worlds["World.001"].node_tree.nodes["Background"].inputs[1]
world_light.default_value = 1
sun_light.energy=100


src_dir="C:/Inspec/BladeSYNS/Backgrounds/"

image_list = os.listdir(src_dir)

background=bpy.data.scenes["Scene.001"].node_tree.nodes["Image"]



def randomize_background(src_dir,image_list):
    random_back = random.randint(0, len(image_list)-1)
    random_back=28
    img_back=os.path.join(src_dir, image_list[random_back])
    background.image = bpy.data.images.load(img_back)
    return random_back

def randomize_light(sun_light,world_light):
    pp=np.random.uniform(0, 1, 2)
    
    if pp[0]>0.5:
        sun_light.energy=np.random.uniform(200,700, 1)
    else:
        sun_light.energy=700
    if pp[1]>0.5:
        world_light.default_value =np.random.uniform(0.1,0.8, 1)
    else:
        world_light.default_value = 1

def rotate_obj(angle):
    th=angle*np.pi/180
    Top_angle.default_value[0]=th
    bottom_angle.default_value[0]=th
    
view_angle=np.random.uniform(-50,50, 1)
rotate_obj(view_angle)
randomize_light(sun_light,world_light)

randomlist = np.random.uniform(-1, 1, 3)
randomlist[-1]=0
Corrosion_color.position = np.random.uniform(0.2, 0.6, 1)
Noise_coordinates.default_value = randomlist
def gt():
    black.check = True
    bottom.boolean=False
    mask.default_value = 1 

def image():
    black.check = False
    bottom.boolean=True
    mask.default_value = 0 
image()

Noise_w.default_value=np.random.uniform(0, 10, 1)






#bpy.ops.image.open(filepath="//..\\..\\..\\..\\Inspec\\BladeSYNS\\Backgrounds\\13.jpg", directory="C:\\Inspec\\BladeSYNS\\Backgrounds\\", files=[{"name":"13.jpg", "name":"13.jpg"}], show_multiview=False)
#bpy.data.images["22.jpg"].name = img_back

Numper_of_images=2000

for nn in range(0,Numper_of_images):

        image()
        view_angle=np.random.uniform(-50,50, 1)
        rotate_obj(view_angle)
        randomize_light(sun_light,world_light)
        
        b=randomize_background(src_dir,image_list)
        
        randomlist = np.random.uniform(-1, 1, 3)
        randomlist[-1]=0

        Noise_coordinates.default_value = randomlist
        Noise_w.default_value=np.random.uniform(0, 10, 1)
        Corrosion_color.position = np.random.uniform(0.2, 0.6, 1)
        
        file_name = f"Corrosion_draft_sept_30\\image_{nn}.png"
        file_name_gt = f"Corrosion_draft_sept_30\\mask_{nn}.png"
        bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name
        bpy.ops.render.render(write_still=True)
        gt()
        bpy.context.scene.render.filepath = "//..\\..\\..\\..\\Inspec\\BladeSYNS\\" + file_name_gt
        bpy.ops.render.render(write_still=True)
        
image()