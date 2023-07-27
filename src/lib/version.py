import bpy
import addon_utils                  

class ARP_blender_version:
    _string = bpy.app.version_string
    blender_v = bpy.app.version
    _float = 0.0
    
    def __init__(self):
        str = ''.join([i for i in self._string if i in '0123456789'])#int(_string.replace('.', ''))#blender_v[0]*100+blender_v[1]+blender_v[2]*0.01
        self._float = float(str)
        if len(str) > 3:# hu! some version are defined as '3.00', some as '2.93.9'
            self._float = float(str)/10
        
blender_version = ARP_blender_version()


def is_proxy(obj):
    # proxy atttribute removed in Blender 3.3
    if 'proxy' in dir(obj):
        if obj.proxy:
            return True
    return False


def get_autorigpro_version():
    addons = addon_utils.modules()[:]
    
    for addon in addons:    
        if addon.bl_info['name'].startswith('Auto-Rig Pro'):
            print(addon)
            print()
            ver_list = addon.bl_info.get('version')
            ver_string = str(ver_list[0]) + str(ver_list[1]) + str(ver_list[2])
            ver_int = int(ver_string)
            return ver_int
            
            
def ver_int_to_str(version_int):
    to_str = str(version_int)
    return to_str[0] + '.' + to_str[1] + to_str[2] + '.' + to_str[3] + to_str[4]


def convert_drivers_cs_to_xyz(armature):
    # Blender 3.0 requires Vector3 custom_shape_scale values
    # convert single uniform driver to vector3 array drivers
    drivers_armature = [i for i in armature.animation_data.drivers]   
    
    for dr in drivers_armature:
        if 'custom_shape_scale' in dr.data_path:
            if not 'custom_shape_scale_xyz' in dr.data_path:                      
                for i in range(0, 3):
                    new_dr = armature.animation_data.drivers.from_existing(src_driver=dr)
                    new_dr.data_path = new_dr.data_path.replace('custom_shape_scale', 'custom_shape_scale_xyz')
                    new_dr.array_index = i
                    new_dr.driver.expression += ''# update hack

                armature.driver_remove(dr.data_path, dr.array_index)                
                
    # tag in prop
    armature.data["arp_updated_3.0"] = True
    print("Converted custom shape scale drivers to xyz")


def is_fc_bb_param(fc, param):    
    # is the fcurve a bendy-bones parameter?
    # bendy-bones params data path depends on the Blender version
    
    # scale are array
    #   scale in
    if param == 'bbone_scaleinx':       
        if get_bbone_param_name(param) in fc.data_path:
            if (bpy.app.version >= (3,0,0) and fc.array_index == 0) or (bpy.app.version < (3,0,0)):
                return True
    elif param == 'bbone_scaleiny':     
        if get_bbone_param_name(param) in fc.data_path:
            if (bpy.app.version >= (3,0,0) and fc.array_index == 1) or (bpy.app.version < (3,0,0)):
                return True
    elif param == 'bbone_scaleinz': 
        if 'bbone_scalein' in fc.data_path:# only in Blender 3.0 and after
            if (bpy.app.version >= (3,0,0) and fc.array_index == 2):
                return True
        
    #   scale out
    elif param == 'bbone_scaleoutx':    
        if get_bbone_param_name(param) in fc.data_path:
            if (bpy.app.version >= (3,0,0) and fc.array_index == 0) or (bpy.app.version < (3,0,0)):
                return True
    elif param == 'bbone_scaleouty':    
        if get_bbone_param_name(param) in fc.data_path:
            if (bpy.app.version >= (3,0,0) and fc.array_index == 1) or (bpy.app.version < (3,0,0)):
                return True
    elif param == 'bbone_scaleoutz':
        if 'bbone_scaleout' in fc.data_path:# only in Blender 3.0 and after
            if (bpy.app.version >= (3,0,0) and fc.array_index == 2):
                return True


def get_bbone_param_name(setting):
    # bendy-bones setting name depending on the Blender version   
    # curve out
    if setting == 'bbone_curveoutz':
        if bpy.app.version < (3,0,0):
            return 'bbone_curveouty'
        else:
            return 'bbone_curveoutz'
    # curve in
    elif setting == 'bbone_curveinz':
        if bpy.app.version < (3,0,0):
            return 'bbone_curveiny'
        else:
            return 'bbone_curveinz'
            
    # scale in X
    elif setting == 'bbone_scaleinx':
        if bpy.app.version < (3,0,0):
            return 'bbone_scaleinx'
        else:
            return 'bbone_scalein'
    # scale in Y
    elif setting == 'bbone_scaleiny':
        if bpy.app.version < (3,0,0):
            return 'bbone_scaleiny'
        else:
            return 'bbone_scalein'
            
    # scale out X
    elif setting == 'bbone_scaleoutx':
        if bpy.app.version < (3,0,0):
            return 'bbone_scaleoutx'
        else:
            return 'bbone_scaleout'
    # scale in Y
    elif setting == 'bbone_scaleouty':
        if bpy.app.version < (3,0,0):
            return 'bbone_scaleouty'
        else:
            return 'bbone_scaleout' 


def check_id_root(action):    
    if bpy.app.version >= (2,90,1):
        if getattr(action, "id_root", None) == "OBJECT":
            return True
        else:
            return False
    else:
        return True
        
        
def invert_angle_with_blender_versions(angle=None, bone=False, axis=None):
    # Deprecated!
    # Use rotate_edit_bone() and rotate_object() instead
    #
    # bpy.ops.transform.rotate has inverted angle value depending on the Blender version
    # this function is necessary to support these version specificities
  
    invert = False
    if bone == False:
        if (bpy.app.version >= (2,83,0) and bpy.app.version < (2,90,0)) or (bpy.app.version >= (2,90,1) and bpy.app.version < (2,90,2)):
            invert = True

    elif bone == True:
        # bone rotation support
        # the rotation direction is inverted in Blender 2.83 only for Z axis
        if axis == "Z":
            if bpy.app.version >= (2,83,0) and bpy.app.version < (2,90,0):
                invert = True
        # the rotation direction is inverted for all but Z axis in Blender 2.90 and higher
        if axis != "Z":
            if bpy.app.version >= (2,90,0):
                invert = True

    if invert:
        angle = -angle

    return angle
    
def enable_constraint(cns, value):
    if bpy.app.version >= (3,0,0):
        cns.enabled = value
    else:
        cns.mute = not value
        