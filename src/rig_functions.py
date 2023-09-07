import bpy, os, ast
from bpy.types import (Operator, Menu, Panel, UIList, PropertyGroup, FloatProperty, StringProperty, BoolProperty)
from bpy.props import *
from mathutils import *
from math import *
from bpy.app.handlers import persistent
from . import auto_rig_datas
from . import reset_all_controllers
from operator import itemgetter


# Global vars
hands_ctrl = ["c_hand_ik", "c_hand_fk"]
sides = [".l", ".r"]
eye_aim_bones = ["c_eye_target.x", "c_eye"]
auto_eyelids_bones = ["c_eye", "c_eyelid_top", "c_eyelid_bot"]
fk_arm = ["c_arm_fk", "c_forearm_fk", "c_hand_fk", "arm_fk_pole"]
ik_arm = ["arm_ik", "forearm_ik", "c_hand_ik", "c_arms_pole", "c_arm_ik"]
fk_leg = ["c_thigh_fk", "c_leg_fk", "c_foot_fk", "c_toes_fk", "leg_fk_pole"]
ik_leg = ["thigh_ik", "leg_ik", "c_foot_ik", "c_leg_pole", "c_toes_ik", "c_foot_01", "c_foot_roll_cursor", "foot_snap_fk", "c_thigh_ik", "c_toes_pivot", "c_foot_ik_offset", "c_thigh_b"]
fingers_root = ["c_index1_base", "c_thumb1_base", "c_middle1_base", "c_ring1_base", "c_pinky1_base"]
fingers_start = ["c_thumb", "c_index", "c_middle", "c_ring", "c_pinky"]
fingers_type_list = ["thumb", "index", "middle", "ring", "pinky"]

                        

# versioning utils, update functions, must be first
def is_proxy(obj):
    # proxy atttribute removed in Blender 3.3
    if 'proxy' in dir(obj):
        if obj.proxy:
            return True
    return False
    
    
def get_blender_version():
    ver = bpy.app.version
    return ver[0]*100+ver[1]+ver[2]*0.01
        
        
def get_override_dict_compat():    
    if bpy.app.version >= (2,91,0):     
        return {'LIBRARY_OVERRIDABLE', 'USE_INSERTION'}
    else:      
        return {'LIBRARY_OVERRIDABLE'}


# if layers viz are animated, update on each frame
@persistent   
def rig_layers_anim_update(foo):   
    if bpy.context.scene.arp_layers_animated:
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                if 'layers_sets' in obj.keys():
                    for lay in obj.layers_sets:
                        lay.visibility_toggle = lay.visibility_toggle# hacky but works

        
def update_visibility_toggle(self, context):
    set_layer_vis(self, self.visibility_toggle)
    
    
def update_layer_select(self, context):
    if self.update_saved_layers == False:
        return

    rig = bpy.context.active_object
    
    def select_bone(bname):
        if bpy.context.mode == "EDIT_ARMATURE":
            b = get_edit_bone(bname)
            if b:
                b.select = True
                
        elif bpy.context.mode == "POSE" or bpy.context.mode == "OBJECT":
            b = get_data_bone(bname)
            if b:
                b.select = True
                
    # bones layer  
    for i, lay in enumerate(self.layers):
        if lay:        
            #rig.data.layers[i] = True# show the layer before selecting
            
            for b in rig.data.bones:                
                if b.layers[i]:
                    select_bone(b.name)     
             

    # bones list
    bones_names = ast.literal_eval(self.bones)
  
    for bname in bones_names:
        select_bone(bname)     

    
    
def update_layer_set_exclusive(self, context):
    if self.update_saved_layers == False:
        return
        
    rig = bpy.context.active_object
    
    # armature layers
    set_layer_vis(self, True)
    
    current_layers_idx = [i for i, l in enumerate(self.layers) if l]    
    
    if self.exclusive_toggle:
        
        # save current displayed layers
        saved_layers = []
        
        for i, lay in enumerate(rig.data.layers):
            if lay:
                saved_layers.append(i)
                
        self.exclusive_saved_layers = str(saved_layers)
        
        # hide other layers
        if len(current_layers_idx):
            for i, lay in enumerate(rig.data.layers):
                if not i in current_layers_idx:
                    rig.data.layers[i] = False
                    
    else:
        # restore saved layers  
        #print(self.exclusive_saved_layers)
        saved_layers = ast.literal_eval(self.exclusive_saved_layers)
        
        for i in saved_layers:
            rig.data.layers[i] = True
    
    # bones       
    bones_list = ast.literal_eval(self.bones)        
    
    if len(bones_list):
        if bpy.context.mode == "EDIT_ARMATURE":
            for eb in rig.data.edit_bones:
                if self.exclusive_toggle:
                    if not eb.name in bones_list:
                        eb.hide = True     
                else:
                    eb.hide = False
                    
        elif bpy.context.mode == "POSE" or bpy.context.mode == "OBJECT":
            for db in rig.data.bones: 
                if self.exclusive_toggle:
                    if not db.name in bones_list:
                        db.hide = True
                else:
                    db.hide = False
                    
                    
    # for now, multiple exclusive layers is not possible, maybe todo later  
    # disable other exclusive toggles    
    for layerset in rig.layers_sets:           
        if layerset != self:
            layerset.update_saved_layers = False# workaround recursion depth issue
            layerset.exclusive_toggle = False
            layerset.update_saved_layers = True
            
    # objects
    # do not set objects visibility exclusively
    # how to restore hidden objects visibility that are not part of any layer?
    
    
# OPERATOR CLASSES ########################################################################################################### 
class ARP_OT_property_pin(Operator):
    """Pin the custom property to this panel (always on display even if the bone is not selected)"""
    bl_idname = "arp.property_pin"
    bl_label = "Property Pin"
    bl_options = {'UNDO'}   
    
    prop_dp_pb: StringProperty(default='')
    prop: StringProperty(default='')
    state: BoolProperty(default=True)
    
    def execute(self, context):        
        #try:
        rig = bpy.context.active_object
        pb = bpy.context.selected_pose_bones[0]
        
        if not 'arp_pinned_props' in rig.data.keys():
            create_custom_prop(node=rig.data, prop_name="arp_pinned_props", prop_val='', prop_description="Pinned custom properties")
        
        
        pinned_props_list = get_pinned_props_list(rig)
        
        def is_dp_in_list(prop_dp):
            if len(pinned_props_list):
                for prop_dp_list in pinned_props_list:                      
                    if prop_dp_list == prop_dp:                        
                        return True                 
                return False
                
            else:                
                return False
            
        
        def pin_prop(prop_dp, check=True):         
            add = False
            if check:                    
                if not is_dp_in_list(prop_dp):                  
                    add = True
            else:
                add = True
            
            if add:                  
                rig.data["arp_pinned_props"] = rig.data["arp_pinned_props"] + prop_dp + ','
                
                
        def unpin_prop(prop_dp):
            if is_dp_in_list(prop_dp):
                pinned_props_copy = [i for i in pinned_props_list]
                rig.data["arp_pinned_props"] = ''# clear   
                # copy back while skipping selected prop
                for prop_copy_dp in pinned_props_copy:
                    if prop_copy_dp == '':
                        continue
                    if prop_copy_dp != prop_dp:
                        pin_prop(prop_copy_dp, check=False)
                
                if len(rig.data["arp_pinned_props"]) == 1:
                     rig.data["arp_pinned_props"] = ''
                        
                        
        if self.state:# Pin          
            pin_prop(pb.path_from_id() + '["'+ self.prop + '"]')
        else:# Unpin       
            unpin_prop(self.prop_dp_pb + '["'+ self.prop + '"]')
                
                    
        #except:
        #    print("Error when pinning prop")
            
        return {'FINISHED'}        


class ARP_OT_layers_add_defaults(Operator):
    """Add default Main and Secondary layer sets"""
    bl_idname = "arp.layers_add_defaults"
    bl_label = "Show All Layers Set"
    bl_options = {'UNDO'}   
  
    def execute(self, context):        
        try:           
            rig = bpy.context.active_object
    
            set1 = rig.layers_sets.add()
            set1.name = 'Main' 
            set1.layers[0] = True          
            
            set2 = rig.layers_sets.add()
            set2.name = 'Secondary'
            set2.layers[1] = True
            
            rig.layers_sets_idx = len(rig.layers_sets)-1
                    
        except:
            pass
            
        return {'FINISHED'}
        
        
class ARP_OT_layers_sets_all_toggle(Operator):
    """Set all layers visibility.\nWhen hiding all, the first layer will remain displayed"""
    bl_idname = "arp.layers_sets_all_toggle"
    bl_label = "Show All Layers Set"
    bl_options = {'UNDO'}   
  
    state: BoolProperty(default=True)
    
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object           
            
            # hide all (at least the first layer must remain enabled)
            if self.state == False:
                rig.data.layers[0] = True
                
            for set in rig.layers_sets:
                # show/hide layers
                for i, lay in enumerate(set.layers):
                    if self.state == False:
                        if i == 0:
                            continue
                    if lay:
                        rig.data.layers[i] = self.state 

                # show/hide objects              
                for obji in set.objects_set:
                    obj = obji.object_item
                    if self.state == True:
                        unhide_object(obj)
                    else:
                        hide_object(obj)
                            
        except:
            pass
            
        return {'FINISHED'}
        

class ARP_MT_layers_sets_menu(Menu):
    bl_label = "Layers Set Specials"

    def draw(self, _context):
        scn = bpy.context.scene
        layout = self.layout
        layout.menu("ARP_MT_layers_sets_menu_import", text="Import", icon='IMPORT')
        layout.menu("ARP_MT_layers_sets_menu_export", text="Export", icon='EXPORT')        
        
        layout.operator('arp.layers_sets_all_toggle', text="Show All", icon='HIDE_OFF').state = True
        layout.operator('arp.layers_sets_all_toggle', text="Hide All", icon='HIDE_ON').state = False
        layout.operator('arp.layers_sets_edit', text="Edit Layer...")    
        layout.prop(scn, "arp_layers_set_render", text="Set Render Visibility")
        layout.prop(scn, "arp_layers_show_exclu", text="Show Exclusive Toggle")
        layout.prop(scn, "arp_layers_show_select", text="Show Select Toggle")
        layout.prop(scn, 'arp_layers_animated', text="Animated Layers")
        

class ARP_MT_layers_sets_menu_import(Menu):
    bl_label = "Layers Set Import"
    
    custom_presets = []
    
    def draw(self, _context):
        layout = self.layout
        layout.operator("arp.layers_set_import", text="From File...")
        layout.separator()
        layout.operator("arp.layers_add_defaults", text="Add Default Layers")
        layout.separator()
        for cp in self.custom_presets:
            op = layout.operator("arp.layers_set_import_preset", text=cp.title()).preset_name = cp
        
        
class ARP_MT_layers_sets_menu_export(Menu):
    bl_label = "Layers Set Export"
    
    def draw(self, _context):
        layout = self.layout
        
        layout.operator("arp.layers_set_export", text="To File...")    
        layout.operator("arp.layers_set_export_preset", text="As New Preset...")
        
        
class ARP_OT_layers_set_import(bpy.types.Operator):
    """ Import the selected preset file"""

    bl_idname = "arp.layers_set_import"
    bl_label = "Import Preset"

    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH", default='py')
    
    
    def execute(self, context):
        scn = bpy.context.scene
        
        try:         
            _import_layers_sets(self)
            
        finally:
            pass
            
        return {'FINISHED'}
        

    def invoke(self, context, event):
        self.filepath = 'layers_set_preset.py'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
        
class ARP_OT_layers_set_import_preset(bpy.types.Operator):
    """ Import the selected preset file"""

    bl_idname = "arp.layers_set_import_preset"
    bl_label = "Import Preset"
   
    preset_name: StringProperty(default='')
    filepath: StringProperty(subtype="FILE_PATH", default='py')
    
    
    def execute(self, context):
        scn = bpy.context.scene
        
        try:         
            # custom presets       
            custom_dir = bpy.context.preferences.addons[__package__.split('.')[0]].preferences.rig_layers_path
            if not (custom_dir.endswith("\\") or custom_dir.endswith('/')):
                custom_dir += '/'
                
            try:
                os.listdir(custom_dir)
            except:
                self.report({'ERROR'}, 'The rig layers presets directory seems invalid: '+custom_dir+'\nCheck the path in the addon preferences')
                return
    
            self.filepath = custom_dir + self.preset_name+'.py'  
            
            _import_layers_sets(self)
            
        finally:
            pass
            
        return {'FINISHED'}

        
class ARP_OT_layers_set_export(Operator):
    """ Export the selected preset file"""

    bl_idname = "arp.layers_set_export"
    bl_label = "Export Preset"

    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH", default='py')
    
    
    def execute(self, context):
        scn = bpy.context.scene
        
        try:         
            _export_layers_sets(self)
            
        finally:
            pass
            
        return {'FINISHED'}
        

    def invoke(self, context, event):
        self.filepath = 'layers_set_preset.py'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
        
class ARP_OT_layers_set_export_preset(Operator):
    """ Export the selected preset file"""

    bl_idname = "arp.layers_set_export_preset"
    bl_label = "Export Preset"
    
    filepath: StringProperty(subtype="FILE_PATH", default='py') 
    preset_name: StringProperty(default='CoolRigLayers')
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name", text="Preset Name")
        
    
    def execute(self, context):
        scn = bpy.context.scene
        
        try:        
            custom_dir = bpy.context.preferences.addons[__package__.split('.')[0]].preferences.rig_layers_path
            if not (custom_dir.endswith("\\") or custom_dir.endswith('/')):
                custom_dir += '/'
                
            if not os.path.exists(os.path.dirname(custom_dir)):
                try:
                    os.makedirs(os.path.dirname(custom_dir))
                except:
                    pass
            """      
            try:
                os.listdir(custom_dir)
            except:
                self.report({'ERROR'}, 'The rig layers presets directory seems invalid: '+custom_dir+'\nCheck the path in the addon preferences')
                return
            """
            
            self.filepath = custom_dir + self.preset_name+'.py'  
            
            _export_layers_sets(self)
            
            update_layers_set_presets()
            
        finally:
            pass
            
        return {'FINISHED'}
        

class ARP_OT_layers_sets_remove_bones(Operator):
    """Removes all bones from the set"""
    bl_idname = "arp.layers_sets_remove_bones"
    bl_label = "Removes Bones From Set" 
  
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object           
            current_set = rig.layers_sets[rig.layers_sets_idx]     
            current_set.bones = '[]'                
        except:
            pass
            
        return {'FINISHED'}
        
        
class ARP_OT_layers_sets_add_bones(Operator):
    """Add selected bones in layer set"""
    bl_idname = "arp.layers_sets_add_bones"
    bl_label = "Add Bones In Set"   
  
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object           
            current_set = rig.layers_sets[rig.layers_sets_idx]
            
            # mirror must be disabled, leads to wrong selection otherwise
            mirror_state = rig.data.use_mirror_x            
            rig.data.use_mirror_x = False
            
            # get selected bones names
            sel_bones_names = []
            
            if context.mode == "POSE":
                sel_bones_names = [i.name for i in bpy.context.selected_pose_bones]
            elif context.mode == "EDIT_ARMATURE":
                sel_bones_names = [i.name for i in bpy.context.selected_editable_bones]
            
            current_list = ast.literal_eval(current_set.bones)
            add_bones_names = [i for i in sel_bones_names if not i in current_list]# check for possible doubles            
            #print("set", add_bones_names)
            current_set.bones = str(current_list + add_bones_names) 
            
            # restore mirror
            rig.data.use_mirror_x = mirror_state
                
        except:
            pass
            
        return {'FINISHED'}
        
        
class ARP_OT_layers_sets_clear_objects(Operator):
    """Clear all objects in set"""
    bl_idname = "arp.layers_sets_clear_objects"
    bl_label = "Clear Objects In Set"   
  
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object           
            current_set = rig.layers_sets[rig.layers_sets_idx]
            
            while len(current_set.objects_set):
                current_set.objects_set.remove(0)
                
        except:
            pass
            
        return {'FINISHED'}        
        
        
class ARP_OT_layers_sets_add_object(Operator):
    """Add object in layer set"""
    bl_idname = "arp.layers_sets_add_object"
    bl_label = "Add Object In Set"   
  
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object           
            current_set = rig.layers_sets[rig.layers_sets_idx]
           
            # check if it's not already in the set
            found = False
            for item in current_set.objects_set:
                if item.object_item == current_set.object_to_add:
                    found = True             
                    break                
        
            # add object entry
            if not found:
                if current_set.object_to_add != None:
                    obj_set = current_set.objects_set.add()
                    obj_set.object_item = current_set.object_to_add
                
        except:
            pass
            
        return {'FINISHED'}
        

class ObjectSet(PropertyGroup):
    object_item : PointerProperty(type=bpy.types.Object)

 
class LayerSet(PropertyGroup):  
    exclusive_toggle_desc = 'Only show this layer'
    select_toggle_desc = 'Select bones in this layer'
    objects_set_desc = 'Collection of objects in this set'
    visibility_toggle_desc = 'Show or hide this layer'
    
    if bpy.app.version >= (2,90,0):
        name : StringProperty(default="", description="Limb Name", override={'LIBRARY_OVERRIDABLE'})        
        layers: BoolVectorProperty(size=32, default=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False), subtype='LAYER', override={'LIBRARY_OVERRIDABLE'})      
        objects_set : CollectionProperty(type=ObjectSet, description=objects_set_desc, override=get_override_dict_compat())
        collection : PointerProperty(type=bpy.types.Collection, override={'LIBRARY_OVERRIDABLE'})    
        object_to_add: PointerProperty(type=bpy.types.Object, override={'LIBRARY_OVERRIDABLE'})        
        visibility_toggle: BoolProperty(default=True, update=update_visibility_toggle, override={'LIBRARY_OVERRIDABLE'}, description=visibility_toggle_desc, options={'ANIMATABLE'})       
        exclusive_toggle: BoolProperty(default=False, update=update_layer_set_exclusive, override={'LIBRARY_OVERRIDABLE'}, description=exclusive_toggle_desc)
        select_toggle: BoolProperty(default=True, update=update_layer_select, override={'LIBRARY_OVERRIDABLE'}, description=select_toggle_desc)
        show_objects: BoolProperty(default=True, override={'LIBRARY_OVERRIDABLE'})
        bones: StringProperty(default="[]", override={'LIBRARY_OVERRIDABLE'})
        exclusive_saved_layers: StringProperty(default='[]', override={'LIBRARY_OVERRIDABLE'})
        update_saved_layers: BoolProperty(default=True, override={'LIBRARY_OVERRIDABLE'})
    else:# no overrides before 290
        name : StringProperty(default="", description="Limb Name")       
        layers: BoolVectorProperty(size=32, default=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False), subtype='LAYER')      
        objects_set : CollectionProperty(type=ObjectSet, description=objects_set_desc)
        collection : PointerProperty(type=bpy.types.Collection)   
        object_to_add: PointerProperty(type=bpy.types.Object)  
        visibility_toggle: BoolProperty(default=True, update=update_visibility_toggle, description=visibility_toggle_desc, options={'ANIMATABLE'})       
        exclusive_toggle: BoolProperty(default=False, update=update_layer_set_exclusive, description=exclusive_toggle_desc)    
        select_toggle: BoolProperty(default=True, update=update_layer_select, description=select_toggle_desc)        
        show_objects: BoolProperty(default=True)        
        bones: StringProperty(default="[]")
        exclusive_saved_layers: StringProperty(default='[]')    
        update_saved_layers: BoolProperty(default=True)    


class ARP_UL_layers_sets_list(UIList):
    """
    @classmethod
    def poll(cls, context):
        return
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scn = bpy.context.scene
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, translate=False)# icon='BONE_DATA')
        if scn.arp_layers_show_select:
            row.prop(item, "select_toggle", text="", icon='RESTRICT_SELECT_OFF', emboss=False)
        row.prop(item, 'visibility_toggle', text='', icon='HIDE_OFF' if item.visibility_toggle else 'HIDE_ON', emboss=False)      
        #row.prop(item, "show_toggle", text="", icon='HIDE_OFF', emboss=False)
        #row.prop(item, "hide_toggle", text="", icon='HIDE_ON', emboss=False)   
        if scn.arp_layers_show_exclu:
            icon_name = 'SOLO_ON' if item.exclusive_toggle else 'SOLO_OFF'            
            row.prop(item, "exclusive_toggle", text="", icon=icon_name, emboss=False)#icon='LAYER_ACTIVE'
        
        
    def invoke(self, context, event):
        pass
        
        
class ARP_OT_layers_sets_move(Operator):
    """Move entry"""
    bl_idname = "arp.layers_sets_move"
    bl_label = "Move Layer Set"
    bl_options = {'UNDO'}   
  
    direction: StringProperty(default="UP")
    
    def execute(self, context):        
        try:   
            rig = bpy.context.active_object
            fac = -1
            if self.direction == 'DOWN':
                fac = 1
                
            target_idx = rig.layers_sets_idx + fac
            if target_idx < 0:
                target_idx = len(rig.layers_sets)-1
            if target_idx > len(rig.layers_sets)-1:
                target_idx = 0
                
            #item = rig.layers_sets[rig.layers_sets_idx]
            rig.layers_sets.move(rig.layers_sets_idx, target_idx)
            rig.layers_sets_idx = target_idx
            
        except:
            pass
        return {'FINISHED'}
  

'''
class ARP_PT_layers_sets_edit(Panel):
    bl_label = "Edit Layer Set"
    bl_region_type = 'HEADER'
    bl_space_type = 'VIEW_3D'
    bl_ui_units_x = 14
    
    def draw(self, context):    
        draw_layer_set_edit(self, context) 
'''

class ARP_PT_layers_sets_edit(Operator):
    """Edit a layer set"""
    bl_idname = "arp.layers_sets_edit"
    bl_label = "Edit Layer Set"
    bl_options = {'UNDO'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
   
    def draw(self, context):
        draw_layer_set_edit(self, context)        
    
    def execute(self, context):    
        return {'FINISHED'}    
  
  
class ARP_OT_layers_sets_add(Operator):
    """Add a layer set"""
    bl_idname = "arp.layers_sets_add"
    bl_label = "Add Layer"
    bl_options = {'UNDO'}
    
    def invoke(self, context, event):
        # add new layer set with default settings
        _add_layer_set(self)
        
        # Open dialog
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
   
    def draw(self, context):
        draw_layer_set_edit(self, context)        
    
    def execute(self, context):    
        return {'FINISHED'}    
        
        
class ARP_OT_layers_sets_remove(Operator):
    """Remove a layer set"""
    bl_idname = "arp.layers_sets_remove"
    bl_label = "Remove Layer"
    bl_options = {'UNDO'}

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:       
            _remove_layer_set(self)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'} 
        
        
class ARP_OT_childof_keyer(Operator):
    """Keyframe the influence of all Child Of constraints of this bone"""
    
    bl_idname = "arp.childof_keyer"
    bl_label = "Child Of Keyframer"
    bl_options = {'UNDO'}    
  
    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')
 

    def execute(self, context):
        
        if len(bpy.context.selected_pose_bones) == 0:
            self.report({'ERROR'}, "A bone must be selected")
            return {'FINISHED'}
        
        for pb in bpy.context.selected_pose_bones:
            try:            
                _childof_keyer(pb)
            finally:
                pass
            
        return {'FINISHED'}


class ARP_OT_childof_switcher(Operator):
    """Switch and snap to the selected Child Of constraint (parent space)"""
    
    bl_idname = "arp.childof_switcher"
    bl_label = "Switch and snap Child Of constraints"
    bl_options = {'UNDO'}
    
    cns_items = []     
    
    def get_cns_items(self, context):
        return ARP_OT_childof_switcher.cns_items        

    child_of_cns: EnumProperty(items=get_cns_items, default=None)  
    bake_type: EnumProperty(items=(('STATIC', 'Static', 'Switch and snap only for the current frame'), ('ANIM', 'Anim', 'Switch and snap over a specified frame range')), default='STATIC')
    fstart: IntProperty(default=0)
    fend: IntProperty(default=10)
    # NID
    only_at_keyframe: BoolProperty(default=False)
    
    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')        
       

    def invoke(self, context, event):   
        ARP_OT_childof_switcher.cns_items = []       
        active_bone = None
        try:
            active_bone = bpy.context.selected_pose_bones[0]
        except:
            pass
            
        if active_bone == None:
            self.report({'ERROR'}, "A bone must be selected")
            return {'FINISHED'}            
        
        active_cns = None
        
        # collect current ChildOf constraints
        if len(active_bone.constraints):
            # get active one first
            for cns in active_bone.constraints:                
                if cns.type == 'CHILD_OF':                    
                    if cns.influence > 0:
                        active_cns = cns
                        separator = ''
                        if cns.subtarget != '':
                            separator = ': '
                        ARP_OT_childof_switcher.cns_items.append((cns.name, cns.target.name + separator + cns.subtarget, ''))
        
            # others
            for cns in active_bone.constraints:                
                if cns.type == 'CHILD_OF':                    
                    if cns != active_cns or active_cns == None:     
                        separator = ''
                        if cns.subtarget != '':
                            separator = ': '
                        ARP_OT_childof_switcher.cns_items.append((cns.name, cns.target.name + separator + cns.subtarget, ''))
                  
        ARP_OT_childof_switcher.cns_items.append(('NONE', 'None', 'None'))
        
        if active_cns != None:
            self.child_of_cns = active_cns.name
    
        if len(ARP_OT_childof_switcher.cns_items) == 1:
            self.report({'ERROR'}, "No ChildOf constraint found on this bone")
            return {'FINISHED'}
            
        # set frame start and endswith
        if context.active_object.animation_data.action:
            act = context.active_object.animation_data.action
            self.fstart, self.fend = int(act.frame_range[0]), int(act.frame_range[1])            
            
            
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
        
    def draw(self, context):
        layout = self.layout
        layout.label(text='Active Parent:           '+self.cns_items[0][1])
        layout.prop(self, 'child_of_cns', text='Snap To')
        
        layout.prop(self, 'bake_type', expand=True)
        
        if self.bake_type == 'ANIM':
            row = layout.column().row(align=True)
            row.prop(self, 'fstart', text='Frame Start')
            row.prop(self, 'fend', text='Frame End')
            row = layout.row()    
            row.prop(self, 'only_at_keyframe', text='Only at Keyframe')
        

    def execute(self, context):
    
        try:      
            if self.bake_type == 'STATIC':
                _childof_switcher(self)
            elif self.bake_type == 'ANIM':
                # set autokey on
                autokey_state = context.scene.tool_settings.use_keyframe_insert_auto
                context.scene.tool_settings.use_keyframe_insert_auto = True
                
                context.scene.frame_set(self.fstart)
                
                pb = context.selected_pose_bones[0]               
                base_transform = pb.location.copy(), pb.rotation_euler.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()
                
                cns_dict = {}
                
                for cns in pb.constraints:
                    if cns.type == 'CHILD_OF':
                        cns_dict[cns.name] = cns.influence

                # NID, this branch is added by NID
                if self.only_at_keyframe is True:

                    # prepass, 
                    # key child of cns influences at every keyframe 
                    # if no prepass, influences might change unexpectedly after jump to the next keyframe
                    #
                    # for example: location keyframe at 0, 10, 20, but child of cns influences are not keyed
                    # influences A == 1, B == 0
                    # if we switch child of at 0, then jump to 10, then A == 0, B == 1
                    # but, at that time, location is not recalculated, causing final transform to difer from original
                    #

                    context.scene.frame_set(self.fstart-1)
                    prev_frame = self.fstart-1

                    for i in range(self.fstart, self.fend+1):

                        bpy.ops.screen.keyframe_jump(next=True)

                        if context.scene.frame_current > self.fend or context.scene.frame_current < self.fstart or prev_frame == context.scene.frame_current:
                            break

                        prev_frame = context.scene.frame_current

                        bpy.ops.arp.childof_keyer()

                    # normal pass

                    context.scene.frame_set(self.fstart-1)
                    prev_frame = self.fstart-1
                    
                    for i in range(self.fstart, self.fend+1):

                        bpy.ops.screen.keyframe_jump(next=True)

                        if context.scene.frame_current > self.fend or context.scene.frame_current < self.fstart or prev_frame == context.scene.frame_current:
                            break

                        prev_frame = context.scene.frame_current

                        # and constraints
                        for cns_name in cns_dict:
                            pb.constraints.get(cns_name).influence = cns_dict[cns_name]
                        
                        # reset the initial transforms          
                        pb.location, pb.rotation_euler, pb.rotation_quaternion, pb.scale = base_transform
                        
                        _childof_switcher(self)


                # NID, this branch is original
                else:

                    for i in range(self.fstart, self.fend+1):
                        print("SNAP FRAME", i)                              
                        context.scene.frame_set(i)
                        
                        # and constraints
                        for cns_name in cns_dict:
                            pb.constraints.get(cns_name).influence = cns_dict[cns_name]
                        
                        # reset the initial transforms          
                        pb.location, pb.rotation_euler, pb.rotation_quaternion, pb.scale = base_transform
                        
                        _childof_switcher(self)
                   
                # restore autokey state
                context.scene.tool_settings.use_keyframe_insert_auto = autokey_state
                    
        finally:
            pass
            
        return {'FINISHED'}
        
        
class ARP_OT_rotation_mode_convert(Operator):
    """Convert bones to euler or quaternion rotation"""
    
    bl_idname = "arp.convert_rot_mode"
    bl_label = "Convert Rotation Mode"
    bl_options = {'UNDO'}        
   
    mode: StringProperty(default="TO_QUAT")
    frame_start: IntProperty(default=0, description="Start frame")
    frame_end: IntProperty(default=10, description="End frame")
    one_key_per_frame: BoolProperty(default=False, description="Insert one keyframe per frame if enabled, otherwise only existing keyframes within the given frame range will be keyframed", name="Key All Frames")
    #key_rot_mode: BoolProperty(default=False, description="Keyframe the rotation mode if enabled. Useful when mixing multiple rotation modes in the same action", name="Key Rotation Mode")   
    selected_only: BoolProperty(default=True, description="Only convert selected bones rotation if enabled, otherwise all animated bones", name='Selected Bones Only')
    euler_order: EnumProperty(items=(('XYZ', 'XYZ', 'XYZ'), ('XZY', 'XZY', 'XZY'), ('YXZ', 'YXZ', 'YXZ'), ('YZX', 'YZX', 'YZX'), ('ZXY', 'ZXY', 'ZXY'), ('ZYX', 'ZYX', 'ZYX')), description='Euler order', name='Euler Order')
    text_title = ''
    
    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')        
        

    def invoke(self, context, event):        
        action = context.active_object.animation_data.action
        if action == None:
            self.report({'ERROR'}, "This only works for animated bones")
            return {'FINISHED'}
            
        self.frame_start, self.frame_end = int(action.frame_range[0]), int(action.frame_range[1])
        
        self.text_title = 'Quaternions' if self.mode == 'rotation_quaternion' else 'Euler'
    
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        
        
    def draw(self, context):
        layout = self.layout
        layout.label(text='To '+self.text_title)
        layout.prop(self, 'selected_only')
        layout.prop(self, 'one_key_per_frame')   
        if self.mode == 'rotation_euler':
            layout.prop(self, 'euler_order')
        #layout.prop(self, 'key_rot_mode')# not supported for now, rotation conversion update issues
        row = layout.column().row(align=True)
        row.prop(self, 'frame_start', text='Frame Start')
        row.prop(self, 'frame_end', text='Frame End')
        layout.separator()
        

    def execute(self, context):
    
        try:
            convert_rot_mode(self)

        finally:
            pass
            
        return {'FINISHED'}
        
        
class ARP_OT_switch_snap_root_tip_all(Operator):
    """Switch and snap all fingers IK Root-Tip"""

    bl_idname = "arp.switch_snap_root_tip_all"
    bl_label = "switch_snap_root_tip_all"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    finger_root_name: StringProperty(name="", default="")
    state: StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            for fing_type in fingers_start:
                finger_root_name = fing_type+"1_base"+self.side
                finger_root = get_pose_bone(finger_root_name)

                if self.state == "ROOT":
                    root_to_tip_finger(finger_root, self.side)
                elif self.state == "TIP":
                    tip_to_root_finger(finger_root, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_switch_all_fingers(Operator):
    """Set all fingers to IK or FK"""

    bl_idname = "arp.switch_all_fingers"
    bl_label = "switch_all_fingers"
    bl_options = {'UNDO'}

    state: StringProperty(default="")
    side: StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        try:
            for fing_type in fingers_start:
                finger_root_name = fing_type+"1_base"+self.side
                finger_root = get_pose_bone(finger_root_name)

                if finger_root:
                    if "ik_fk_switch" in finger_root.keys():
                        if self.state == "IK":
                            ik_to_fk_finger(finger_root, self.side)

                        elif self.state == "FK":
                            fk_to_ik_finger(finger_root, self.side)

        finally:
            pass

        return {'FINISHED'}


class ARP_OT_free_parent_ik_fingers(Operator):
    """Enable or disable the Child Of constraints of all fingers IK target"""

    bl_idname = "arp.free_lock_ik_fingers"
    bl_label = "free_lock_ik_fingers"
    bl_options = {'UNDO'}

    side: StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        try:
            for fing_type in fingers_start:
                ik_target_name = fing_type+"_ik"+self.side
                ik_target2_name = fing_type+"_ik2"+self.side
                ik_target_pb = get_pose_bone(ik_target_name)
                ik_target2_pb = get_pose_bone(ik_target2_name)

                for b in [ik_target_pb, ik_target2_pb]:
                    if b == None:
                        continue
                    if len(b.constraints) == 0:
                        continue

                    hand_cns = b.constraints.get("Child Of_hand")
                    if hand_cns:
                        if hand_cns.influence > 0.5:# set free
                            mat = b.matrix.copy()
                            hand_cns.influence = 0.0
                            b.matrix = mat

                        else:# parent
                            mat = b.matrix.copy()
                            bone_parent = get_pose_bone(hand_cns.subtarget)
                            hand_cns.influence = 1.0
                            b.matrix = bone_parent.matrix_channel.inverted() @ mat


        finally:
            pass

        return {'FINISHED'}


class ARP_OT_toggle_layers(Operator):
    """Toggle controller layers visibility"""

    bl_idname = "arp.toggle_layers"
    bl_label = "toggle_layers"
    bl_options = {'UNDO'}

    layer_idx : IntProperty(name="Layer Index", default=0)

    @classmethod
    def poll(cls, context):
        if context.active_object != None:
            if context.active_object.type == "ARMATURE":
                return True

    def execute(self, context):
        try:
            arm = bpy.context.active_object
            arm.data.layers[self.layer_idx] = not arm.data.layers[self.layer_idx]
        finally:
            pass
            
        return {'FINISHED'}


class ARP_OT_snap_head(Operator):
    """Switch the Head Lock and snap the head rotation"""

    bl_idname = "arp.snap_head"
    bl_label = "snap_head"
    bl_options = {'UNDO'}

    side : StringProperty(name="Side", default="")

    @classmethod
    def poll(cls, context):
        if context.object != None:
            if is_object_arp(context.object):
                return True

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)
            _snap_head(self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class ARP_OT_reset_script(Operator):
    """Reset character controllers to rest position"""

    bl_idname = "arp.reset_pose"
    bl_label = "reset_pose"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object != None:
            if is_object_arp(context.object):
                return True

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            reset_all_controllers.reset_all_controllers()

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_set_picker_camera_func(Operator):

    """Display the bone picker of the selected character in this active view"""

    bl_idname = "id.set_picker_camera_func"
    bl_label = "set_picker_camera_func"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object != None:
            if is_object_arp(context.object):
                return True

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            _set_picker_camera(self)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class ARP_OT_toggle_multi(Operator):
    """Toggle multi-limb visibility"""

    bl_idname = "id.toggle_multi"
    bl_label = "toggle_multi"
    bl_options = {'UNDO'}

    limb : StringProperty(name="Limb")
    id : StringProperty(name="Id")
    key : StringProperty(name="key")
    """
    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')
    """

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            _toggle_multi(self.limb, self.id, self.key)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class ARP_OT_snap_pin(Operator):
    """Switch and snap the pinning bone"""

    bl_idname = "pose.arp_snap_pin"
    bl_label = "Arp Switch and Snap Pin"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    type : StringProperty(name="bone side")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            if is_selected(fk_arm, bname) or is_selected(ik_arm, bname):
                self.type = "arm"
            elif is_selected(fk_leg, bname) or is_selected(ik_leg, bname):
                self.type = "leg"

            _switch_snap_pin(self.side, self.type)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_arp_snap_pole(Operator):
    """Switch and snap the IK pole parent"""

    bl_idname = "pose.arp_snap_pole"
    bl_label = "Arp Snap FK arm to IK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    bone_type : StringProperty(name="arm or leg")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            if is_selected(fk_arm, bname) or is_selected(ik_arm, bname):
                self.bone_type = "arms"
            elif is_selected(fk_leg, bname) or is_selected(ik_leg, bname):
                self.bone_type = "leg"

            _arp_snap_pole(context.active_object, self.side, self.bone_type)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_arm_bake_fk_to_ik(Operator):
    """Snaps and bake an FK to an IK arm over a specified frame range"""

    bl_idname = "pose.arp_bake_arm_fk_to_ik"
    bl_label = "Snap an FK to IK arm over a specified frame range"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    frame_start : IntProperty(name="Frame start", default=0)
    frame_end : IntProperty(name="Frame end", default=10)
    get_sel_side: BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')


    def draw(self, context):
        layout = self.layout
        row = layout.column().row(align=True)
        row.prop(self, 'frame_start', text='Frame Start')
        row.prop(self, 'frame_end', text='Frame End')
        layout.separator()


    def invoke(self, context, event):
        self.get_sel_side = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)


    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        scn = context.scene
        
        # save current autokey state
        auto_key_state = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        # set auto key to True
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
        # save current frame
        cur_frame = scn.frame_current

        try:
            if self.get_sel_side:
                bname = get_selected_pbone_name()
                self.side = get_bone_side(bname)

            bake_fk_to_ik_arm(self)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
            # restore autokey state
            scn.tool_settings.use_keyframe_insert_auto = auto_key_state
            # restore frame
            scn.frame_set(cur_frame)

        return {'FINISHED'}


class ARP_OT_arm_fk_to_ik(Operator):
    """Snaps an FK arm to an IK arm"""

    bl_idname = "pose.arp_arm_fk_to_ik_"
    bl_label = "Arp Snap FK arm to IK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            fk_to_ik_arm(context.active_object, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_arm_bake_ik_to_fk(Operator):
    """Snaps and bake an IK to an FK arm over a specified frame range"""

    bl_idname = "pose.arp_bake_arm_ik_to_fk"
    bl_label = "Snap an IK to FK arm over a specified frame range"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side", default='')
    frame_start : IntProperty(name="Frame start", default=0)
    frame_end : IntProperty(name="Frame end", default=10)
    get_sel_side: BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def draw(self, context):
        layout = self.layout
        row = layout.column().row(align=True)
        row.prop(self, 'frame_start', text='Frame Start')
        row.prop(self, 'frame_end', text='Frame End')
        layout.separator()

    def invoke(self, context, event):
        self.get_sel_side = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        scn = context.scene
        
        # save current autokey state
        auto_key_state = scn.tool_settings.use_keyframe_insert_auto
        # set auto key to True
        scn.tool_settings.use_keyframe_insert_auto = True
        # save current frame
        cur_frame = scn.frame_current

        try:
            if self.get_sel_side:
                bname = get_selected_pbone_name()
                self.side = get_bone_side(bname)

            bake_ik_to_fk_arm(self)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
            # restore autokey state
            scn.tool_settings.use_keyframe_insert_auto = auto_key_state
            # restore frame
            scn.frame_set(cur_frame)

        return {'FINISHED'}


class ARP_OT_arm_ik_to_fk(Operator):
    """Snaps an IK arm to an FK arm"""

    bl_idname = "pose.arp_arm_ik_to_fk_"
    bl_label = "Arp Snap IK arm to FK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            ik_to_fk_arm(context.active_object, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class ARP_OT_switch_snap_root_tip(Operator):
    """Switch and snap fingers IK Root-Tip"""

    bl_idname = "arp.switch_snap_root_tip"
    bl_label = "switch_snap_root_tip"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    finger_root_name: StringProperty(name="", default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            finger_type = None
            for type in fingers_type_list:
                if type in bname:
                    finger_type = type
                    break

            self.finger_root_name = "c_"+finger_type+"1_base"+self.side
            root_finger = get_pose_bone(self.finger_root_name)

            if root_finger['ik_tip'] < 0.5:
                tip_to_root_finger(root_finger, self.side)
            else:
                root_to_tip_finger(root_finger, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_switch_snap(Operator):
    """Switch and snap the IK-FK"""

    bl_idname = "pose.arp_switch_snap"
    bl_label = "Arp Switch and Snap IK FK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    type : StringProperty(name="type", default="")
    finger_root_name: StringProperty(name="", default="")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            if is_selected(fk_leg, bname) or is_selected(ik_leg, bname):
                self.type = "LEG"
            elif is_selected(fk_arm, bname) or is_selected(ik_arm, bname):
                self.type = "ARM"
            elif is_selected(fingers_start, bname, startswith=True):
                self.type = "FINGER"

                finger_type = None
                for type in fingers_type_list:
                    if type in bname:
                        finger_type = type
                        break

                self.finger_root_name = "c_"+finger_type+"1_base"+self.side

            if self.type == "ARM":
                hand_ik = get_pose_bone(ik_arm[2] + self.side)
                if hand_ik['ik_fk_switch'] < 0.5:
                    fk_to_ik_arm(context.active_object, self.side)
                else:
                    ik_to_fk_arm(context.active_object, self.side)

            elif self.type == "LEG":
                foot_ik = get_pose_bone(ik_leg[2] + self.side)
                if foot_ik['ik_fk_switch'] < 0.5:
                    fk_to_ik_leg(context.active_object, self.side)
                else:
                    ik_to_fk_leg(context.active_object, self.side)

            elif self.type == "FINGER":
                root_finger = get_pose_bone(self.finger_root_name)
                if root_finger['ik_fk_switch'] < 0.5:
                    fk_to_ik_finger(root_finger, self.side)
                else:
                    ik_to_fk_finger(root_finger, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}


class ARP_OT_leg_bake_fk_to_ik(Operator):
    """Snaps and bake an FK leg to an IK leg over a specified frame range"""

    bl_idname = "pose.arp_bake_leg_fk_to_ik"
    bl_label = "Snap an FK to IK leg over a specified frame range"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    get_sel_side: BoolProperty(default=True)
    frame_start : IntProperty(name="Frame start", default=0)
    frame_end : IntProperty(name="Frame end", default=10)
    temp_frame_start = 0
    temp_frame_end = 1

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')


    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'frame_start', text='Frame Start')
        row.prop(self, 'frame_end', text='Frame End')

        layout.separator()


    def invoke(self, context, event):
        self.get_sel_side = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)


    def set_range():
        ARP_OT_leg_bake_fk_to_ik.frame_start = ARP_OT_leg_bake_fk_to_ik.temp_frame_start
        ARP_OT_leg_bake_fk_to_ik.frame_end = ARP_OT_leg_bake_fk_to_ik.temp_frame_end


    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        scn = context.scene
        
        # save current autokey state
        auto_key_state = scn.tool_settings.use_keyframe_insert_auto
        # set auto key to True
        scn.tool_settings.use_keyframe_insert_auto = True
        # save current frame
        cur_frame = scn.frame_current
        
        try:
            if self.get_sel_side:
                bname = get_selected_pbone_name()
                self.side = get_bone_side(bname)

            bake_fk_to_ik_leg(self)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
            # restore autokey state
            scn.tool_settings.use_keyframe_insert_auto = auto_key_state
            # restore frame
            scn.frame_set(cur_frame)

        return {'FINISHED'}


class ARP_OT_leg_fk_to_ik(Operator):
    """Snaps an FK leg to an IK leg"""

    bl_idname = "pose.arp_leg_fk_to_ik_"
    bl_label = "Arp Snap FK leg to IK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False

        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            fk_to_ik_leg(context.active_object, self.side)

        finally:
            context.preferences.edit.use_global_undo = use_global_undo
        return {'FINISHED'}


class ARP_OT_leg_bake_ik_to_fk(Operator):
    """Snaps and bake an IK leg to an FK leg over a specified frame range"""

    bl_idname = "pose.arp_bake_leg_ik_to_fk"
    bl_label = "Snap an IK to FK leg over a specified frame range"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")
    get_sel_side: BoolProperty(default=True)
    frame_start : IntProperty(name="Frame start", default=0)
    frame_end : IntProperty(name="Frame end", default=10)

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def draw(self, context):
        layout = self.layout
        row = layout.column().row(align=True)
        row.prop(self, 'frame_start', text='Frame Start')
        row.prop(self, 'frame_end', text='Frame End')
        layout.separator()

    def invoke(self, context, event):
        self.get_sel_side = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        scn = context.scene
        
        # save current autokey state
        auto_key_state = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        # set auto key to True
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
        # save current frame
        cur_frame = scn.frame_current

        try:
            if self.get_sel_side:
                bname = get_selected_pbone_name()
                self.side = get_bone_side(bname)

            bake_ik_to_fk_leg(self)
            
        finally:
            context.preferences.edit.use_global_undo = use_global_undo
            # restore autokey state
            scn.tool_settings.use_keyframe_insert_auto = auto_key_state
            # restore frame
            scn.frame_set(cur_frame)

        return {'FINISHED'}


class ARP_OT_leg_ik_to_fk(Operator):
    """Snaps an IK leg to an FK leg"""

    bl_idname = "pose.arp_leg_ik_to_fk_"
    bl_label = "Arp Snap IK leg to FK"
    bl_options = {'UNDO'}

    side : StringProperty(name="bone side")

    @classmethod
    def poll(cls, context):
        return (context.active_object != None and context.mode == 'POSE')

    def execute(self, context):
        use_global_undo = context.preferences.edit.use_global_undo
        context.preferences.edit.use_global_undo = False
        try:
            bname = get_selected_pbone_name()
            self.side = get_bone_side(bname)

            ik_to_fk_leg(context.active_object, self.side)
        finally:
            context.preferences.edit.use_global_undo = use_global_undo

        return {'FINISHED'}



###FUNCTIONS ##############################################
# Functions Utils
def _rotate_point(point_loc, angle, axis, origin):
    # rotate the point_loc (vector 3) around the "axis" (vector 3) 
    # for the angle value (radians)
    # around the origin (vector 3)
    rot_mat = Matrix.Rotation(angle, 4, axis.normalized())
    loc = point_loc.copy()
    loc = loc - origin
    point_mat = Matrix.Translation(loc).to_4x4()
    point_mat_rotated = rot_mat @ point_mat
    loc, rot, scale = point_mat_rotated.decompose()
    loc = loc + origin
    return loc
    
    
def compensate_ik_pole_position(fk1, fk2, ik1, ik2, pole):
    angle_offset = get_ik_fk_angle_offset(fk1, fk2, ik1, ik2, pole)
    i = 0
    dir = 1
    while (angle_offset > 0.005 and i < 6):
        print('Correcting IK pole snap', i)
        axis = (ik2.tail-ik1.head)
        origin = (fk2.tail + fk1.head) / 2
        pole_rotated = _rotate_point(pole.head, angle_offset*dir, axis, origin)        
        snap_pos_matrix(pole, Matrix.Translation(pole_rotated))
        new_angle = get_ik_fk_angle_offset(fk1, fk2, ik1, ik2, pole)
        if new_angle > angle_offset:# wrong direction!            
            dir *= -1
        angle_offset = new_angle
        i += 1
    
    
def keyframe_pb_transforms(pb, loc=True, rot=True, scale=True, keyf_locked=False):
    if loc:
        for i, j in enumerate(pb.lock_location):
            if not j or keyf_locked:
                pb.keyframe_insert(data_path='location', index=i)  
    if rot:
        rot_dp = 'rotation_quaternion' if pb.rotation_mode == 'QUATERNION' else 'rotation_euler' 
        rot_locks = [i for i in pb.lock_rotation]
        if rot_dp == 'rotation_quaternion':
            rot_locks.insert(0, pb.lock_rotation_w)
        for i, j in enumerate(rot_locks):
            if not j or keyf_locked:
                pb.keyframe_insert(data_path=rot_dp, index=i)
        
    if scale:
        for i, j in enumerate(pb.lock_scale):
            if not j or keyf_locked:
                pb.keyframe_insert(data_path='scale', index=i)

    
                    
def get_pinned_props_list(rig):
    current_pinned_string = rig.data["arp_pinned_props"]
    return current_pinned_string.split(',')

                
def set_prop_setting(node, prop_name, setting, value):
    if bpy.app.version >= (3,0,0):
        ui_data = node.id_properties_ui(prop_name)
        if setting == 'default':
            ui_data.update(default=value)
        elif setting == 'min':
            print("node", node, "prop name", prop_name, setting, value)
            ui_data.update(min=value)
        elif setting == 'max':
            ui_data.update(max=value)     
        elif setting == 'soft_min':
            ui_data.update(soft_min=value)
        elif setting == 'soft_max':
            ui_data.update(soft_max=value)
        elif setting == 'description':
            ui_data.update(description=value)
            
    else:
        if not "_RNA_UI" in node.keys():
            node["_RNA_UI"] = {}   
        node['_RNA_UI'][prop_name][setting] = value
        

def create_custom_prop(node=None, prop_name="", prop_val=1.0, prop_min=0.0, prop_max=1.0, prop_description="", soft_min=None, soft_max=None, default=None):
    if soft_min == None:
        soft_min = prop_min
    if soft_max == None:
        soft_max = prop_max
    
    if bpy.app.version < (3,0,0):
        if not "_RNA_UI" in node.keys():
            node["_RNA_UI"] = {}    
    
    node[prop_name] = prop_val    
    
    if default == None:
        default = prop_val
    
    if bpy.app.version < (3,0,0):
        node["_RNA_UI"][prop_name] = {'use_soft_limits':True, 'min': prop_min, 'max': prop_max, 'description': prop_description, 'soft_min':soft_min, 'soft_max':soft_max, 'default':default}
    else:     
        if type(prop_val) != str:#string props have no min, max, soft min, soft max
            set_prop_setting(node, prop_name, 'min', prop_min)
            set_prop_setting(node, prop_name, 'max', prop_max)
            set_prop_setting(node, prop_name, 'soft_min', soft_min)
            set_prop_setting(node, prop_name, 'soft_max', soft_max)
        
        set_prop_setting(node, prop_name, 'description', prop_description)        
        set_prop_setting(node, prop_name, 'default', default)
        
    # set as overridable
    node.property_overridable_library_set('["'+prop_name+'"]', True)
    

def get_object(name):
    return bpy.data.objects.get(name)
    
        
def search_layer_collection(layerColl, collName):
    # Recursivly transverse layer_collection for a particular name
    found = None
    if (layerColl.name == collName):
        return layerColl
    for layer in layerColl.children:
        found = search_layer_collection(layer, collName)
        if found:
            return found
            
            
def hide_object(obj_to_set):
    try:# object may not be in current view layer
        obj_to_set.hide_set(True)
        obj_to_set.hide_viewport = True
    except:
        pass
        
        
def unhide_object(obj_to_set):
    # we can only operate on the object if it's in the active view layer...
    try:
        obj_to_set.hide_set(False)
        obj_to_set.hide_viewport = False
    except:
        print("Could not reveal object:", obj_to_set.name)
        
        
def set_active_object(object_name):
     bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
     bpy.data.objects[object_name].select_set(state=1)

     
def is_object_arp(object):
    if object.type == 'ARMATURE':
        if object.pose.bones.get('c_pos') != None:
            return True
            

def get_selected_pbone_name():
    try:
        return bpy.context.selected_pose_bones[0].name#bpy.context.active_pose_bone.name
    except:
        return
        

def get_bone_side(bone_name):
    side = ""
    if not "_dupli_" in bone_name:
        side = bone_name[-2:]
    else:
        side = bone_name[-12:]
    return side


# Functions Operators
def _childof_keyer(pb):  
    for cns in pb.constraints:
        if cns.type == 'CHILD_OF':
            cns.keyframe_insert(data_path='influence')


def _childof_switcher(self):
    rig = bpy.context.active_object
    pb = bpy.context.selected_pose_bones[0]
    mat_prev = pb.matrix.copy()
    scn = bpy.context.scene
    
    def disable_cns(cns):
        if cns.influence != 0.0:
            
            parent_type = 'bone' if cns.subtarget else 'object'
            parent_name = cns.subtarget if parent_type == 'bone' else cns.target.name
            
            # set influence
            cns.influence = 0.0
            
            # snap
            if parent_type == 'bone':
                bone_parent = get_pose_bone(parent_name)             
                pb.matrix = mat_prev                
                
            elif parent_type == 'object':
                obj_par = get_object(parent_name)
                pb.matrix = cns.inverse_matrix.inverted() @ obj_par.matrix_world.inverted() @ pb.matrix
                
            # auto keyframe
            if scn.tool_settings.use_keyframe_insert_auto:
                keyframe_pb_transforms(pb)
                cns.keyframe_insert(data_path='influence')
                
            
    def enable_cns(cns):
        debug = False
        
        if cns.influence != 1.0:
            if debug:
                print("enable constraint:", cns.name)
            parent_type = 'bone' if cns.subtarget else 'object'
            parent_name = cns.subtarget if parent_type == 'bone' else cns.target.name            
            
            if debug:
                print("MAT INIT")
                mat_init = pb.matrix.copy()                
                print(mat_init)
                
            # set influence
            cns.influence = 1.0
         
            update_transform() 
            
            # snap
            if parent_type == 'bone':
                bone_parent = get_pose_bone(parent_name)
                pb.matrix = cns.inverse_matrix.inverted() @ bone_parent.matrix.inverted() @ mat_prev
                
                update_transform()
                
                if debug:
                    print("MAT POST")
                    print(pb.matrix)          
                
            elif parent_type == 'object':
                if debug:
                    print("  object type")
                obj_par = get_object(parent_name)
                pb.matrix = cns.inverse_matrix.inverted() @ obj_par.matrix_world.inverted() @ mat_prev#pb.matrix
                
            # auto keyframe
            if scn.tool_settings.use_keyframe_insert_auto:
                keyframe_pb_transforms(pb)
                cns.keyframe_insert(data_path='influence')
                
    
    for cns in pb.constraints: 
        if cns.type != 'CHILD_OF':
            continue
        if cns.name != self.child_of_cns:            
            disable_cns(cns)  

    for cns in pb.constraints:
        if cns.type != 'CHILD_OF':
            continue
        if cns.name == self.child_of_cns:
            enable_cns(cns)
    

def _export_layers_sets(self):
    scn = bpy.context.scene
    rig = bpy.context.active_object
    
    filepath = self.filepath
    
    if not filepath.endswith(".py"):
        filepath += ".py"

    file = open(filepath, "w", encoding="utf8", newline="\n")
    layers_set_dict = {}
    
    """
    name: string
    layers: Bool list
    objects_set: CollectionProp[object_item(pointer object)]
    collection: Pointer(Collection)    
    bones: String
    """
    
    # fetch data
    for layerset in rig.layers_sets:
        layer_dict = {}
        
        # name
        layer_dict['name'] = layerset.name
        
        # layers
        layer_dict['layers'] = [i for i in layerset.layers]
        
        # objects
        objects_names = []
        for obj_i in layerset.objects_set:
            obj = obj_i.object_item
            if obj != None:
                objects_names.append(obj.name)
            
        layer_dict['objects_set'] = objects_names
        
        # collection
        collec_name = ''
        if layerset.collection != None:
            collec_name = layerset.collection.name
            
        layer_dict['collection'] = collec_name
        
        # bones
        layer_dict['bones'] = layerset.bones        
        
        # set dict    
        layers_set_dict[layerset.name] = layer_dict
    
    # write file
    file.write(str(layers_set_dict))

    # close file
    file.close()   
    
    
def _import_layers_sets(self):
    filepath = self.filepath
    scn = bpy.context.scene
    rig = bpy.context.active_object   
    
    # read file
    file = open(filepath, 'rU')
    file_lines = file.readlines()
    dict_str = str(file_lines[0])
    file.close()
    
    # import data
    layers_set_dict = ast.literal_eval(dict_str)     
    
    for layer_name in layers_set_dict:
      
        layerset = rig.layers_sets.add()
        
        # name
        layerset.name = layer_name
        
        # layers
        layerset.layers = layers_set_dict[layer_name]['layers']
        
        # objects
        objects_set = layers_set_dict[layer_name]['objects_set']
        if len(objects_set):
            for name in objects_set:
                if get_object(name):
                    obj_i = layerset.objects_set.add()
                    obj_i.object_item = get_object(name)
                    
        # collection
        collec_name = layers_set_dict[layer_name]['collection']
        if collec_name != '':
            collec = bpy.data.collections.get(collec_name)
            if collec:
                layerset.collection = collec
                
        # bones
        layerset.bones = layers_set_dict[layer_name]['bones']
            

def draw_layer_set_edit(self, context):
    rig = context.active_object 
    
    if len(rig.layers_sets) == 0:
        return
        
    current_set = rig.layers_sets[rig.layers_sets_idx]
    
    layout = self.layout
    
    # layers
    layout.label(text='Layers:')   
    col = layout.column(align=True)   
    col.prop(current_set, "layers", text="")
   
    layout.separator()  
    
    # bones
    #print(current_set.bones)
    len_bones = str(len(ast.literal_eval(current_set.bones)))
    col = layout.column()
    row = col.row(align=True)
    row.operator("arp.layers_sets_add_bones", text="Add Selected Bones ("+len_bones+")")
    row.operator("arp.layers_sets_remove_bones", text="", icon="PANEL_CLOSE")
    
    # collection
    col = layout.column()
    col.prop(current_set, "collection", text="Collection")    
    
    # objects
    row = col.row(align=True)
    row.prop(current_set, "object_to_add", text="Add Object")
    row.operator("arp.layers_sets_add_object", text="", icon="ADD")
   
    layout.operator("arp.layers_sets_clear_objects", text="Remove All Objects")
    layout.prop(current_set, "show_objects", text="", icon="HIDE_OFF")    
    
    if current_set.show_objects:
        col = layout.column(align=True)
        if len(current_set.objects_set):
            for obji in current_set.objects_set:
                col.label(text=obji.object_item.name)
        else:
            col.label(text="No objects in this set")
    
    layout.separator()

    
def set_layer_vis(self, state):
    #print("SET LAYER VIZ")
    rig = bpy.context.active_object
    scn = bpy.context.scene
    
    if rig.type != 'ARMATURE':
        return
    
    # set armature layers visibility   
    for i, lay in enumerate(self.layers):
        if lay:
            rig.data.layers[i] = state
            
    # set bones visibility
    bones_names = ast.literal_eval(self.bones)
    
    for bname in bones_names:
        if bpy.context.mode == "EDIT_ARMATURE":
            b = get_edit_bone(bname)
            if b:
                b.hide = not state
            
        elif bpy.context.mode == "POSE" or bpy.context.mode == "OBJECT":
            b = get_data_bone(bname)
            if b:
                b.hide = not state
            
    
    # set collection visibility
    if self.collection != None: 
        # hide at collection level
        self.collection.hide_viewport = not state
        
        if scn.arp_layers_set_render:
            self.collection.hide_render = not state
                
        # hide at view layer level
        try:
            layer_col = search_layer_collection(bpy.context.view_layer.layer_collection, self.collection.name)              
            layer_col.hide_viewport = not state
            
            if scn.arp_layers_set_render:
                layer_col.hide_render = not state
            
        except:
            pass
            
    # set objects visibility
    for obji in self.objects_set:
        obj = obji.object_item
        if state == True:
            unhide_object(obj)
            
            if scn.arp_layers_set_render:
                obj.hide_render = False
        else:
            hide_object(obj)
            
            if scn.arp_layers_set_render:
                obj.hide_render = True
             


def tip_to_root_finger(root_finger, side):
    scn = bpy.context.scene

    finger_type = None
    rig = bpy.context.active_object

    for i in fingers_type_list:
        if i in root_finger.name:
            finger_type = i
            break

    ik_target_name = ""
    ik_tip = root_finger["ik_tip"]
    ik_target_name = "c_"+finger_type+"_ik"+side
    ik_target2_name = "c_"+finger_type+"_ik2"+side
    ik_target = get_pose_bone(ik_target_name)
    ik_target2 = get_pose_bone(ik_target2_name)

    if ik_target == None or ik_target2 == None:
        print("Finger IK target not found:", ik_target_name)
        return

    ik_pole_name = "c_"+finger_type+"_pole"+side
    ik_pole = get_pose_bone(ik_pole_name)
    if ik_pole == None:
        print("Finger IK pole not found:", ik_pole_name)
        return

    # Snap IK target
        # constraint support
    constraint, bparent_name, parent_type, valid_constraint = get_active_child_of_cns(ik_target)
    finger3_ik = get_pose_bone("c_"+finger_type+"3_ik"+side)

    if constraint and valid_constraint:
        if parent_type == "bone":
            bone_parent = get_pose_bone(bparent_name)
            ik_target.matrix = bone_parent.matrix_channel.inverted() @ finger3_ik.matrix
            update_transform()
            # set head to tail position
            tail_mat = bone_parent.matrix_channel.inverted() @ Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
            ik_target.matrix = tail_mat @ ik_target.matrix

        if parent_type == "object":
            obj = bpy.data.objects.get(bparent_name)
            ik_target.matrix = constraint.inverse_matrix.inverted() @ obj.matrix_world.inverted() @ finger3_ik.matrix
            update_transform()
            # set head to tail position
            tail_mat = constraint.inverse_matrix.inverted() @ obj.matrix_world.inverted() @ Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
            ik_target.matrix = tail_mat @ ik_target.matrix
    else:
        ik_target.matrix = finger3_ik.matrix
        update_transform()
        # set head to tail position
        tail_mat = Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
        ik_target.matrix = tail_mat @ ik_target.matrix

    update_transform()

    # Snap phalanges
    ik_fingers = ["c_"+finger_type+"1_ik"+side, "c_"+finger_type+"2_ik"+side, "c_"+finger_type+"3_ik"+side]

        # store current matrices
    fingers_mat = []
    for i, bname in enumerate(ik_fingers):
        b_ik = get_pose_bone(bname)
        fingers_mat.append(b_ik.matrix.copy())

    # Switch prop
    root_finger["ik_tip"] = 1

    for iter in range(0,4):
        for i, bname in enumerate(ik_fingers):
            b_ik = get_pose_bone(bname)
            loc, scale = b_ik.location.copy(), b_ik.scale.copy()
            b_ik.matrix = fingers_mat[i]
            # restore loc and scale, only rotation for better results
            b_ik.location = loc
            b_ik.scale = scale
        # update hack
        update_transform()

    # udpate hack
    update_transform()

    #insert key if autokey enable
    if scn.tool_settings.use_keyframe_insert_auto:
        root_finger.keyframe_insert(data_path='["ik_tip"]')

        for bname in ik_fingers+[ik_target.name, ik_target2.name]:
            pb = get_pose_bone(bname)
            pb.keyframe_insert(data_path="location")
            if pb.rotation_mode != "QUATERNION":
                pb.keyframe_insert(data_path="rotation_euler")
            else:
                pb.keyframe_insert(data_path="rotation_quaternion")
                
            for i, j in enumerate(pb.lock_scale):
                if not j:
                    pb.keyframe_insert(data_path="scale", index=i)
                    

def root_to_tip_finger(root_finger, side):
    scn = bpy.context.scene
    finger_type = None
    rig = bpy.context.active_object

    for i in fingers_type_list:
        if i in root_finger.name:
            finger_type = i
            break

    ik_target_name = ""
    ik_tip = root_finger["ik_tip"]
    ik_target_name = "c_"+finger_type+"_ik"+side
    ik_target2_name = "c_"+finger_type+"_ik2"+side
    ik_target = get_pose_bone(ik_target_name)
    ik_target2 = get_pose_bone(ik_target2_name)

    if ik_target == None or ik_target2 == None:
        print("Finger IK target not found:", ik_target_name)
        return

    ik_pole_name = "c_"+finger_type+"_pole"+side
    ik_pole = get_pose_bone(ik_pole_name)
    if ik_pole == None:
        print("Finger IK pole not found:", ik_pole_name)
        return

    # Snap IK target
        # constraint support
    constraint, bparent_name, parent_type, valid_constraint = get_active_child_of_cns(ik_target)

    finger3_ik = get_pose_bone("c_"+finger_type+"3_ik"+side)
    if constraint and valid_constraint:
        if parent_type == "bone":
            bone_parent = get_pose_bone(bparent_name)
            ik_target2.matrix = bone_parent.matrix_channel.inverted() @ finger3_ik.matrix
            update_transform()

        elif parent_type == "object":
            obj = bpy.data.objects.get(bparent_name)
            ik_target2.matrix = constraint.inverse_matrix.inverted() @ obj.matrix_world.inverted() @ finger3_ik.matrix
            update_transform()

    else:
        ik_target2.matrix = finger3_ik.matrix
        update_transform()

    update_transform()

    # Snap phalanges
    ik_fingers = ["c_"+finger_type+"1_ik"+side, "c_"+finger_type+"2_ik"+side]

        # store current matrices
    fingers_mat = []
    for i, bname in enumerate(ik_fingers):
        b_ik = get_pose_bone(bname)
        fingers_mat.append(b_ik.matrix.copy())

    # Switch prop
    root_finger["ik_tip"] = 0

    for iter in range(0,4):
        for i, bname in enumerate(ik_fingers):
            b_ik = get_pose_bone(bname)
            loc, scale = b_ik.location.copy(), b_ik.scale.copy()
            b_ik.matrix = fingers_mat[i]
            # restore loc and scale, only rotation for better results
            b_ik.location = loc
            b_ik.scale = scale
        # update hack
        update_transform()


    #insert key if autokey enable
    if scn.tool_settings.use_keyframe_insert_auto:
        root_finger.keyframe_insert(data_path='["ik_tip"]')

        for bname in ik_fingers+[ik_target.name, ik_target2.name]:
            pb = get_pose_bone(bname)
            pb.keyframe_insert(data_path="location")
            if pb.rotation_mode != "QUATERNION":
                pb.keyframe_insert(data_path="rotation_euler")
            else:
                pb.keyframe_insert(data_path="rotation_quaternion")
            
            for i, j in enumerate(pb.lock_scale):
                if not j:
                    pb.keyframe_insert(data_path="scale", index=i)
       

def _switch_snap_pin(side, type):
    if type == "leg":
        c_leg_stretch = get_pose_bone("c_stretch_leg"+side)
        if c_leg_stretch == None:
            print("No 'c_stretch_leg' bone found")
            return

        c_leg_pin = get_pose_bone("c_stretch_leg_pin"+side)
        if c_leg_pin == None:
            print("No 'c_leg_stretch_pin' bone found")
            return

        if c_leg_stretch["leg_pin"] == 0.0:
            c_leg_pin.matrix = c_leg_stretch.matrix
            c_leg_stretch["leg_pin"] = 1.0
        else:
            c_leg_stretch["leg_pin"] = 0.0
            c_leg_stretch.matrix = c_leg_pin.matrix

    if type == "arm":
        c_arm_stretch = get_pose_bone("c_stretch_arm"+side)
        if c_arm_stretch == None:
            print("No 'c_stretch_arm' bone found")
            return

        c_arm_pin = get_pose_bone("c_stretch_arm_pin"+side)
        if c_arm_pin == None:
            print("No 'c_stretch_arm_pin' bone found")
            return
        
        # NID, new ik elbow pin snapping
        c_arm_pole = get_pose_bone("c_arms_pole"+side)
        if c_arm_pole == None:
            print("No 'c_arms_pole' bone found")
            return
        # NID END

        if c_arm_stretch["elbow_pin"] == 0.0:
            c_arm_pin.matrix = c_arm_stretch.matrix
            c_arm_stretch["elbow_pin"] = 1.0
        else:
            c_arm_stretch["elbow_pin"] = 0.0
            c_arm_stretch.matrix =  c_arm_pin.matrix
            # NID, new ik elbow pin snapping
            c_arm_pole.matrix =  c_arm_pin.matrix
            # NID END


def _set_picker_camera(self):
    # go to object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    #save current scene camera
    current_cam = bpy.context.scene.camera

    rig = bpy.data.objects.get(bpy.context.active_object.name)
    
    bpy.ops.object.select_all(action='DESELECT')
    
    cam_ui = None
    rig_ui = None
    ui_mesh = None
    char_name_text = None
    
    is_a_proxy = False
    if 'proxy_collection' in dir(rig):# proxy support
        if rig.proxy_collection:
            is_a_proxy = True
            children = rig.proxy_collection.instance_collection.all_objects
    if not is_a_proxy:
        children = rig.children

    for child in children:
        if child.type == 'CAMERA' and 'cam_ui' in child.name:
            cam_ui = child
        if child.type == 'EMPTY' and 'rig_ui' in child.name:
            rig_ui = child
            for _child in rig_ui.children:
                if _child.type == 'MESH' and 'mesh' in _child.name:
                    ui_mesh = _child

    # if the picker is not there, escape
    if rig_ui == None and is_proxy(rig) == False:
        self.report({'INFO'}, 'No picker found, click "Add Picker" to add one.')
        return

    # ui cam not found, add one
    active_obj_name = bpy.context.active_object.name
    if not cam_ui:
        bpy.ops.object.camera_add(align="VIEW", enter_editmode=False, location=(0, 0, 0), rotation=(0, 0, 0))
        # set cam data
        bpy.context.active_object.name = "cam_ui"
        cam_ui = bpy.data.objects["cam_ui"]
        cam_ui.data.type = "ORTHO"
        cam_ui.data.display_size = 0.1
        cam_ui.data.show_limits = False
        cam_ui.data.show_passepartout = False
        cam_ui.parent = bpy.data.objects[active_obj_name]

        # set collections
        for col in bpy.data.objects[active_obj_name].users_collection:
            try:
                col.objects.link(cam_ui)
            except:
                pass

    set_active_object(active_obj_name)

    if cam_ui:
        # lock the camera transforms
        ##cam_ui.lock_location[0]=cam_ui.lock_location[1]=cam_ui.lock_location[2]=cam_ui.lock_rotation[0]=cam_ui.lock_rotation[1]=cam_ui.lock_rotation[2] = True
        #cam_ui.select_set(state=1)
        #bpy.context.view_layer.objects.active = cam_ui
        #bpy.ops.view3d.object_as_camera()
        
        space_data = bpy.context.space_data
        space_data.use_local_camera = True
        space_data.camera = cam_ui
        space_data.region_3d.view_perspective = "CAMERA"

        # set viewport display options
        ##bpy.context.space_data.lock_camera_and_layers = False
        space_data.overlay.show_relationship_lines = False
        space_data.overlay.show_text = False
        space_data.overlay.show_cursor = False
        current_area = bpy.context.area
        space_view3d = [i for i in current_area.spaces if i.type == "VIEW_3D"]
        space_view3d[0].shading.type = 'SOLID'
        space_view3d[0].shading.show_object_outline = False
        space_view3d[0].shading.show_specular_highlight = False
        space_view3d[0].show_gizmo_navigate = False
        space_view3d[0].use_local_camera = True
        bpy.context.space_data.lock_camera = False#unlock camera to view

        rig_ui_scale = 1.0

        if rig_ui:
            rig_ui_scale = rig_ui.scale[0]

        units_scale = bpy.context.scene.unit_settings.scale_length
        fac_ortho = 1.8# * (1/units_scale)

        # Position the camera height to the backplate height
        if ui_mesh:
            vert_pos = [v.co for v in ui_mesh.data.vertices]
            vert_pos = sorted(vert_pos, reverse=False, key=itemgetter(2))
            max1 = ui_mesh.matrix_world @ vert_pos[0]
            max2 = ui_mesh.matrix_world @ vert_pos[len(vert_pos)-1]
            picker_size = (max1-max2).magnitude
            picker_center = (max1+max2)/2
            
            # set the camera matrix            
            pos_Z_world = rig.matrix_world.inverted() @ Vector((0.0, 0.0, picker_center[2]))
            cam_ui.matrix_world = rig.matrix_world @ Matrix.Translation(Vector((0, -40, pos_Z_world[2])))
            
            cam_ui.scale = (1.0,1.0,1.0)
            cam_ui.rotation_euler = (radians(90), 0, 0)

            # set the camera clipping and ortho scale
            bpy.context.evaluated_depsgraph_get().update()
            dist = (cam_ui.matrix_world.to_translation() - picker_center).length
            cam_ui.data.clip_start = dist*0.9
            cam_ui.data.clip_end = dist*1.1
            cam_ui.data.ortho_scale = fac_ortho * picker_size

        #restore the scene camera
        #bpy.context.scene.camera = current_cam

    else:
        self.report({'ERROR'}, 'No picker camera found for this rig')

    #back to pose mode
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(state=1)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    # enable the picker addon
    try:
        bpy.context.scene.Proxy_Picker.active = True
    except:
        pass


def project_point_onto_plane(q, p, n):
    n = n.normalized()
    return q - ((q - p).dot(n)) * n


def get_ik_pole_pos(b1, b2, dist):
    plane_normal = (b1.head - b2.tail)
    midpoint = (b1.head + b2.tail) * 0.5
    prepole_dir = b2.head - midpoint
    pole_pos = b2.head + prepole_dir.normalized()
    pole_pos = project_point_onto_plane(pole_pos, b2.head, plane_normal)
    pole_pos = b2.head + ((pole_pos - b2.head).normalized() * (b2.head - b1.head).magnitude * dist)
    
    return pole_pos


def get_pose_matrix_in_other_space(mat, pose_bone):
    rest = pose_bone.bone.matrix_local.copy()
    rest_inv = rest.inverted()
    par_mat = Matrix()
    par_inv = Matrix()
    par_rest = Matrix()
    
    # bone parent case
    if pose_bone.parent and pose_bone.bone.use_inherit_rotation:
        par_mat = pose_bone.parent.matrix.copy()
        par_inv = par_mat.inverted()
        par_rest = pose_bone.parent.bone.matrix_local.copy()
    # bone parent as constraint case
    elif len(pose_bone.constraints):
        for cns in pose_bone.constraints:
            if cns.type != 'ARMATURE':
                continue
            for tar in cns.targets:
                if tar.subtarget != '':
                    if tar.weight > 0.5:# not ideal, but take the bone as parent if influence is above average
                        par_bone = get_pose_bone(tar.subtarget)
                        par_mat = par_bone.matrix.copy()
                        par_inv = par_mat.inverted()
                        par_rest = par_bone.bone.matrix_local.copy()
                        break

    smat = rest_inv @ (par_rest @ (par_inv @ mat))

    return smat


def _snap_head(side):
    c_head = get_pose_bone("c_head"+side)
    head_scale_fix = get_pose_bone("head_scale_fix" + side)

    # get the bone parent (constrained) of head_scale_fix
    head_scale_fix_parent = None
    for cns in head_scale_fix.constraints:
        if cns.type == "CHILD_OF" and cns.influence == 1.0:
            head_scale_fix_parent = get_pose_bone(cns.subtarget)

    c_head_loc = c_head.location.copy()

    # matrices evaluations
    c_head_mat = c_head.matrix.copy()
    head_scale_fix_mat = head_scale_fix_parent.matrix_channel.inverted() @ head_scale_fix.matrix_channel

    # switch the prop
    c_head["head_free"] = 0 if c_head["head_free"] == 1 else 1

    # apply the matrices
    # two time because of a dependency lag
    for i in range(0,2):
        update_transform()
        c_head.matrix = head_scale_fix_mat.inverted() @ c_head_mat
        # the location if offset, preserve it
        c_head.location = c_head_loc

    #insert keyframe if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        c_head.keyframe_insert(data_path='["head_free"]')


def set_pos(pose_bone, mat):
    if pose_bone.bone.use_local_location == True:
        pose_bone.location = mat.to_translation()
    else:
        loc = mat.to_translation()

        rest = pose_bone.bone.matrix_local.copy()
        if pose_bone.bone.parent:
            par_rest = pose_bone.bone.parent.matrix_local.copy()
        else:
            par_rest = Matrix()

        q = (par_rest.inverted() @ rest).to_quaternion()
        pose_bone.location = q @ loc


def set_pose_rotation(pose_bone, mat):
    q = mat.to_quaternion()

    if pose_bone.rotation_mode == 'QUATERNION':
        pose_bone.rotation_quaternion = q
    elif pose_bone.rotation_mode == 'AXIS_ANGLE':
        pose_bone.rotation_axis_angle[0] = q.angle
        pose_bone.rotation_axis_angle[1] = q.axis[0]
        pose_bone.rotation_axis_angle[2] = q.axis[1]
        pose_bone.rotation_axis_angle[3] = q.axis[2]
    else:
        pose_bone.rotation_euler = q.to_euler(pose_bone.rotation_mode)


def snap_pos(pose_bone, target_bone):
    # Snap a bone to another bone. Supports child of constraints and parent.
    """
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pos(pose_bone, mat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    """

    # if the pose_bone has direct parent
    if pose_bone.parent:
        # apply double time because of dependecy lag
        pose_bone.matrix = target_bone.matrix
        #update hack
        update_transform()
        # second apply
        pose_bone.matrix = target_bone.matrix
    else:
        # is there a child of constraint attached?
        child_of_cns = None
        if len(pose_bone.constraints) > 0:
            all_child_of_cns = [i for i in pose_bone.constraints if i.type == "CHILD_OF" and i.influence == 1.0 and i.mute == False and i.target]
            if len(all_child_of_cns) > 0:
                child_of_cns = all_child_of_cns[0]# in case of multiple child of constraints enabled, use only the first for now

        if child_of_cns != None:
            if child_of_cns.subtarget != "" and get_pose_bone(child_of_cns.subtarget):
                # apply double time because of dependecy lag
                pose_bone.matrix = get_pose_bone(child_of_cns.subtarget).matrix_channel.inverted() @ target_bone.matrix
                update_transform()
                pose_bone.matrix = get_pose_bone(child_of_cns.subtarget).matrix_channel.inverted() @ target_bone.matrix
            else:
                pose_bone.matrix = target_bone.matrix

        else:
            pose_bone.matrix = target_bone.matrix

            
def update_transform():   
    # hack to trigger the update with a blank rotation operator
    bpy.ops.transform.rotate(value=0, orient_axis='Z', orient_type='VIEW', orient_matrix=((0.0, 0.0, 0), (0, 0.0, 0.0), (0.0, 0.0, 0.0)), orient_matrix_type='VIEW', mirror=False)

    
def get_ik_fk_angle_offset(fk1, fk2, ik1, ik2, pole):
    def signed_angle(vector_u, vector_v, normal):
        normal = normal.normalized()
        a = vector_u.angle(vector_v)
        if vector_u.magnitude != 0.0 and vector_v.magnitude != 0.0 and normal.magnitude != 0.0:
            if vector_u.cross(vector_v).magnitude != 0.0:      
                if vector_u.cross(vector_v).angle(normal) < 1:
                    a = -a
        return a
    
    midpoint = (fk2.tail + fk1.head) / 2
    vec1 = fk2.head - midpoint
    vec2 = ik2.head - midpoint
    pole_normal = (ik2.tail - ik1.head).cross(pole.head - ik1.head)
    angle = signed_angle(vec1, vec2, pole_normal)
    return angle
    
    
def snap_pos_matrix(pose_bone, target_bone_matrix):
    # Snap a bone to another bone. Supports child of constraints and parent.

    # if the pose_bone has direct parent
    if pose_bone.parent:       
        pose_bone.matrix = target_bone_matrix.copy()        
        update_transform()
    else:
        # is there a child of constraint attached?
        child_of_cns = None
        if len(pose_bone.constraints) > 0:
            all_child_of_cns = [i for i in pose_bone.constraints if i.type == "CHILD_OF" and i.influence == 1.0 and i.mute == False and i.target]
            if len(all_child_of_cns) > 0:
                child_of_cns = all_child_of_cns[0]# in case of multiple child of constraints enabled, use only the first for now

        if child_of_cns:
            if child_of_cns.subtarget != "" and get_pose_bone(child_of_cns.subtarget):              
                pose_bone.matrix = get_pose_bone(child_of_cns.subtarget).matrix_channel.inverted_safe() @ target_bone_matrix                
                update_transform()
            else:
                pose_bone.matrix = target_bone_matrix.copy()
        else:
            pose_bone.matrix = target_bone_matrix.copy()


def snap_rot(pose_bone, target_bone):
    mat = get_pose_matrix_in_other_space(target_bone.matrix, pose_bone)
    set_pose_rotation(pose_bone, mat)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')


def set_inverse_child(b):
    pbone = bpy.context.active_object.pose.bones[b]
    context_copy = bpy.context.copy()
    context_copy["constraint"] = pbone.constraints["Child Of"]
    bpy.context.active_object.data.bones.active = pbone.bone
    bpy.ops.constraint.childof_set_inverse(context_copy, constraint="Child Of", owner='BONE')


def convert_rot_mode(self):
    scn = bpy.context.scene
    armature = bpy.context.active_object
    rot_mode_tar = self.mode
    current_frame = scn.frame_current
    
    def set_target_rot_mode(pb):
        pb.rotation_mode = 'QUATERNION' if rot_mode_tar == 'rotation_quaternion' else self.euler_order
        
    def insert_keyframe(pb):
        pb.keyframe_insert(data_path=rot_mode_tar)
        # Todo, auto-keyframing the rot mode is not supported for now, it leads to rotation conversion update issue
        # see if it can be fixed later
        #if self.key_rot_mode:
        #    pb.keyframe_insert(data_path='rotation_mode')


    pose_bones = bpy.context.selected_pose_bones if self.selected_only else armature.pose.bones
    
    if len(pose_bones) == 0:
        return
        
    for pb in pose_bones:
        current_mode = pb.rotation_mode
        pb_path = pb.path_from_id() 
        fc_data_path = pb_path+'.rotation_quaternion' if current_mode == 'QUATERNION' else pb_path+'.rotation_euler'        
        fc = armature.animation_data.action.fcurves.find(fc_data_path)       
        
        if fc == None and self.selected_only == False:# only animated bones, otherwise could insert keyframes on unwanted bones (rig mechanics)
            continue
                
        keyf_to_del = []
                
        if self.one_key_per_frame:            
                
            for f in range(self.frame_start, self.frame_end +1):
                scn.frame_set(f)
                
                for pb in pose_bones:
                    current_mode = pb.rotation_mode
                    
                    # convert rot mode
                    set_target_rot_mode(pb)                          
                    
                    # add keyframe
                    insert_keyframe(pb)
                    
                    # restore rot mode for next keyframe
                    if f != self.frame_end:
                        pb.rotation_mode = current_mode
        
        else:# only convert existing keyframes     
            if fc == None:
                # no keyframes yet, convert rot mode
                set_target_rot_mode(pb)
                continue                
            
            for keyf in fc.keyframe_points:
                if keyf.co[0] >= self.frame_start and keyf.co[0] <= self.frame_end:
                    scn.frame_set(int(keyf.co[0]))
                    keyf_to_del.append(keyf.co[0])
                    set_target_rot_mode(pb)        
                    insert_keyframe(pb)                    
                    
                    # restore rot mode for next keyframe                    
                    pb.rotation_mode = current_mode                    
        
                        
        set_target_rot_mode(pb)
        
    # restore initial frame
    scn.frame_set(current_frame)
    
    
def bake_fk_to_ik_arm(self):
    for f in range(self.frame_start, self.frame_end +1):
        bpy.context.scene.frame_set(f)
        #print("baking frame", f)

        fk_to_ik_arm(bpy.context.active_object, self.side)


def fk_to_ik_arm(obj, side):

    arm_fk  = obj.pose.bones[fk_arm[0] + side]
    forearm_fk  = obj.pose.bones[fk_arm[1] + side]
    hand_fk  = obj.pose.bones[fk_arm[2] + side]

    arm_ik = obj.pose.bones[ik_arm[0] + side]
    forearm_ik = obj.pose.bones[ik_arm[1] + side]
    hand_ik = obj.pose.bones[ik_arm[2] + side]
    pole = obj.pose.bones[ik_arm[3] + side]

    # Stretch
    if hand_ik['auto_stretch'] == 0.0:
        hand_fk['stretch_length'] = hand_ik['stretch_length']
    else:
        diff = (arm_ik.length+forearm_ik.length) / (arm_fk.length+forearm_fk.length)
        hand_fk['stretch_length'] *= diff

    #Snap rot
    snap_rot(arm_fk, arm_ik)
    snap_rot(forearm_fk, forearm_ik)
    snap_rot(hand_fk, hand_ik)

    #Snap scale
    hand_fk.scale =hand_ik.scale

    #rot debug
    forearm_fk.rotation_euler[0]=0
    forearm_fk.rotation_euler[1]=0

    #switch
    hand_ik['ik_fk_switch'] = 1.0

    #udpate view   
    bpy.context.view_layer.update()

    #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        #fk chain
        hand_ik.keyframe_insert(data_path='["ik_fk_switch"]')
        hand_fk.keyframe_insert(data_path='["stretch_length"]')
        
        keyframe_pb_transforms(hand_fk, loc=False)
        keyframe_pb_transforms(arm_fk, loc=False, scale=False)
        keyframe_pb_transforms(forearm_fk, loc=False, scale=False)

        #ik chain
        hand_ik.keyframe_insert(data_path='["stretch_length"]')
        hand_ik.keyframe_insert(data_path='["auto_stretch"]')
        keyframe_pb_transforms(hand_ik)
        pole.keyframe_insert(data_path='location')

    # change hand IK to FK selection, if selected
    if hand_ik.bone.select:    
        hand_fk.bone.select = True
        obj.data.bones.active = hand_fk.bone
        hand_ik.bone.select = False        
        

def bake_ik_to_fk_arm(self):
    for f in range(self.frame_start, self.frame_end +1):
        bpy.context.scene.frame_set(f)

        ik_to_fk_arm(bpy.context.active_object, self.side)


def ik_to_fk_arm(obj, side):
    arm_fk  = obj.pose.bones[fk_arm[0] + side]
    forearm_fk  = obj.pose.bones[fk_arm[1] + side]
    hand_fk  = obj.pose.bones[fk_arm[2] + side]    

    arm_ik = obj.pose.bones[ik_arm[0] + side]
    forearm_ik = obj.pose.bones[ik_arm[1] + side]
    hand_ik = obj.pose.bones[ik_arm[2] + side]
    pole  = obj.pose.bones[ik_arm[3] + side]

    # reset custom pole angle if any
    if obj.pose.bones.get("c_arm_ik" + side) != None:
        obj.pose.bones["c_arm_ik" + side].rotation_euler[1] = 0.0

    # Stretch
    hand_ik['stretch_length'] = hand_fk['stretch_length']

    # Snap
    #   constraint support
    constraint = None
    bparent_name = ""
    parent_type = ""
    valid_constraint = True

    if len(hand_ik.constraints) > 0:
        for c in hand_ik.constraints:
            if not c.mute and c.influence > 0.5 and c.type == 'CHILD_OF':
                if c.target:
                    #if bone
                    if c.target.type == 'ARMATURE':
                        bparent_name = c.subtarget
                        parent_type = "bone"
                        constraint = c
                    #if object
                    else:
                        bparent_name = c.target.name
                        parent_type = "object"
                        constraint = c


    if constraint != None:
        if parent_type == "bone":
            if bparent_name == "":
                valid_constraint = False

    if constraint and valid_constraint:
        if parent_type == "bone":
            bone_parent = bpy.context.object.pose.bones[bparent_name]
            hand_ik.matrix = bone_parent.matrix_channel.inverted()@ hand_fk.matrix
        if parent_type == "object":
            bone_parent = bpy.data.objects[bparent_name]
            obj_par = bpy.data.objects[bparent_name]
            hand_ik.matrix = constraint.inverse_matrix.inverted() @ obj_par.matrix_world.inverted() @ hand_fk.matrix
    else:
        hand_ik.matrix = hand_fk.matrix

    # Pole target position
    pole_dist = 1.0
    hand_ref = get_data_bone("hand_ref"+side)
    if hand_ref:
        if "ik_pole_distance" in hand_ref.keys():
            pole_dist = hand_ref["ik_pole_distance"]

    pole_pos = get_ik_pole_pos(arm_fk, forearm_fk, pole_dist)
    pole_mat = Matrix.Translation(pole_pos)
    snap_pos_matrix(pole, pole_mat)
    
    # there may be still an offset angle in case automatic IK roll alignment if disabled
    # compensate
    compensate_ik_pole_position(arm_fk, forearm_fk, arm_ik, forearm_ik, pole)
    
    # switch
    hand_ik['ik_fk_switch'] = 0.0

    #update view  
    bpy.context.view_layer.update()  

     #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        #ik chain
        hand_ik.keyframe_insert(data_path='["ik_fk_switch"]')
        hand_ik.keyframe_insert(data_path='["stretch_length"]')
        hand_ik.keyframe_insert(data_path='["auto_stretch"]')
        keyframe_pb_transforms(hand_ik)
        pole.keyframe_insert(data_path="location")

        #ik controller if any
        if obj.pose.bones.get('c_arm_ik' + side) != None:
            get_pose_bone('c_arm_ik' + side).keyframe_insert(data_path="rotation_euler", index=1)    

        #fk chain
        hand_fk.keyframe_insert(data_path='["stretch_length"]')
        keyframe_pb_transforms(hand_fk) 
        keyframe_pb_transforms(arm_fk, loc=False, scale=False)       
        keyframe_pb_transforms(forearm_fk, loc=False, scale=False)

    # change FK to IK hand selection, if selected
    if hand_fk.bone.select:
        hand_ik.bone.select = True
        obj.data.bones.active = hand_ik.bone
        hand_fk.bone.select = False
        
    #update hack
    update_transform()


def bake_fk_to_ik_leg(self):
    for f in range(self.frame_start, self.frame_end +1):
        bpy.context.scene.frame_set(f)
        #print("baking frame", f)

        fk_to_ik_leg(bpy.context.active_object, self.side)


def fk_to_ik_leg(obj, side):
    thigh_fk  = get_pose_bone(fk_leg[0] + side)
    leg_fk  = get_pose_bone(fk_leg[1] + side)
    foot_fk  = get_pose_bone(fk_leg[2] + side)
    toes_fk = get_pose_bone(fk_leg[3] + side)

    thigh_ik = get_pose_bone(ik_leg[0] + side)
    thigh_ik_nostr = get_pose_bone(ik_leg[0]+'_nostr'+side)
    leg_ik = get_pose_bone(ik_leg[1] + side)
    leg_ik_nostr = get_pose_bone(ik_leg[1]+'_nostr'+side)
    foot_ik = get_pose_bone(ik_leg[2] + side)
    pole = get_pose_bone(ik_leg[3] + side)
    toes_ik = get_pose_bone(ik_leg[4] + side)
    foot_01 = get_pose_bone(ik_leg[5] + side)
    foot_roll = get_pose_bone(ik_leg[6] + side)
    footi_rot = get_pose_bone(ik_leg[7] + side)

    # save the c_thigh_b matrix if any
    c_thigh_b = get_pose_bone("c_thigh_b"+side)
    if c_thigh_b:
        c_thigh_b_matrix = c_thigh_b.matrix.copy()

    # Stretch
    soft_ik = 'leg_softik' in foot_ik.keys()
    
    if foot_ik['auto_stretch'] == 0.0 and soft_ik == False:
        foot_fk['stretch_length'] = foot_ik['stretch_length']       
    else:
        diff = (thigh_ik.length+leg_ik.length) / (thigh_fk.length+leg_fk.length)
        foot_fk['stretch_length'] *= diff

    # Thigh snap
    snap_rot(thigh_fk, thigh_ik)

    # Leg snap
    snap_rot(leg_fk, leg_ik)

    # foot_fk snap
    snap_rot(foot_fk, footi_rot)
    #   scale
    foot_fk.scale =foot_ik.scale

    #Toes snap
    snap_rot(toes_fk, toes_ik)
    #   scale
    toes_fk.scale =toes_ik.scale

    # rotation debug
    leg_fk.rotation_euler[0]=0
    leg_fk.rotation_euler[1]=0

    # switch
    foot_ik['ik_fk_switch'] = 1.0

    # udpate hack  
    bpy.context.view_layer.update()

    if c_thigh_b:
        c_thigh_b.matrix = c_thigh_b_matrix.copy()


    #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        #fk chain
        foot_ik.keyframe_insert(data_path='["ik_fk_switch"]')
        foot_fk.keyframe_insert(data_path='["stretch_length"]')
        keyframe_pb_transforms(foot_fk, loc=False)
        keyframe_pb_transforms(thigh_fk, loc=False, scale=False)
        keyframe_pb_transforms(leg_fk, loc=False, scale=False)
        keyframe_pb_transforms(toes_fk, loc=False)
      
        #ik chain
        foot_ik.keyframe_insert(data_path='["stretch_length"]')
        foot_ik.keyframe_insert(data_path='["auto_stretch"]')
        keyframe_pb_transforms(foot_ik)   

        foot_01.keyframe_insert(data_path='rotation_euler')
        foot_roll.keyframe_insert(data_path='location')
        keyframe_pb_transforms(toes_ik, loc=False)
        pole.keyframe_insert(data_path="location")

        #ik angle controller if any
        if get_pose_bone('c_thigh_ik'+side) != None:
            get_pose_bone('c_thigh_ik'+side).keyframe_insert(data_path='rotation_euler', index=1)

    # change IK to FK foot selection, if selected
    if foot_ik.bone.select:
        foot_fk.bone.select = True
        obj.data.bones.active = foot_fk.bone
        foot_ik.bone.select = False      


def bake_ik_to_fk_leg(self):
    for f in range(self.frame_start, self.frame_end +1):
        bpy.context.scene.frame_set(f)
        #print("baking frame", f)

        ik_to_fk_leg(bpy.context.active_object, self.side)


def ik_to_fk_leg(rig, side):
    thigh_fk = get_pose_bone(fk_leg[0] + side)
    leg_fk = get_pose_bone(fk_leg[1] + side)
    foot_fk = get_pose_bone(fk_leg[2] + side)
    toes_fk = get_pose_bone(fk_leg[3] + side)    
    
    thigh_ik = get_pose_bone(ik_leg[0] + side)
    leg_ik = get_pose_bone(ik_leg[1] + side)  
    foot_ik = get_pose_bone(ik_leg[2] + side)
    pole_ik = get_pose_bone(ik_leg[3] + side)
    toes_ik = get_pose_bone(ik_leg[4] + side)
    foot_01 = get_pose_bone(ik_leg[5] + side)
    foot_roll = get_pose_bone(ik_leg[6] + side)
    toes_pivot = get_pose_bone("c_toes_pivot"+side)
    ik_offset = get_pose_bone("c_foot_ik_offset"+side)

    # Snap Stretch
    soft_ik = 'leg_softik' in foot_ik.keys()
    
    if soft_ik == False:
        foot_ik['stretch_length'] = foot_fk['stretch_length']
    else:
        soft_ik_fac = foot_ik['stretch_length'] / (thigh_ik.length+leg_ik.length)       
        foot_ik['stretch_length'] = soft_ik_fac * (thigh_fk.length+leg_fk.length)

    # reset IK foot_01, toes_pivot, ik_offset, foot_roll
    foot_01.rotation_euler = [0,0,0]
    
    if toes_pivot:
        toes_pivot.rotation_euler = toes_pivot.location = [0,0,0]
    if ik_offset:
        ik_offset.rotation_euler = ik_offset.location = [0,0,0]

    foot_roll.location[0] = 0.0
    foot_roll.location[2] = 0.0

    # reset custom pole angle if any
    if rig.pose.bones.get("c_thigh_ik" + side) != None:
        rig.pose.bones["c_thigh_ik" + side].rotation_euler[1] = 0.0
    
    # save the c_thigh_b matrix if any
    c_thigh_b = get_pose_bone("c_thigh_b"+side)
    if c_thigh_b:
        c_thigh_b_matrix = c_thigh_b.matrix.copy()

    # Snap Toes
    toes_ik.rotation_euler= toes_fk.rotation_euler
    toes_ik.scale = toes_fk.scale
    
    # Child Of constraint or parent cases
    constraint = None
    bparent_name = ""
    parent_type = ""
    valid_constraint = True

    if len(foot_ik.constraints) > 0:
        for c in foot_ik.constraints:
            if not c.mute and c.influence > 0.5 and c.type == 'CHILD_OF':
                if c.target:
                    #if bone
                    if c.target.type == 'ARMATURE':
                        bparent_name = c.subtarget
                        parent_type = "bone"
                        constraint = c
                    #if object
                    else:
                        bparent_name = c.target.name
                        parent_type = "object"
                        constraint = c


    if constraint != None:
        if parent_type == "bone":
            if bparent_name == "":
                valid_constraint = False

    # Snap Foot
    if constraint and valid_constraint:
        if parent_type == "bone":
            bone_parent = get_pose_bone(bparent_name)
            foot_ik.matrix = bone_parent.matrix_channel.inverted() @ foot_fk.matrix
        if parent_type == "object":
            rig = bpy.data.objects[bparent_name]
            foot_ik.matrix = constraint.inverse_matrix.inverted() @ rig.matrix_world.inverted() @ foot_fk.matrix

    else:
        foot_ik.matrix = foot_fk.matrix.copy()
    
    # udpate
    bpy.context.view_layer.update()    
    
    # Snap Pole
    pole_dist = 1.0
    foot_ref = get_data_bone("foot_ref"+side)
    if foot_ref:
        if "ik_pole_distance" in foot_ref.keys():
            pole_dist = foot_ref["ik_pole_distance"]

    pole_pos = get_ik_pole_pos(thigh_fk, leg_fk, pole_dist)
    pole_mat = Matrix.Translation(pole_pos)
    snap_pos_matrix(pole_ik, pole_mat)    
    compensate_ik_pole_position(thigh_fk, leg_fk, thigh_ik, leg_ik, pole_ik)
        
    #if bpy.context.scene.frame_current == 1:
    #    print(br)
    
    # udpate hack
    update_transform()
    
     # Switch prop
    foot_ik['ik_fk_switch'] = 0.0

    # udpate hack
    update_transform()

     # Restore c_thigh_b matrix if any
    if c_thigh_b:
        c_thigh_b.matrix = c_thigh_b_matrix.copy()

    #update hack
    update_transform()

    #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        #ik chain
        foot_ik.keyframe_insert(data_path='["ik_fk_switch"]')
        foot_ik.keyframe_insert(data_path='["stretch_length"]')        
        foot_ik.keyframe_insert(data_path='["auto_stretch"]')
        
        keyframe_pb_transforms(foot_ik)                
        foot_01.keyframe_insert(data_path="rotation_euler")
        foot_roll.keyframe_insert(data_path="location")
        keyframe_pb_transforms(toes_ik, loc=False)        
        pole_ik.keyframe_insert(data_path="location")
        
        #ik controller if any
        if get_pose_bone('c_thigh_ik'+side):            
            get_pose_bone('c_thigh_ik'+side).keyframe_insert(data_path="rotation_euler", index=1)

        #fk chain        
        foot_fk.keyframe_insert(data_path='["stretch_length"]')
        keyframe_pb_transforms(foot_fk, loc=False)
        keyframe_pb_transforms(thigh_fk, loc=False, scale=False)
        keyframe_pb_transforms(leg_fk, loc=False, scale=False)
        keyframe_pb_transforms(toes_fk, loc=False)
       
        
    # change FK to IK foot selection, if selected
    if foot_fk.bone.select:        
        foot_ik.bone.select = True
        rig.data.bones.active = foot_ik.bone
        foot_fk.bone.select = False        


def _arp_snap_pole(ob, side, bone_type):
    pole = get_pose_bone('c_' + bone_type + '_pole' + side)
    
    if pole:     
        if "pole_parent" in pole.keys():
            # save the pole matrix
            pole_mat = pole.matrix.copy()

            # switch the property
            if pole["pole_parent"] == 0:
                pole["pole_parent"] = 1
            else:
                pole["pole_parent"] = 0

            #update view
            update_transform()

            # are constraints there?
            cons = [None, None]
            for cns in pole.constraints:
                if cns.name == "Child Of_local":
                    cons[0] = cns
                if cns.name == "Child Of_global":
                    cons[1] = cns


            # if yes, set parent inverse
            if cons[0] != None and cons[1] != None:
                if pole["pole_parent"] == 0:
                    pole.matrix = get_pose_bone(cons[1].subtarget).matrix_channel.inverted() @ pole_mat
                    #pole.matrix = get_pose_bone(cons[1].subtarget).matrix.inverted()
                if pole["pole_parent"] == 1:
                    pole.matrix = get_pose_bone(cons[0].subtarget).matrix_channel.inverted() @ pole_mat

        else:
            print("No pole_parent poprerty found")

    else:
        print("No c_leg_pole found")


def get_active_child_of_cns(bone):
    constraint = None
    bparent_name = ""
    parent_type = ""
    valid_constraint = True

    if len(bone.constraints) > 0:
        for c in bone.constraints:
            if not c.mute and c.influence > 0.5 and c.type == 'CHILD_OF':
                if c.target:
                    if c.target.type == 'ARMATURE':# bone
                        bparent_name = c.subtarget
                        parent_type = "bone"
                        constraint = c
                    else:# object
                        bparent_name = c.target.name
                        parent_type = "object"
                        constraint = c

    if constraint:
        if parent_type == "bone":
            if bparent_name == "":
                valid_constraint = False

    return constraint, bparent_name, parent_type, valid_constraint


def ik_to_fk_finger(root_finger, side):
    finger_type = None
    rig = bpy.context.active_object

    for i in fingers_type_list:
        if i in root_finger.name:
            finger_type = i
            break

    ik_target_name = ""
    ik_tip = root_finger["ik_tip"]

    if ik_tip == 1:# ik1
        ik_target_name = "c_"+finger_type+"_ik"+side
    elif ik_tip == 0:# ik2
        ik_target_name = "c_"+finger_type+"_ik2"+side

    ik_target = get_pose_bone(ik_target_name)
    if ik_target == None:
        print("Finger IK target not found:", ik_target_name)
        return

    ik_pole_name = "c_"+finger_type+"_pole"+side
    ik_pole = get_pose_bone(ik_pole_name)
    if ik_pole == None:
        print("Finger IK pole not found:", ik_pole_name)
        return

    hand_b = get_data_bone("hand_ref"+side)

    fingers_ik_pole_distance = 1.0
    if "fingers_ik_pole_distance" in hand_b.keys():
        fingers_ik_pole_distance = hand_b["fingers_ik_pole_distance"]

    # Snap IK target
        # constraint support
    constraint, bparent_name, parent_type, valid_constraint = get_active_child_of_cns(ik_target)

    finger3_fk = get_pose_bone("c_"+finger_type+"3"+side)
    if constraint and valid_constraint:
        if parent_type == "bone":
            bone_parent = get_pose_bone(bparent_name)
            ik_target.matrix = bone_parent.matrix_channel.inverted() @ finger3_fk.matrix
            update_transform()
            if ik_tip == 1:
                # set head to tail position
                tail_mat = bone_parent.matrix_channel.inverted() @ Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
                ik_target.matrix = tail_mat @ ik_target.matrix

        if parent_type == "object":
            obj = bpy.data.objects.get(bparent_name)
            ik_target.matrix = constraint.inverse_matrix.inverted() @ obj.matrix_world.inverted() @ finger3_fk.matrix
            update_transform()
            if ik_tip == 1:
                # set head to tail position
                tail_mat = constraint.inverse_matrix.inverted() @ obj.matrix_world.inverted() @ Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
                ik_target.matrix = tail_mat @ ik_target.matrix
    else:
        ik_target.matrix = finger3_fk.matrix
        update_transform()
        if ik_tip == 1:
            # set head to tail position
            tail_mat = Matrix.Translation((ik_target.y_axis.normalized() * ik_target.length))
            ik_target.matrix = tail_mat @ ik_target.matrix

    update_transform()

    # Snap IK pole
    fk_fingers = ["c_"+finger_type+"1"+side, "c_"+finger_type+"2"+side, "c_"+finger_type+"3"+side]
    ik_fingers = ["c_"+finger_type+"1_ik"+side, "c_"+finger_type+"2_ik"+side, "c_"+finger_type+"3_ik"+side]

    if ik_tip == 0:# only the first two phalanges must be snapped if ik2, since the last is the IK target
        fk_fingers.pop()
        ik_fingers.pop()

    phal2 = get_pose_bone(fk_fingers[1])
        # constraint support
    pole_cns, bpar_name, par_type, valid_cns = get_active_child_of_cns(ik_pole)

    if pole_cns and valid_cns:
        bone_parent = get_pose_bone(bpar_name)
        ik_pole.matrix = bone_parent.matrix_channel.inverted() @ Matrix.Translation((phal2.z_axis.normalized() * phal2.length * 1.3 * fingers_ik_pole_distance)) @ phal2.matrix
    else:
        ik_pole.matrix = Matrix.Translation((phal2.z_axis.normalized() * phal2.length * 1.3 * fingers_ik_pole_distance)) @ phal2.matrix

    ik_pole.rotation_euler = [0,0,0]

    update_transform()

        # phalanges
    for iter in range(0,4):
        for i, bname in enumerate(ik_fingers):
            b_ik = get_pose_bone(bname)
            loc, scale = b_ik.location.copy(), b_ik.scale.copy()
            b_fk = get_pose_bone(fk_fingers[i])
            b_ik.matrix = b_fk.matrix
            # restore loc and scale, only rotation for better results
            b_ik.location = loc
            b_ik.scale = scale
            # update hack
            update_transform()

     # Switch prop
    root_finger['ik_fk_switch'] = 0.0

    # udpate hack
    update_transform()

    #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        root_finger.keyframe_insert(data_path='["ik_fk_switch"]')

        for bname in ik_fingers + fk_fingers + [ik_target.name]:
            pb = get_pose_bone(bname)
            pb.keyframe_insert(data_path="location")
            if pb.rotation_mode != "QUATERNION":
                pb.keyframe_insert(data_path="rotation_euler")
            else:
                pb.keyframe_insert(data_path="rotation_quaternion")
            
            for i, j in enumerate(pb.lock_scale):
                if not j:
                    pb.keyframe_insert(data_path="scale", index=i)
          

def fk_to_ik_finger(root_finger, side):
    finger_type = None

    for i in fingers_type_list:
        if i in root_finger.name:
            finger_type = i
            break

    ik_target_name = "c_"+finger_type+"_ik"+side
    ik_target = get_pose_bone(ik_target_name)
    if ik_target == None:
        print("Finger IK target not found:", ik_target_name)
        return

    # snap
    fk_fingers = ["c_"+finger_type+"1"+side, "c_"+finger_type+"2"+side, "c_"+finger_type+"3"+side]
    ik_fingers = ["c_"+finger_type+"1_ik"+side, "c_"+finger_type+"2_ik"+side, "c_"+finger_type+"3_ik"+side]

    for i in range(0,2):
        for i, name in enumerate(fk_fingers):
            b_fk = get_pose_bone(name)
            b_ik = get_pose_bone(ik_fingers[i])
            b_fk.matrix = b_ik.matrix

            # udpate hack
            update_transform()

     #switch
    root_finger['ik_fk_switch'] = 1.0

    # udpate hack
    update_transform()

    #insert key if autokey enable
    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
        root_finger.keyframe_insert(data_path='["ik_fk_switch"]')

        for bname in ik_fingers + fk_fingers + [ik_target.name]:
            pb = get_pose_bone(bname)
            pb.keyframe_insert(data_path="location")
            if pb.rotation_mode != "QUATERNION":
                pb.keyframe_insert(data_path="rotation_euler")
            else:
                pb.keyframe_insert(data_path="rotation_quaternion")
            
            for i, j in enumerate(pb.lock_scale):
                if not j:
                    pb.keyframe_insert(data_path="scale", index=i) 


def get_data_bone(name):
    return bpy.context.active_object.data.bones.get(name)
    

def get_pose_bone(name):
    return bpy.context.active_object.pose.bones.get(name)
    
    
def get_edit_bone(name):
    return bpy.context.active_object.data.edit_bones.get(name)
    

def _toggle_multi(limb, id, key):
    bone_list = []

    if limb == 'arm':
        bone_list = auto_rig_datas.arm_displayed + auto_rig_datas.fingers_displayed
    if limb == 'leg':
        bone_list = auto_rig_datas.leg_control

    if get_pose_bone('c_pos')[key] == 1:
        get_pose_bone('c_pos')[key] = 0
    else:
        get_pose_bone('c_pos')[key] = 1

    for bone in bone_list:
        current_bone = get_data_bone(bone+'_dupli_'+id)
        if current_bone:      
            if get_pose_bone('c_pos')[key] == 0:
                current_bone.hide = True
            else:
                current_bone.hide = False   


def is_selected(names, selected_bone_name, startswith=False):
    bone_side = get_bone_side(selected_bone_name)
    if startswith == False:
        if type(names) == list:
            for name in names:
                if not "." in name[-2:]:
                    if name + bone_side == selected_bone_name:
                        return True
                else:
                    if name[-2:] == ".x":
                        if name[:-2] + bone_side == selected_bone_name:
                            return True
        elif names == selected_bone_name:
            return True
    else:#startswith
        if type(names) == list:
            for name in names:
                if selected_bone_name.startswith(name):
                    return True
        else:
            return selected_bone_name.startswith(names)
    return False


def is_selected_prop(pbone, prop_name):
    if pbone.bone.keys():
        if prop_name in pbone.bone.keys():
            return True


def _add_layer_set(self):
    rig = bpy.context.active_object
    
    new_set = rig.layers_sets.add()
    new_set.name = 'LayerSet'    

    rig.layers_sets_idx = len(rig.layers_sets)-1    

        
def _remove_layer_set(self):
    rig = bpy.context.active_object
    
    rig.layers_sets.remove(rig.layers_sets_idx)
    
    if rig.layers_sets_idx > len(rig.layers_sets)-1:
        rig.layers_sets_idx = len(rig.layers_sets)-1
    
    
    
# Rig UI Panels ##################################################################################################################
class ArpRigToolsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_category = "Tool"
    
    
class ARP_PT_RigProps(Panel, ArpRigToolsPanel):
    bl_label = "Rig Main Properties"    
    
    @classmethod
    def poll(self, context):
        if context.active_object:
            return context.active_object.type == "ARMATURE"      
        
        
    def draw(self, context): 
        pass    


class ARP_PT_RigProps_LayerSets(Panel, ArpRigToolsPanel):
    bl_label = "Rig Layers"
    bl_parent_id = "ARP_PT_RigProps"   
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene
        rig = context.active_object        
       
        row = layout.row(align=True)
        row.template_list("ARP_UL_layers_sets_list", "", rig, "layers_sets", rig, "layers_sets_idx", rows=5)
        col = row.column(align=True)
        col.operator(ARP_OT_layers_sets_add.bl_idname, text="", icon="ADD")
        col.operator(ARP_OT_layers_sets_remove.bl_idname, text="", icon="REMOVE")
        col.separator()
        col.menu("ARP_MT_layers_sets_menu", icon='DOWNARROW_HLT', text="")
        col.separator()
        col.separator()
        col.operator(ARP_OT_layers_sets_move.bl_idname, text="", icon="TRIA_UP").direction = 'UP'
        col.operator(ARP_OT_layers_sets_move.bl_idname, text="", icon="TRIA_DOWN").direction = 'DOWN'
   
        layout.separator()
        
 
class ARP_PT_BoneCustomProps(Panel, ArpRigToolsPanel):
    bl_label = "Bone Custom Props"
    bl_parent_id = "ARP_PT_RigProps"   
    bl_options = {'DEFAULT_CLOSED'}
       
    @classmethod    
    def poll(self, context):
        return context.mode == 'POSE'
   
    def draw(self, context):
        try:
            active_bone = context.selected_pose_bones[0]
        except:
            return
        
        layout = self.layout  
        col = layout.column(align=True)   
        rig = bpy.context.active_object
            
        # pinned props
        if 'arp_pinned_props' in rig.data.keys():
            pinned_props_list = get_pinned_props_list(rig)
            
            if len(rig.data['arp_pinned_props']):
                col.label(text="Pinned Props:")
                
                for prop_dp in pinned_props_list:
                    if prop_dp == '':
                        continue
                    dp_pb = prop_dp.split('][')[0] + ']'
                    
                    dp_pb_resolved = rig.path_resolve(dp_pb)
                    prop_name = prop_dp.split(']["')[1][:-2]
                    row = col.row(align=True)
                    row.prop(dp_pb_resolved, '["'+prop_name+'"]')
                    btn = row.operator(ARP_OT_property_pin.bl_idname, text='', icon='PINNED')
                    btn.state = False
                    btn.prop = prop_name
                    btn.prop_dp_pb = dp_pb
                    
                col.separator()
                
        if len(active_bone.keys()):
            for prop_name in active_bone.keys():
                if prop_name.startswith('_RNA_'):
                    continue
                row = col.row(align=True)
                row.prop(active_bone, '["'+prop_name+'"]')
                btn = row.operator(ARP_OT_property_pin.bl_idname, text='', icon='UNPINNED')
                btn.state = True
                btn.prop = prop_name
        

 
class ARP_PT_RigProps_Settings(Panel, ArpRigToolsPanel):
    bl_label = "Settings"
    bl_parent_id = "ARP_PT_RigProps"

    @classmethod
    def poll(self, context):
        if context.mode != 'POSE':
            return False
        else:
            if context.active_object.data.get("rig_id") != None:
                return True
    
    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene
        rig = context.active_object
        
        try:
            active_bone = context.selected_pose_bones[0]#context.active_pose_bone
            selected_bone_name = active_bone.name
        except:
            return

        # Get bone side
        bone_side = get_bone_side(selected_bone_name)
        
        # Spine
        if is_selected('c_spine_', selected_bone_name, startswith=True):
            c_root_master_pb = get_pose_bone('c_root_master.x')
            if c_root_master_pb and 'spine_stretch_volume' in c_root_master_pb.keys():
                col = layout.column(align=True)
                col.prop(c_root_master_pb, '["spine_stretch_volume"]', text='Spine Stretch')
            
       # Leg
        if (is_selected(fk_leg, selected_bone_name) or is_selected(ik_leg, selected_bone_name)):
            
            c_foot_ik = get_pose_bone("c_foot_ik"+bone_side)
            c_foot_fk = get_pose_bone("c_foot_fk"+bone_side)
            
            # IK-FK Switch
            col = layout.column(align=True)
            row = col.row(align=True)
            row.operator(ARP_OT_switch_snap.bl_idname, text="Snap IK-FK")

            row.prop(scn, "show_ik_fk_advanced", text="", icon="SETTINGS")
            col.prop(c_foot_ik, '["ik_fk_switch"]', text="IK-FK Switch", slider=True)

            if scn.show_ik_fk_advanced:
                col.operator("pose.arp_leg_fk_to_ik_", text="Snap IK > FK")     
                col.operator("pose.arp_leg_ik_to_fk_", text="Snap FK > IK")                           
                col.operator("pose.arp_bake_leg_fk_to_ik", text="Bake IK > FK...")
                col.operator("pose.arp_bake_leg_ik_to_fk", text="Bake FK > IK...")
                
            layout.separator() 
            
            c_thighb = get_pose_bone("c_thigh_b"+bone_side)
            
            if is_selected(fk_leg, selected_bone_name):
                # FK Lock property               
                if 'thigh_lock' in c_thighb.keys():
                    layout.prop(c_thighb, '["thigh_lock"]', text="Leg Lock", slider=True)
                    
                # Stretch length property
                layout.prop(c_foot_fk, '["stretch_length"]', text="Stretch Length (FK)", slider=True)
                
            if is_selected(ik_leg, selected_bone_name):                
                layout.prop(c_foot_ik, '["stretch_length"]', text="Stretch Length (IK)", slider=True)                
                layout.prop(c_foot_ik, '["auto_stretch"]', text="Auto Stretch", slider=True)
                # 3 bones IK
                if "three_bones_ik" in c_foot_ik.keys():
                    layout.prop(c_foot_ik, '["three_bones_ik"]' , text="3 Bones IK", slider=True)
                    
                    
            # Twist tweak            
            if "thigh_twist" in c_thighb.keys():# backward-compatibility
                layout.prop(c_thighb, '["thigh_twist"]', text="Thigh Twist", slider=True)
            
            # Fix_roll prop
            layout.prop(c_foot_ik, '["fix_roll"]', text="Fix Roll", slider=True)            


            if is_selected(ik_leg, selected_bone_name):
                if "pole_parent" in get_pose_bone("c_leg_pole" + bone_side).keys():
                    # IK Pole parent
                    col = layout.column(align=True)
                    op = col.operator("pose.arp_snap_pole", text = "Snap Pole Parent")
                    col.prop(get_pose_bone("c_leg_pole" + bone_side), '["pole_parent"]', text="Pole Parent", slider=True)

            # Pin Snap
            layout.separator()
            col = layout.column(align=True)
            p = col.operator("pose.arp_snap_pin", text="Snap Pinning")
            # Pinning
            col.prop(get_pose_bone("c_stretch_leg"+ bone_side), '["leg_pin"]', text="Knee Pinning", slider=True)


        # Arm
        if is_selected(fk_arm, selected_bone_name) or is_selected(ik_arm, selected_bone_name):
        
            # IK-FK Switch
            col = layout.column(align=True)
            row = col.row(align=True)
            row.operator(ARP_OT_switch_snap.bl_idname, text="Snap IK-FK")

            row.prop(scn, "show_ik_fk_advanced", text="", icon="SETTINGS")
            col.prop(get_pose_bone("c_hand_ik" + bone_side), '["ik_fk_switch"]', text="IK-FK Switch", slider=True)

            if scn.show_ik_fk_advanced:
                col.operator("pose.arp_arm_fk_to_ik_", text="Snap IK > FK")
                col.operator("pose.arp_arm_ik_to_fk_", text="Snap FK > IK")
                col.operator("pose.arp_bake_arm_fk_to_ik", text="Bake IK > FK...")
                col.operator("pose.arp_bake_arm_ik_to_fk", text="Bake FK > IK...")
            
            layout.separator() 
            
            if is_selected(fk_arm, selected_bone_name):
                # FK Lock property
                c_shoulder = get_pose_bone("c_shoulder" + bone_side)
                if 'arm_lock' in c_shoulder.keys():
                    layout.prop(c_shoulder, '["arm_lock"]', text="Arm Lock", slider=True)
                # stretch length property
                layout.prop(get_pose_bone("c_hand_fk" + bone_side), '["stretch_length"]', text="Stretch Length (FK)", slider=True)
            if is_selected(ik_arm, selected_bone_name):
                layout.prop(get_pose_bone("c_hand_ik" + bone_side), '["stretch_length"]', text="Stretch Length (IK)", slider=True)
                # Auto_stretch ik
                layout.prop(get_pose_bone("c_hand_ik" + bone_side), '["auto_stretch"]', text="Auto Stretch", slider=True)
                
            # Twist tweak
            c_shoulder = get_pose_bone("c_shoulder"+bone_side)
            if "arm_twist" in c_shoulder.keys():# backward-compatibility
                layout.prop(c_shoulder, '["arm_twist"]', text="Arm Twist", slider=True)


            if is_selected(ik_arm, selected_bone_name):
                # IK Pole parent
                if "pole_parent" in get_pose_bone("c_arms_pole" + bone_side).keys():
                    col = layout.column(align=True)
                    op = col.operator("pose.arp_snap_pole", text = "Snap Pole Parent")
                    col.prop(get_pose_bone("c_arms_pole" + bone_side), '["pole_parent"]', text="Pole Parent", slider=True)

            # Pin Snap
            layout.separator()
            col = layout.column(align=True)
            col.operator("pose.arp_snap_pin", text="Snap Pinning")
            # Pinning
            col.prop(get_pose_bone("c_stretch_arm"+ bone_side), '["elbow_pin"]', text="Elbow Pinning", slider=True)

        # Eye Aim
        if is_selected(eye_aim_bones, selected_bone_name):
            layout.prop(get_pose_bone("c_eye_target" + bone_side[:-2] + '.x'), '["eye_target"]', text="Eye Target", slider=True)


        # Auto-eyelid
        for eyel in auto_eyelids_bones:
            if is_selected(eyel + bone_side, selected_bone_name):
                eyeb = get_pose_bone("c_eye" + bone_side)
                #retro compatibility, check if property exists
                if len(eyeb.keys()) > 0:
                    if "auto_eyelid" in eyeb.keys():
                        layout.separator()
                        layout.prop(get_pose_bone("c_eye" + bone_side), '["auto_eyelid"]', text="Auto-Eyelid", slider=True)


        # Fingers
        if is_selected(fingers_start, selected_bone_name, startswith=True):
            finger_type = None
            for type in fingers_type_list:
                if type in selected_bone_name:
                    finger_type = type
                    break

            layout.label(text=finger_type.title()+" "+bone_side+":")

            finger_root = get_pose_bone("c_"+finger_type+"1_base"+bone_side)

            # Fingers IK-FK switch
            if "ik_fk_switch" in finger_root.keys():
                col = layout.column(align=True)
                col.operator(ARP_OT_switch_snap.bl_idname, text="Snap IK-FK")
                col.prop(finger_root, '["ik_fk_switch"]', text="IK-FK", slider=True)
                row = col.row(align=True).split(factor=0.7, align=True)
                btn = row.operator(ARP_OT_switch_all_fingers.bl_idname, text="Snap All to IK")
                btn.state = "IK"
                btn.side = bone_side
                btn = row.operator(ARP_OT_switch_all_fingers.bl_idname, text="FK")
                btn.state = "FK"
                btn.side = bone_side

                col = layout.column(align=True)
                col.operator(ARP_OT_switch_snap_root_tip.bl_idname, text="Snap Root-Tip")
                col.prop(finger_root, '["ik_tip"]', text="IK Root-Tip", slider=True)
                row = col.row(align=True).split(factor=0.7, align=True)
                btn = row.operator(ARP_OT_switch_snap_root_tip_all.bl_idname, text="Snap All to Root")
                btn.state = "ROOT"
                btn.side = bone_side
                btn = row.operator(ARP_OT_switch_snap_root_tip_all.bl_idname, text="Tip")
                btn.state = "TIP"
                btn.side = bone_side

                col.separator()

                col.operator(ARP_OT_free_parent_ik_fingers.bl_idname, text="Toggle All IK Parents").side = bone_side

                layout.separator()

            # Fingers Bend
            layout.prop(finger_root, '["bend_all"]', text="Bend All Phalanges", slider=True)


        # Fingers Grasp
        if is_selected(hands_ctrl, selected_bone_name):
            if 'fingers_grasp' in get_pose_bone("c_hand_fk" + bone_side).keys():#if property exists, retro-compatibility check
                layout.label(text="Fingers:")
                layout.prop(get_pose_bone("c_hand_fk" + bone_side),  '["fingers_grasp"]', text = "Fingers Grasp", slider = False)


        # Pinning
        pin_arms = ["c_stretch_arm_pin", "c_stretch_arm_pin", "c_stretch_arm", "c_stretch_arm"]
        if is_selected(pin_arms, selected_bone_name):
            if (selected_bone_name[-2:] == ".l"):
                layout.label(text="Left Elbow Pinning")
                layout.prop(get_pose_bone("c_stretch_arm"+ bone_side), '["elbow_pin"]', text="Elbow pinning", slider=True)
            if (selected_bone_name[-2:] == ".r"):
                layout.label(text="Right Elbow Pinning")
                layout.prop(get_pose_bone("c_stretch_arm"+bone_side), '["elbow_pin"]', text="Elbow pinning", slider=True)

        pin_legs = ["c_stretch_leg_pin", "c_stretch_leg_pin", "c_stretch_leg", "c_stretch_leg"]


        if is_selected(pin_legs, selected_bone_name):
            if (selected_bone_name[-2:] == ".l"):
                layout.label(text="Left Knee Pinning")
                layout.prop(get_pose_bone("c_stretch_leg"+bone_side), '["leg_pin"]', text="Knee pinning", slider=True)
            if (selected_bone_name[-2:] == ".r"):
                layout.label(text="Right Knee Pinning")
                layout.prop(get_pose_bone("c_stretch_leg"+bone_side), '["leg_pin"]', text="Knee pinning", slider=True)


        # Head Lock
        if is_selected('c_head' + bone_side, selected_bone_name):
            head_pbone = get_pose_bone('c_head' + bone_side)
            if len(head_pbone.keys()) > 0:
                if 'head_free' in head_pbone.keys():#retro compatibility
                    col = layout.column(align=True)
                    op = col.operator(ARP_OT_snap_head.bl_idname, text="Snap Head Lock")
                    col.prop(context.selected_pose_bones[0], '["head_free"]', text = 'Head Lock', slider = True)
            neck_pbone = get_pose_bone("c_neck"+bone_side)
            if len(neck_pbone.keys()) > 0:
                if "neck_global_twist" in neck_pbone.keys():
                    col = layout.column(align=True)
                    col.prop(neck_pbone, '["neck_global_twist"]', text = 'Neck Global Twist', slider = False)

        # Neck
        if selected_bone_name.startswith("c_neck") or selected_bone_name.startswith("c_subneck_"):
            if len(active_bone.keys()):
                if "neck_twist" in active_bone.keys():
                    col = layout.column(align=True)
                    neck_pbone = get_pose_bone("c_neck"+bone_side)
                    if len(neck_pbone.keys()):
                        if "neck_global_twist" in neck_pbone.keys():
                            col = layout.column(align=True)
                            col.prop(neck_pbone, '["neck_global_twist"]', text = 'Neck Global Twist', slider = False)

                    col.prop(active_bone, '["neck_twist"]', text = 'Neck Twist', slider = False)


        # Lips Retain
        if is_selected('c_jawbone'+bone_side, selected_bone_name):
            if len(get_pose_bone('c_jawbone'+bone_side).keys()):
                if 'lips_retain' in get_pose_bone('c_jawbone'+bone_side).keys():#retro compatibility
                    layout.prop(get_pose_bone("c_jawbone"+bone_side), '["lips_retain"]', text='Lips Retain', slider=True)
                    layout.prop(get_pose_bone("c_jawbone"+bone_side), '["lips_stretch"]', text='Lips Stretch', slider=True)
                if 'lips_sticky_follow' in get_pose_bone('c_jawbone'+bone_side).keys():#retro compatibility
                    layout.prop(get_pose_bone("c_jawbone"+bone_side), '["lips_sticky_follow"]', text='Lips Follow', slider=True)

        # Spline IK
        if is_selected("c_spline_", selected_bone_name, startswith=True) or is_selected_prop(active_bone, "arp_spline"):
            layout.label(text="Spline IK")
            spline_name = selected_bone_name.split('_')[1]
            if active_bone.bone.keys() and "arp_spline" in active_bone.bone.keys():
                spline_name = active_bone.bone['arp_spline']

            if len(active_bone.keys()):
                if "twist" in active_bone.keys():
                    layout.prop(active_bone, '["twist"]', text="Twist")

            spline_root = get_pose_bone("c_" + spline_name + "_root" + bone_side)

            if spline_root:
                str = "None"
                if spline_root["y_scale"] == 1:
                    str = "Fit Curve"
                elif spline_root["y_scale"] == 2:
                    str = "Bone Original"
                layout.label(text="Y Scale:")
                layout.prop(spline_root, '["y_scale"]', text = str)

                str = "None"
                if spline_root["stretch_mode"] == 1:
                    str = "Bone Original"
                elif spline_root["stretch_mode"] == 2:
                    str = "Inverse Scale"
                elif spline_root["stretch_mode"] == 3:
                    str = "Volume Preservation"
                layout.label(text="XZ Scale:")
                layout.prop(spline_root, '["stretch_mode"]', text = str)

                layout.prop(spline_root, '["volume_variation"]', text = 'Volume Variation')


        # Child Of switcher        
        col = layout.column(align=True)
        col.separator()
        row = col.row(align=True)
        row.operator('arp.childof_switcher', text="Snap Child Of...", icon='CON_CHILDOF')        
        row.operator('arp.childof_keyer', text="", icon='KEY_HLT')
        #row.prop(scn, 'show_snap_child_advanced', text="", icon='SETTINGS')
        
        
        # Reset
        layout.separator()
        col = layout.column(align=True)
        col.operator(ARP_OT_reset_script.bl_idname, text="Reset All Pose")

        # Multi Limb display
        if is_selected('c_pos', selected_bone_name):
            layout.label(text='Multi-Limb Display:')
            #look for multi limbs

            if len(get_pose_bone('c_pos').keys()) > 0:
                for key in get_pose_bone('c_pos').keys():

                    if 'leg' in key or 'arm' in key:
                        row = layout.column(align=True)
                        b = row.operator('id.toggle_multi', text=key)
                        if 'leg' in key:
                            b.limb = 'leg'
                        if 'arm' in key:
                            b.limb = 'arm'
                        b.id = key[-5:]
                        b.key = key
                        row.prop(get_pose_bone('c_pos'), '["'+key+'"]', text=key)

            else:
                layout.label(text='No Multiple Limbs')     

                          
         
class ARP_PT_RigProps_SetPickerCam(Panel, ArpRigToolsPanel):
    bl_label = "Picker"
    bl_parent_id = "ARP_PT_RigProps"   
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(self, context):
        if context.mode != 'POSE':
            return False
        else:
            if context.active_object.data.get("rig_id") != None:
                return True
    
    def draw(self, context):
        layout = self.layout    
        col = layout.column(align=True)
        col.operator(ARP_OT_set_picker_camera_func.bl_idname, text="Set Picker Cam")#, icon = 'CAMERA_DATA')
        
        
class ARP_PT_RigProps_Utils(Panel, ArpRigToolsPanel):
    bl_label = "Rotation Mode Convertor"
    bl_parent_id = "ARP_PT_RigProps"   
    bl_options = {'DEFAULT_CLOSED'}
       
    @classmethod    
    def poll(self, context):
        return context.mode == 'POSE'
   
    def draw(self, context):
        layout = self.layout   
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator(ARP_OT_rotation_mode_convert.bl_idname, text="To Quaternions").mode = "rotation_quaternion"
        row.operator(ARP_OT_rotation_mode_convert.bl_idname, text="To Euler").mode = "rotation_euler"
        
           


###########  REGISTER  ##################
classes = (ARP_PT_RigProps, ARP_PT_RigProps_LayerSets, ARP_PT_BoneCustomProps, ARP_PT_RigProps_Settings, ARP_PT_RigProps_SetPickerCam,
        ARP_PT_RigProps_Utils, ARP_OT_snap_head, ARP_OT_set_picker_camera_func, ARP_OT_toggle_multi, ARP_OT_arp_snap_pole, 
        ARP_OT_arm_bake_fk_to_ik, ARP_OT_arm_fk_to_ik, ARP_OT_arm_bake_ik_to_fk, ARP_OT_arm_ik_to_fk, ARP_OT_switch_snap, 
        ARP_OT_leg_fk_to_ik, ARP_OT_leg_bake_fk_to_ik,  ARP_OT_leg_ik_to_fk, ARP_OT_leg_bake_ik_to_fk, ARP_OT_snap_pin, 
        ARP_OT_reset_script, ARP_OT_toggle_layers, ARP_OT_free_parent_ik_fingers, ARP_OT_switch_all_fingers, ARP_OT_switch_snap_root_tip, 
        ARP_OT_switch_snap_root_tip_all, 
        ARP_UL_layers_sets_list, ObjectSet, LayerSet, 
        ARP_OT_layers_sets_add, ARP_OT_layers_sets_remove, ARP_OT_layers_sets_move, ARP_MT_layers_sets_menu, ARP_MT_layers_sets_menu_import, 
        ARP_MT_layers_sets_menu_export, ARP_OT_layers_set_import, ARP_OT_layers_set_import_preset, ARP_OT_layers_set_export, ARP_OT_layers_set_export_preset, 
        ARP_OT_layers_sets_all_toggle, ARP_OT_layers_add_defaults, ARP_PT_layers_sets_edit, ARP_OT_layers_sets_add_object, 
        ARP_OT_layers_sets_clear_objects, ARP_OT_layers_sets_add_bones, ARP_OT_layers_sets_remove_bones, 
        ARP_OT_rotation_mode_convert, ARP_OT_property_pin, ARP_OT_childof_switcher, ARP_OT_childof_keyer)


def update_arp_tab():
    interface_classes = (ARP_PT_RigProps, ARP_PT_RigProps_LayerSets, ARP_PT_BoneCustomProps, ARP_PT_RigProps_Settings, ARP_PT_RigProps_SetPickerCam, ARP_PT_RigProps_Utils)
    for cl in interface_classes:
        try:
            bpy.utils.unregister_class(cl)     
        except:
            pass
        
    ArpRigToolsPanel.bl_category = bpy.context.preferences.addons[__package__.split('.')[0]].preferences.arp_tools_tab_name
    
    for cl in interface_classes:       
        bpy.utils.register_class(cl)
        
        
def update_layers_set_presets():
    presets_directory = bpy.context.preferences.addons[__package__.split('.')[0]].preferences.rig_layers_path
    
    if not (presets_directory.endswith("\\") or presets_directory.endswith('/')):
        presets_directory += '/'

    try:
        os.listdir(presets_directory)
    except:
        #print("The rig layers presets directory seems invalid:", presets_directory)
        return
    
    for file in os.listdir(presets_directory):
        if not file.endswith(".py"):
            continue
            
        preset_name = file.replace('.py', '')
        
        if preset_name in ARP_MT_layers_sets_menu_import.custom_presets:
            continue

        ARP_MT_layers_sets_menu_import.custom_presets.append(preset_name)


def register():
    from bpy.utils import register_class

    for cls in classes:      
        register_class(cls)
            

    update_arp_tab()
    update_layers_set_presets()
    
    bpy.app.handlers.frame_change_post.append(rig_layers_anim_update)
    
    if bpy.app.version >= (2,90,0):
        bpy.types.Object.layers_sets = CollectionProperty(type=LayerSet, name="Layers Set", description="List of bones layers set", override=get_override_dict_compat())
        bpy.types.Object.layers_sets_idx = IntProperty(name="List Index", description="Index of the layers set list", default=0, override={'LIBRARY_OVERRIDABLE'})
    else:# no overrides before 290
        bpy.types.Object.layers_sets = CollectionProperty(type=LayerSet, name="Layers Set", description="List of bones layers set")
        bpy.types.Object.layers_sets_idx = IntProperty(name="List Index", description="Index of the layers set list", default=0)
        
    bpy.types.Scene.show_ik_fk_advanced = BoolProperty(name="Show IK-FK operators", description="Show IK-FK manual operators", default=False)
    bpy.types.Scene.show_snap_child_advanced = BoolProperty(name="Show Snap Child Of operators", description="Show Snap Child Of operators", default=False)
    bpy.types.Scene.arp_layers_set_render = BoolProperty(name="Set Render Visibility", description="Set objects visibility for rendering as well (not only viewport)", default=False)  
    bpy.types.Scene.arp_layers_show_exclu = BoolProperty(name="Show Exclusive Toggle", description="Show the exclusive visibility toggle of rig layers")
    bpy.types.Scene.arp_layers_show_select = BoolProperty(name="Show Select Toggle", description="Show the select toggle of rig layers")
    bpy.types.Scene.arp_layers_animated = BoolProperty(name="Animated Layers", description="Update animated rig layers visibility on each frame")   
    

def unregister():
    from bpy.utils import unregister_class

    for cls in classes:
        try:
            unregister_class(cls)
        except:
            pass
        
    bpy.app.handlers.frame_change_post.remove(rig_layers_anim_update) 

    del bpy.types.Object.layers_sets
    del bpy.types.Object.layers_sets_idx
    del bpy.types.Scene.show_ik_fk_advanced
    del bpy.types.Scene.show_snap_child_advanced
    del bpy.types.Scene.arp_layers_set_render
    del bpy.types.Scene.arp_layers_show_exclu
    del bpy.types.Scene.arp_layers_show_select    
    del bpy.types.Scene.arp_layers_animated    
    
    