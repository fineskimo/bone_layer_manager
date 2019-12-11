import bpy
import re

from .blmfuncs import ShowMessageBox

bpy.types.PoseBone.constraint_active_index = bpy.props.IntProperty()

readonly_attr = ['__doc__', '__module__', '__slots__', 'bl_rna', 'error_location',
                 'error_rotation', 'is_proxy_local', 'is_valid', 'rna_type', 'type']

l_names = ['Left', 'left', 'LEFT', 'L', 'l']
r_names = ['Right', 'right', 'RIGHT', 'R', 'r']


def getmirror(side, oside, name):
    # get mirror name from name
    mir_name = name

    for i, value in enumerate(side):
        if value == name:
            mir_name = oside[i]
            break

    return mir_name


def xflip(xname):
    # Flip names
    arm = bpy.context.active_object
    full_mir_prefix = base = full_mir_suffix = number = ""
    l_joined = "|".join(l_names)
    r_joined = "|".join(r_names)

    find_l = r'^((' + l_joined + r')[._\- ])?(.*?)?([._\- ](' + l_joined + r'))?([._\- ]\d+)?$'
    find_r = r'^((' + r_joined + r')[._\- ])?(.*?)?([._\- ](' + r_joined + r'))?([._\- ]\d+)?$'

    l_match = re.match(find_l, xname)
    r_match = re.match(find_r, xname)

    match = l_match if True else r_match

    if match:
        full_prefix = match.group(1) if match.group(1) is not None else ""
        prefix = match.group(2) if match.group(2) is not None else ""
        base = match.group(3) if match.group(3) is not None else ""
        full_suffix = match.group(4) if match.group(4) is not None else ""
        suffix = match.group(5) if match.group(5) is not None else ""
        number = match.group(6) if match.group(6) is not None else ""

        if prefix is not None:
            side = l_names if prefix in l_names else r_names
            oside = l_names if prefix not in l_names else r_names
            mir_prefix = getmirror(side, oside, prefix)
            full_mir_prefix = re.sub(prefix, mir_prefix, full_prefix)

        if suffix is not None:
            side = l_names if suffix in l_names else r_names
            oside = l_names if suffix not in l_names else r_names
            mir_suffix = getmirror(side, oside, suffix)
            full_mir_suffix = re.sub(suffix, mir_suffix, full_suffix)

    mir_name = f'{full_mir_prefix}{base}{full_mir_suffix}{number}'
    # if bone not found return original target
    if arm.pose.bones.get(mir_name) is None:
        ShowMessageBox("Mirror target not found!", "Bone Layer Manager", 'ERROR')
        return xname

    return mir_name


class QC_OT_contraint_action(bpy.types.Operator):
    # Call constraint operators by action

    bl_idname = "bone.constraint_action"
    bl_label = ""

    action: bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('ADD', "Add", ""),
            ('REMOVE', "Remove", ""),
            ('FOLLOW_PATH', "Follow_Path", ""),
            ('OB_SET_INVERSE', "Ob_Set_Inverse", ""),
            ('OB_CLEAR_INVERSE', "Ob_Clear_Inverse", ""),
            ('LD_RESET', "Ld_Reset", ""),
            ('STRETCH_RESET', "Stretch_reset", ""),
            ('ADD_TARGET', "Add_Target", ""),
            ('REMOVE_TARGET', "Remove_Target", ""),
            ('NORMALIZE_TARGET', "Normalize_Target", ""),
            ('CO_SET_INVERSE', "Co_Set_Inverse", ""),
            ('CO_CLEAR_INVERSE', "Co_Set_Inverse", ""),
        )
    )

    @classmethod
    def poll(cls, context):
        return context.selected_pose_bones

    def invoke(self, context, event):
        bone = context.active_pose_bone
        idx = bone.constraint_active_index
        con_count = len(bone.constraints)

        if con_count > 0:
            con = bone.constraints[idx]
            name = con.name
            # set the constraint in the context
            context_py = context.copy()
            context_py["constraint"] = con
        else:
            bone.constraint_active_index = 0

        # general move\add\remove operators
        if self.action == 'DOWN' and idx < con_count - 1:
            if bpy.ops.constraint.move_down(context_py, constraint=name, owner='BONE') == {'FINISHED'}:
                bone.constraint_active_index += 1
        elif self.action == 'UP' and idx > 0:
            if bpy.ops.constraint.move_up(context_py, constraint=name, owner='BONE') == {'FINISHED'}:
                bone.constraint_active_index -= 1
        elif self.action == 'ADD':
            bpy.ops.qconstraint.popup('INVOKE_DEFAULT')
        elif self.action == 'REMOVE' and con_count > 0:
            bone.constraints.remove(con)
            if idx > 0:
                bone.constraint_active_index -= 1
            # remove active index property if exists and not in use
            if con_count == 1 and bone.get('constraint_active_index') is not None:
                del bone["constraint_active_index"]

        # contraint specific operators
        # FOLLOW PATH
        elif self.action == 'FOLLOW_PATH':
            bpy.ops.constraint.followpath_path_animate(context_py, constraint=name, owner='BONE', frame_start=1, length=100)
        # OBJECT SOLVER
        elif self.action == 'OB_SET_INVERSE':
            bpy.ops.constraint.objectsolver_set_inverse(context_py, constraint=name, owner='BONE')
        elif self.action == 'OB_CLEAR_INVERSE':
            bpy.ops.constraint.objectsolver_clear_inverse(context_py, constraint=name, owner='BONE')
        # LIMIT DISTANCE
        elif self.action == 'LD_RESET':
            bpy.ops.constraint.limitdistance_reset(context_py, constraint=name, owner='BONE')
        # STRETCH TO
        elif self.action == 'STRETCH_RESET':
            bpy.ops.constraint.stretchto_reset(context_py, constraint=name, owner='BONE')
        # ARMATURE
        elif self.action == 'ADD_TARGET':
            bpy.ops.constraint.add_target(context_py)
        elif self.action == 'REMOVE_TARGET':
            bpy.ops.constraint.remove_target(context_py)
        elif self.action == 'NORMALIZE_TARGET':
            bpy.ops.constraint.normalize_target_weights(context_py)
        # CHILD OF
        elif self.action == 'CO_SET_INVERSE':
            bpy.ops.constraint.childof_set_inverse(context_py, constraint=name, owner='BONE')
        elif self.action == 'CO_CLEAR_INVERSE':
            bpy.ops.constraint.childof_clear_inverse(context_py, constraint=name, owner='BONE')

        return {"FINISHED"}


class QC_OT_constraint_add(bpy.types.Operator):
    # Add constraint to active bone
    bl_idname = "qconstraint.constraint_add"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add constraint to active bone"

    ctype: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        bone = context.active_pose_bone
        if len(context.selected_pose_bones) > 1:
            bpy.ops.pose.constraint_add_with_targets(type=self.ctype)
        else:
            bpy.ops.pose.constraint_add(type=self.ctype)
        # Redraw required to update QC_UL_conlist
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()
        # Add index if not present
        if bone.get('constraint_active_index') is None:
            bone.constraint_active_index = 0

        return {'FINISHED'}


class QC_OT_constraint_clear(bpy.types.Operator):
    # Clear all contraints
    bl_idname = "qconstraint.constraint_clear"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear all constraints for the selected bones"

    @classmethod
    def poll(self, context):
        bone = context.active_pose_bone
        return len(bone.constraints) > 0 and len(context.selected_pose_bones) > 0

    def execute(self, context):
        bpy.ops.pose.constraints_clear('INVOKE_DEFAULT')
        # Redraw required to update QC_UL_conlist
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()

        # remove index property from all bones
        for bone in context.selected_pose_bones:
            if bone.get('constraint_active_index') is not None:
                del bone["constraint_active_index"]

        return {'FINISHED'}


class QC_OT_remove_target(bpy.types.Operator):
    # Remove the target from the constraint
    bl_idname = "qconstraint.remove_target"
    bl_label = "Remove Target"
    bl_options = {'UNDO', 'INTERNAL'}
    bl_description = "Remove the target from the constraint"

    index: bpy.props.IntProperty()

    def execute(self, context):
        bone = context.active_pose_bone
        idx = bone.constraint_active_index
        constraint = bone.constraints[idx]
        tgts = constraint.targets
        tgts.remove(tgts[self.index])
        return {'FINISHED'}


class QC_OT_disable_keep_transform(bpy.types.Operator):
    """Set the influence of this constraint to zero while """
    """trying to maintain the object's transformation. Other active """
    """constraints can still influence the final transformation"""

    bl_idname = "qconstraint.disable_keep_transform"
    bl_label = "Disable and Keep Transform"
    bl_options = {'UNDO', 'INTERNAL'}
    bl_description = "Disable constraint while maintaining the visual transform."

    @classmethod
    def poll(self, context):
        bone = context.active_pose_bone
        idx = bone.constraint_active_index
        constraint = bone.constraints[idx]

        return constraint and constraint.influence > 0.0

    def execute(self, context):
        bone = context.active_pose_bone
        idx = bone.constraint_active_index
        constraint = bone.constraints[idx]

        is_bone_constraint = True
        ob = context.object
        mat = ob.matrix_world @ bone.matrix
        constraint.influence = 0.0
        bone.matrix = ob.matrix_world.inverted() @ mat

        return {'FINISHED'}


class QC_OT_copyconstraint(bpy.types.Operator):
    # Copy active constraint to selected bones
    bl_idname = "qconstraint.copy"
    bl_label = ""
    bl_description = "Copy active constraint to selected bones"

    @classmethod
    def poll(self, context):
        bone = context.active_pose_bone
        return len(bone.constraints) > 0 and len(context.selected_pose_bones) > 1

    def execute(self, context):

        source_bone = context.active_pose_bone
        idx = source_bone.constraint_active_index
        source_con = source_bone.constraints[idx]
        selected = context.selected_pose_bones[:]
        selected.remove(source_bone)
        string = ""

        for target_bone in selected:
            target = target_bone.constraints.new(source_con.type)

            # assign property if required
            if len(target_bone.constraints) == 1:
                target_bone.constraint_active_index = 0

            for attr in dir(source_con):
                if attr.find(string) != -1 and attr not in readonly_attr:
                    setattr(target, attr, getattr(source_con, attr))

        return {'FINISHED'}


class QC_OT_copyflipx(bpy.types.Operator):
    # Copy active constraint to selected bones (flip x subtarget name)
    bl_idname = "qconstraint.xflipcopy"
    bl_label = ""
    bl_description = "Copy active constraint to selected bones (X axis flip)"

    @classmethod
    def poll(self, context):
        bone = context.active_pose_bone
        return len(bone.constraints) > 0 and len(context.selected_pose_bones) > 1

    def execute(self, context):

        source_bone = context.active_pose_bone
        idx = source_bone.constraint_active_index
        source_con = source_bone.constraints[idx]
        selected = context.selected_pose_bones[:]
        selected.remove(source_bone)
        string = ""

        for target_bone in selected:
            target = target_bone.constraints.new(source_con.type)

            # assign property if required
            if len(target_bone.constraints) == 1:
                target_bone.constraint_active_index = 0

            for attr in dir(source_con):
                if attr.find(string) != -1 and attr not in readonly_attr:
                    if attr == "subtarget":
                        xname = getattr(source_con, attr)
                        setattr(target, attr, xflip(xname))
                    else:
                        setattr(target, attr, getattr(source_con, attr))
                    # print(f'{attr} Copied')

        return {'FINISHED'}


class QC_OT_copyall(bpy.types.Operator):
    # Copy active constraint to selected bones
    bl_idname = "qconstraint.copyall"
    bl_label = ""
    bl_description = "Copy all constraints to selected bones"

    @classmethod
    def poll(self, context):
        bone = context.active_pose_bone
        return len(bone.constraints) > 0 and len(context.selected_pose_bones) > 1

    def execute(self, context):

        source_bone = context.active_pose_bone
        idx = source_bone.constraint_active_index
        selected = context.selected_pose_bones[:]
        selected.remove(source_bone)

        for target_bone in selected:
            # assign property if required
            if len(target_bone.constraints) == 0:
                target_bone.constraint_active_index = 0

        bpy.ops.pose.constraints_copy('INVOKE_DEFAULT')

        return {'FINISHED'}
