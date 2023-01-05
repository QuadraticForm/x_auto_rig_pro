import bpy

def update_all_tab_names(self, context):
    try:
        from . import auto_rig, auto_rig_ge, auto_rig_smart, auto_rig_remap, rig_functions
        auto_rig.update_arp_tab()
        auto_rig_ge.update_arp_tab()
        auto_rig_smart.update_arp_tab()
        auto_rig_remap.update_arp_tab()
        rig_functions.update_arp_tab()
    except:
        pass
        

class ARP_MT_arp_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    arp_tab_name : bpy.props.StringProperty(name='Interface Tab', description='Name of the tab to display the interface in', default='ARP', update=update_all_tab_names)
    arp_tools_tab_name : bpy.props.StringProperty(name='Tools Interface Tab', description='Name of the tab to display the tools (IK-FK snap...) interface in', default='Tool', update=update_all_tab_names)
    custom_limb_path: bpy.props.StringProperty(name='Custom Limbs Path', subtype='FILE_PATH', default='/Custom Limbs/', description='Path to store custom limb presets')
    rig_layers_path: bpy.props.StringProperty(name='Rig Layers Path', subtype='FILE_PATH', default='/Rig Layers/', description='Path to store rig layers presets')
    remap_presets_path: bpy.props.StringProperty(name='Remap Presets Path', subtype='FILE_PATH', default='/Remap Presets/', description='Path to store remap presets')
    default_ikfk_arm: bpy.props.EnumProperty(items=(('IK', 'IK', 'IK'), ('FK', 'FK', 'FK')), description='Default value for arms IK-FK switch', name='IK-FK Arms Default')
    default_ikfk_leg: bpy.props.EnumProperty(items=(('IK', 'IK', 'IK'), ('FK', 'FK', 'FK')), description='Default value for legs IK-FK switch', name='IK-FK Legs Default')
    default_head_lock: bpy.props.BoolProperty(default=True, name='Head Lock Default', description='Default value for the Head Lock switch')
    
    
    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text='Default:')
        col.prop(self, 'default_ikfk_arm', text='IK-FK Arms')
        col.prop(self, 'default_ikfk_leg', text='IK-FK Legs')
        col.prop(self, 'default_head_lock', text='Head Lock')
        
        col.separator()
        col.label(text='Interface:')
        col.prop(self, 'arp_tab_name', text='Main ARP Tab')
        col.prop(self, 'arp_tools_tab_name', text='Tools Tab') 

        col.separator()
        col.label(text='Paths:')
        col.prop(self, 'custom_limb_path')
        col.prop(self, 'rig_layers_path')
        col.prop(self, 'remap_presets_path')
        
        col.separator()
        col.label(text='Special:')
        col.prop(context.scene, 'arp_debug_mode')
        col.prop(context.scene, 'arp_experimental_mode')
        
        
        

def register():
    from bpy.utils import register_class

    try:
        register_class(ARP_MT_arp_addon_preferences)
    except:
        pass
    bpy.types.Scene.arp_debug_mode = bpy.props.BoolProperty(name='Debug Mode', default = False, description = 'Run the addon in debug mode (should be enabled only for debugging purposes, not recommended for a normal usage)')
    bpy.types.Scene.arp_experimental_mode = bpy.props.BoolProperty(name='Experimental Mode', default = False, description = 'Enable experimental, unstable tools. Warning, can lead to errors. Use it at your own risks.')
    
def unregister():
    from bpy.utils import unregister_class
    unregister_class(ARP_MT_arp_addon_preferences)

    del bpy.types.Scene.arp_debug_mode
    del bpy.types.Scene.arp_experimental_mode
