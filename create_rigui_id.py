import bpy

from bpy.props import IntProperty


class SETUIID_OT_riguiid(bpy.types.Operator):
    """Assign and store a layer index for this layer as ID prop"""
    bl_idname = "bone_layer_man.rigui_set_id"
    bl_label = "Assign RigUI Layer"
    bl_description = (
        "Assign a layer index for the RigUI.\n"
        "Shift + Click to assign to the previous index.\n"
        "Ctrl + Click to assign one value higher than the previous index"
        )
    bl_options = {'REGISTER', 'UNDO'}

    layer_idx: IntProperty(
        name="Layer Index",
        description="Index of the layer to be named",
        default=0, min=0, max=31)

    rigui_id: IntProperty(
        name="RigUI Layer",
        description="Index of the RigUI layer",
        default=0, min=0, max=31, soft_min=0, soft_max=31)

    rigui_idcount: IntProperty(
        name="RigUI Count",
        description="RigUI layer Counter",
        default=0, min=0, max=31, soft_min=0, soft_max=31)

    @classmethod
    def poll(self, context):
        arm = getattr(context.active_object, 'data', None)
        not_link = (getattr(arm, 'library', None) is None)
        return not_link

    def invoke(self, context, event):
        arm = context.active_object.data
        count = arm.get('rigui_idcount', self.rigui_idcount)

        if event.ctrl:
            # Increment rigui_id
            count += 1
            arm['rigui_idcount'] = count
        elif event.shift:
            # Use same rigui_id
            pass
        else:
            arm['rigui_idcount'] = self.rigui_id

        return self.execute(context)

    def execute(self, context):
        arm = context.active_object.data
        count = arm.get('rigui_idcount', self.rigui_idcount)

        arm[f"rigui_id_{self.layer_idx}"] = count

        return {'FINISHED'}
