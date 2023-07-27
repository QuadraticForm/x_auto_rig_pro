import bpy
from .objects import *
from .version import blender_version
from .types_convert import *


def get_selected_pose_bones():
    return bpy.context.selected_pose_bones


def get_pose_bone(name):
    return bpy.context.active_object.pose.bones.get(name)

	
def get_custom_shape_scale_prop_name():  
    if bpy.app.version >= (3,0,0):
        return 'custom_shape_scale_xyz'
    else:
        return 'custom_shape_scale'
        
    
def set_custom_shape_scale(pbone, scale):   
    if bpy.app.version >= (3,0,0):
        # uniform scale
        if type(scale) == int or type(scale) == float:
            for i in range(0,3):
                pbone.custom_shape_scale_xyz[i] = scale
        # array scale
        else:
            pbone.custom_shape_scale_xyz = scale
    # pre-Blender 3.0
    else:
        pbone.custom_shape_scale = scale
            

def get_custom_shape_scale(pbone, uniform=True, as_list=False):   
    if bpy.app.version >= (3,0,0):
        if uniform:       
            # uniform scale
            val = 0
            for i in range(0,3):
                val += pbone.custom_shape_scale_xyz[i]
            return val/3     
        # array scale
        else:
            if as_list:
                return vector_to_list(pbone.custom_shape_scale_xyz)
            else:
                return pbone.custom_shape_scale_xyz
    # pre-Blender 3.0
    else:        
        return pbone.custom_shape_scale
		
		
def set_bone_custom_shape(pbone, cs_name):
    cs = get_object(cs_name)
    if cs == None:        
        append_from_arp(nodes=[cs_name], type='object')
        cs = get_object(cs_name)

    pbone.custom_shape = cs


def set_bone_color_group(obj, pb, grp_name):
    grp_color_body_mid = (0.0, 1.0, 0.0)
    grp_color_body_left = (1.0, 0.0, 0.0)
    grp_color_body_right = (0.0, 0.0, 1.0)

    grp = obj.pose.bone_groups.get(grp_name)
    if grp == None:
        grp = obj.pose.bone_groups.new(name=grp_name)
        grp.color_set = 'CUSTOM'

        grp_color = None
        if grp_name == "body_mid":
            grp_color = grp_color_body_mid
        elif grp_name == "body_left":
            grp_color = grp_color_body_left
        elif grp_name == "body_right":
            grp_color = grp_color_body_right
        elif grp_name == 'yellow':
            grp_color = (1.0, 1.0, 0.0)

        # set normal color
        grp.colors.normal = grp_color
        # set select color/active color
        for col_idx in range(0,3):
            grp.colors.select[col_idx] = grp_color[col_idx] + 0.2
            grp.colors.active[col_idx] = grp_color[col_idx] + 0.4

    pb.bone_group = grp
    
    
def reset_pbone_transforms(pbone):
    pbone.location = [0,0,0]
    pbone.rotation_euler = [0,0,0]
    pbone.rotation_quaternion = [1,0,0,0]
    pbone.scale = [1,1,1]     