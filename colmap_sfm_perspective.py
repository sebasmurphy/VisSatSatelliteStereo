import os
from colmap_sfm_utils import write_template_perspective
import json
import colmap_sfm_commands
from colmap.extract_sfm import extract_camera_dict
import logging
import shutil


def make_subdirs(sfm_dir):
    subdirs = [
                sfm_dir,
                os.path.join(sfm_dir, 'init_triangulate'),
                os.path.join(sfm_dir, 'init_triangulate_ba'),
                os.path.join(sfm_dir, 'init_ba_triangulate')
    ]

    for item in subdirs:
        if not os.path.exists(item):
            os.mkdir(item)


def run_sfm(work_dir, sfm_dir, init_camera_file, weight):
    make_subdirs(sfm_dir)

    with open(init_camera_file) as fp:
        init_camera_dict = json.load(fp)
    with open(os.path.join(sfm_dir, 'init_camera_dict.json'), 'w') as fp:
        json.dump(init_camera_dict, fp, indent=2, sort_keys=True)
    init_template = os.path.join(sfm_dir, 'init_template.json')
    write_template_perspective(init_camera_dict, init_template)

    img_dir = os.path.join(sfm_dir, 'images')
    db_file = os.path.join(sfm_dir, 'database.db')

    colmap_sfm_commands.run_sift_matching(img_dir, db_file, camera_model='PERSPECTIVE')

    out_dir = os.path.join(sfm_dir, 'init_triangulate')
    # colmap_sfm_commands.run_point_triangulation(img_dir, db_file, out_dir, init_template, 1.5, 2, 2)
    colmap_sfm_commands.run_point_triangulation(img_dir, db_file, out_dir, init_template, 2.0, 3.0, 3.0)

    # global bundle adjustment
    in_dir = os.path.join(sfm_dir, 'init_triangulate')
    out_dir = os.path.join(sfm_dir, 'init_triangulate_ba')
    colmap_sfm_commands.run_global_ba(in_dir, out_dir, weight)

    # retriangulate
    camera_dict = extract_camera_dict(out_dir)
    with open(os.path.join(sfm_dir, 'init_ba_camera_dict.json'), 'w') as fp:
        json.dump(camera_dict, fp, indent=2, sort_keys=True)
    init_ba_template = os.path.join(sfm_dir, 'init_ba_template.json')
    write_template_perspective(camera_dict, init_ba_template)

    out_dir = os.path.join(sfm_dir, 'init_ba_triangulate')
    colmap_sfm_commands.run_point_triangulation(img_dir, db_file, out_dir, init_ba_template, 1.5, 2, 2)