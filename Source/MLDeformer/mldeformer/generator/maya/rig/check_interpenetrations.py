from maya import cmds
from maya.api import OpenMaya


def get_dag_path(node, extend_to_shape=False):
    """
    Returns node-name as MDagPath
    """

    selection_list = OpenMaya.MSelectionList()
    try:
        selection_list.add(node)
    except RuntimeError:
        raise RuntimeError('Node not found: "{}"'.format(node))

    # get mesh shape dagpath
    dag_path = selection_list.getDagPath(0)
    
    if extend_to_shape:
        dag_path.extendToShape()

    return dag_path


def get_world_position(dag_path):
    """
    Returns world position as MFloatPoint
    """
    world_matrix = dag_path.inclusiveMatrix()
    return OpenMaya.MFloatPoint(world_matrix.getElement(3,0), world_matrix.getElement(3,1), world_matrix.getElement(3,2))


def get_bone_children(bone):
    """
    Returns bone children as MDagPathArray

    :param bone: Bone path (MDagPath)
    """
    
    children = OpenMaya.MDagPathArray()
    for i in range(bone.childCount()):
        
        child = bone.child(i)
        if child.hasFn(OpenMaya.MFn.kJoint):
            
            fn_child = OpenMaya.MFnDagNode(child)
            dp_child = fn_child.getPath()
            children.append(dp_child)

    return children


def get_face_centers_and_normals(mesh_dag):

    rm_polyiter = OpenMaya.MItMeshPolygon(mesh_dag)
    face_centers = OpenMaya.MFloatPointArray()
    face_normals = OpenMaya.MFloatVectorArray()
    
    while not rm_polyiter.isDone():
        center = rm_polyiter.center(OpenMaya.MSpace.kWorld)
        normal = rm_polyiter.getNormal(OpenMaya.MSpace.kWorld)
        face_centers.append(OpenMaya.MFloatPoint(center))
        face_normals.append(normal)
        rm_polyiter.next()

    return face_centers, face_normals


def set_pose(key_values, ctrl_list, attr_list):
    for i in range(0, len(ctrl_list)):
        cmds.setAttr('{0}.{1}'.format(ctrl_list[i], attr_list[i]), key_values[i])
      

def get_intersecting_bones(collision_mesh, bones, threshold=10):
    '''
    Checks if the bone-hierarchy is colliding against the given mesh.
    A ray will be shoot from each bone to of its children, and check for closest intersection.
    Returns list of intersecting bones. 

    Note: if the bone-hierarchy has a complex leaf structure, it is recommended to create a simplified version of the skeleton.
    Same applies to the mesh, creating a simplified single mesh might work better.
    '''
    
    # get mesh structure
    col_mesh_dag = get_dag_path(collision_mesh, extend_to_shape=True)
    col_fn_mesh = OpenMaya.MFnMesh(col_mesh_dag)
    col_fn_mesh.freeCachedIntersectionAccelerator()
    mesh_accel_params = col_fn_mesh.autoUniformGridParams()
        
    intersecting_bones = set()
    for bone_node in bones:
    
        # get bone position
        bone = get_dag_path(bone_node)
        ray_source = get_world_position(bone)

        # get bone children
        bone_children = get_bone_children(bone)
        
        for i in range(len(bone_children)):
            
            child_position = get_world_position(bone_children[i])
            ray_direction = child_position - ray_source # no need to normalize
            max_param = ray_direction.length()
            
            # get closest intersection
            intersection = col_fn_mesh.closestIntersection(
                ray_source, ray_direction, OpenMaya.MSpace.kWorld, max_param, False,
                idsSorted=False, accelParams=mesh_accel_params, tolerance=1e-6)
            
            if intersection:
                hit_point = intersection[0]

                # make sure ray is under radius
                if (hit_point-ray_source).length() < max_param:                    
                    intersecting_bones.add(bone_node)
            
            # early exit if number of intersecting bones is over threshold.
            if threshold != -1 and len(intersecting_bones) >= threshold:
                return list(intersecting_bones)
            
    return list(intersecting_bones)

  
def get_intersecting_faces(ray_mesh, collision_mesh, calibration_mode=False, calibration_data=[]):

    ray_mesh_dag = get_dag_path(ray_mesh, extend_to_shape=True)
    col_mesh_dag = get_dag_path(collision_mesh, extend_to_shape=True)

    # get rays from mesh
    face_centers, face_normals = get_face_centers_and_normals(ray_mesh_dag)
    
    col_fn_mesh = OpenMaya.MFnMesh(col_mesh_dag)
    col_fn_mesh.freeCachedIntersectionAccelerator()
    mesh_accel_params = col_fn_mesh.autoUniformGridParams()

    intersecting_faces = set()

    for face_id in range(len(face_centers)):
        # raycast for intersections   
        result = col_fn_mesh.allIntersections(face_centers[face_id], face_normals[face_id], OpenMaya.MSpace.kWorld, 
                                             500, False, accelParams=mesh_accel_params)
        if result:
            if calibration_mode and not len(result[0]) % 2 == 0:
                # calibration mode just logs intersection based on odd number of hits to determine a 'default state' of 
                # each vert we cast from.
                intersecting_faces.add(face_id)

            if not calibration_mode:
                # Conditions for logging intersection:
                # vertID is NOT in calibration_data AND odd number of hits recorded
                # vertID is in calibration data AND even number of hits recorded
                if not face_id in calibration_data and not len(result[0]) % 2 == 0: # not in list, and odd numer of hits.
                    intersecting_faces.add(face_id)
                if face_id in calibration_data and len(result[0]) % 2 == 0:  # is in list, and even number of hits...
                    intersecting_faces.add(face_id)

    return list(intersecting_faces)


def create_bone_mesh_test(bone_list, collision_mesh, allowed_collisions):
    """
    Returns a function that returns true if the bones do not intersect with the collision mesh

    :param bone_list: list of bones that make up the skeleton to test
    :param collision_mesh: Path of mesh to collide against.      
    
    Note: if the bone-hierarchy has a complex leaf structure, it is recommended to create a simplified version of the skeleton.
    Same applies to the mesh, creating a simplified single mesh might work better.
    Bones intersecting in rest pose won't be considered.

    """
    
    # initial collision check to calibrate num raycast intersections in ref pose
    intersecting_bones = get_intersecting_bones(collision_mesh, bone_list, threshold=-1)
    if intersecting_bones:
        cmds.warning('Bones intersecting: {}'.format(' '.join(intersecting_bones)))
    bone_list = list(set(bone_list) - set(intersecting_bones))
    if not bone_list:
        cmds.warning('All bones are intersecting')

    def valid_pose_test(rnd_attr_values, ctrl_list, attr_list):
        set_pose(rnd_attr_values, ctrl_list, attr_list)
        # test generated pose for intersection
        intersecting_bones = get_intersecting_bones(collision_mesh, bone_list, threshold=allowed_collisions)
        return len(intersecting_bones) < allowed_collisions
        
    return valid_pose_test


def create_ray_mesh_test(ray_mesh, collision_mesh, allowed_collisions):
    """
     Returns a function that returns true rays cast from the center of ray mesh faces intersect with the collision mesh
     in a different odd / even pattern than during the bind pose.  
    
    :param bone_list: bones to collide against mesh.  Only intersection between the parent and child count. 
    :param collision_mesh: Path of mesh to collide against.  
    """

    # initial collision check to calibrate num raycast intersections in ref pose
    calibration_data = get_intersecting_faces(ray_mesh, collision_mesh, calibration_mode=True)
    
    def valid_pose_test(rnd_attr_values, ctrl_list, attr_list):
        set_pose(rnd_attr_values, ctrl_list, attr_list)
        # test generated pose for intersection
        intersecting_faces = get_intersecting_faces(ray_mesh, collision_mesh, calibration_mode=False,
                                                calibration_data=calibration_data)
        return len(intersecting_faces) < allowed_collisions

    return valid_pose_test

