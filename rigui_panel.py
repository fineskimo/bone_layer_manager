import bpy

from .blmfuncs import prefs


class BLM_PT_rigui(bpy.types.Panel):
    # Creates a Rig UI Panel for based on the assigned Rig_ui_ID
    bl_category = "Bone Layers"
    bl_label = "Rig UI"
    bl_idname = "BLM_PT_rigui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        if getattr(context.active_object, 'pose', None):
            return True
        for ob in context.selected_objects:  # Check for armature in all objects (Add support for Weight Painting)
            if ob.type == 'ARMATURE':
                return True

    def draw(self, context):
        layout = self.layout
        ac_ob = context.active_object
        objects = (
            # List of selected rigs, starting with the active object (if it's a rig)
            *[o for o in {ac_ob} if o and o.type == 'ARMATURE'],
            *[o for o in context.selected_objects
              if (o != ac_ob and o.type == 'ARMATURE')],
        )

        empty_ui = True
        grid = layout.column()

        for ac_ob in objects:
            arm = ac_ob.data
            rows = {}

            # Iterate through layers finding rows for the Rig UI
            for x in range(33):
                name = arm.get(f"layer_name_{x}", "*NO NAME*")
                if name == "":
                    name = "*NO NAME*"
                layer = arm.get(f"rigui_id_{x}", None)

                if layer is not None and layer in range(33):
                    # If the row hasn't been assigned, create empty list for it
                    row = rows[layer] = rows.get(layer, [])
                    row.append([name, x])

            if not rows:
                continue
            empty_ui = False
            box = grid.column()  # TODO: optionallly align up-down
            split = box.row(align=False).split()

            # Display Rig name
            row = split.row()
            if (len(objects) > 1):
                row.label(text=ac_ob.name, icon='ARMATURE_DATA')

            # Display layer buttons
            for i in sorted(rows):
                row = box.row(align=True)

                for (name, x) in rows[i]:
                    row.prop(arm, 'layers', index=x, toggle=True, text=name)

            # Export button
            row = split.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text="Export UI", translate=False)
            row.operator("bone_layer_man.write_rig_ui", emboss=True, text="", icon='EXPORT')

        if empty_ui:
            layout.label(text="No available UI layers in rigs", icon='INFO')
