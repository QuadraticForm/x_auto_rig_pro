import bpy

def restore_armature_layers(layers_select):
    # must enabling at least one
    bpy.context.active_object.data.layers[layers_select[0]] = True
    # restore the armature layers visibility
    for i in range(0, 32):
        bpy.context.active_object.data.layers[i] = layers_select[i]
        
        
def enable_all_armature_layers():
    # enable all layers
    # and return the list of each layer visibility
    _layers = bpy.context.active_object.data.layers
    layers_select = []
    for i in range(0, 32):
        layers_select.append(_layers[i])
    for i in range(0, 32):
        bpy.context.active_object.data.layers[i] = True

    return layers_select
