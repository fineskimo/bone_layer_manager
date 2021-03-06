import bpy

from bpy.props import IntProperty, StringProperty


class CREATEID_OT_name(bpy.types.Operator):
    # Assign and store a name for this layer as ID prop
    bl_idname = "bone_layer_man.layout_do_name"
    bl_label = "Assign Name"
    bl_description = "Assign and store a name for this layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_idx: IntProperty(name="Layer Index",
                           description="Index of the layer to be named",
                           default=0, min=0, max=31)

    layer_name: StringProperty(name="Layer Name",
                               description="Name of the layer",
                               default="")

    @classmethod
    def poll(self, context):
        arm = getattr(context.active_object, 'data', None)
        not_link = (getattr(arm, 'library', None) is None)
        return not_link

    def execute(self, context):
        arm = context.active_object.data
        # Create ID prop by setting it
        arm[f"layer_name_{self.layer_idx}"] = self.layer_name

        return {'FINISHED'}
