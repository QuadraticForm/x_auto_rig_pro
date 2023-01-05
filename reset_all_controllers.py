#############################################################
## Reset All functions used to reset bone controllers positions
## to be used when posing or animating the character.
## Accessed from the picker "Reset" button
## and from the "Reset All" buttons from the N-key panel, 
## Rig Main Properties tab
#############################################################

import bpy


# FUNCTIONS ------------------------------------
def get_blender_version():
    ver = bpy.app.version
    return ver[0]*100+ver[1]+ver[2]*0.01
    
    
def get_prop_setting(node, prop_name, setting):    
    if bpy.app.version >= (3,0,0):
        return node.id_properties_ui(prop_name).as_dict()[setting]
    else:
        return node['_RNA_UI'][prop_name][setting]
    
    
def set_inverse_child(b, cns):			
    # direct inverse matrix method
    if cns.subtarget != "":
        if bpy.context.active_object.data.bones.get(cns.subtarget):           
            cns.inverse_matrix = bpy.context.active_object.pose.bones[cns.subtarget].matrix.inverted()	
    else:
        print("Child Of constraint could not be reset, bone does not exist:", cns.subtarget, cns.name)
        
             
def is_reset_bone(bone_name):    
    reset_bones_parent = ["c_foot_ik", "c_hand_ik"]
    
    for n in reset_bones_parent:
        if n in bone_name:
            return True 

            
def reset_all_controllers():
    # the function is run at startup, in case of error, exit
    try:
        bpy.context.active_object
    except:
        return
        
    #save display layers
    saved_layers = [layer_bool for layer_bool in bpy.context.active_object.data.layers]


    #display layer 8 for neck child of reset
    disp_layer = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,22,23,24,25,26,27,28,29,30,31]
    for idx in disp_layer:
        bpy.context.active_object.data.layers[idx] = True
        
    bones_data = bpy.context.active_object.data.bones

    # Reset Properties
    for bone in bpy.context.object.pose.bones:
        bone_parent = ""
        try:
            bone_parent = bone.parent.name
        except:
            pass
        
        if (bone.name.startswith('c_') or bone.name.startswith("cc_") or 'cc' in bone.keys()) and bone_parent != "Picker": 
            bone.location = [0.0,0.0,0.0]
            bone.rotation_euler = [0.0,0.0,0.0]            
            bone.rotation_quaternion = [1.0,0.0,0.0,0.0]
            bone.scale = [1.0,1.0,1.0]
        
        if len(bone.keys()):
            try:# Error in some rare cases > Error RuntimeError: IDPropertyGroup changed size during iteration   
                for key in bone.keys():
                    
                    if key == 'ik_fk_switch':                        
                        try:
                            bone['ik_fk_switch'] = get_prop_setting(bone, 'ik_fk_switch', 'default')                          
                        except:
                            if 'hand' in bone.name:
                                bone['ik_fk_switch'] = 1.0
                            else:
                                bone['ik_fk_switch'] = 0.0                       
                       
                    if key == 'stretch_length':
                        bone[key] = 1.0
                    # don't set auto-stretch to 1 for now, it's not compatible with Fbx export         
                    if key == 'leg_pin':
                        bone[key] = 0.0
                    if key == 'elbow_min':             
                        bone[key] = 0.0                        
                    if key == 'bend_all':
                        bone[key] = 0.0                    
                    if key == 'fingers_grasp':
                        bone[key] = 0.0                    
                    if key == 'thigh_twist':
                        bone[key] = 0.0                    
                    if key == 'arm_twist':
                        bone[key] = 0.0
                        
            except:
                pass
              
    #hide layers
    for i, layer_bool in enumerate(saved_layers):
        bpy.context.active_object.data.layers[i] = layer_bool

    bpy.ops.pose.select_all(action='DESELECT')
    
# necessary, since the picker execute scripts instead of calling functions 
reset_all_controllers()


