import os
import trimesh
import numpy as np
import multiprocessing
import point_cloud_utils as pcu

from tqdm import tqdm
from typing import Union, Tuple
from deep_sdf.src import utils
from deep_sdf.src.config import Configuration


class DataCreatorHelper:
    MIN_BOUND = "min_bound"
    CENTER = "center"
    CENTER_WITHOUT_Z = "center_without_z"

    TYPES = Union[MIN_BOUND, CENTER, CENTER_WITHOUT_Z]

    @staticmethod
    def load_mesh_and_compute_max_norm(
        path: str,
        map_z_to_y: bool = False,
        check_watertight: bool = True,
        translate_mode: TYPES = CENTER_WITHOUT_Z,
        save_html: bool = False,
    ) -> Tuple[trimesh.Trimesh, float]:
        """
        Load mesh and compute max norm

        Args:
            path (str): mesh path
            map_z_to_y (bool, optional): swap y and z axes. Defaults to False.
            check_watertight (bool, optional): ensure the mesh is watertight. Defaults to True.
            translate_mode (Union[MIN_BOUND, CENTER, CENTER_WITHOUT_Z], optional): Defaults to CENTER_WITHOUT_Z.
            save_html (bool, optional): Defaults to False.

        Returns:
            Tuple[trimesh.Trimesh, float]: mesh, max norm
        """

        print(path, "\n")

        mesh = DataCreatorHelper.load_mesh(
            path,
            normalize=False,
            map_z_to_y=map_z_to_y,
            check_watertight=check_watertight,
            translate_mode=translate_mode,
        )

        if not mesh.is_watertight:
            print(f"{path} is not watertight")

        length = np.max(np.linalg.norm(mesh.vertices, axis=1))

        if save_html:
            utils.commonutils.add_debugvisualizer(globals())

            save_name = os.path.basename(path).replace(".obj", ".html")
            print(f"saving: {save_name}")

            globals()["Plotter"](
                mesh,
                globals()["geometry"].Point(mesh.vertices[np.argmax(np.linalg.norm(mesh.vertices, axis=1))]),
                globals()["geometry"].Point(0, 0),
                map_z_to_y=False,
            ).save(save_name)

        return mesh, length

    @staticmethod
    def get_normalized_mesh(_mesh: trimesh.Trimesh, max_length: float = None) -> trimesh.Trimesh:
        """Normalize to 0 ~ 1 values the given mesh

        Args:
            mesh (trimesh.Trimesh): Given mesh to normalize

        Returns:
            trimesh.Trimesh: Normalized mesh
        """

        mesh = _mesh.copy()

        if max_length is not None:
            length = max_length
        else:
            length = np.max(np.linalg.norm(mesh.vertices, axis=1))

        mesh.vertices = mesh.vertices * (1.0 / length)

        return mesh

    @staticmethod
    def get_closed_mesh(_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Attempt to close an open mesh by filling holes.

        Args:
            mesh (trimesh.Trimesh): The open mesh to close.

        Returns:
            trimesh.Trimesh: The potentially closed mesh.
        """

        mesh = _mesh.copy()
        mesh.fill_holes()

        return mesh

    @staticmethod
    def sample_pts(
        mesh: trimesh.Trimesh,
        n_surface_sampling: int,
        n_bbox_sampling: int,
        n_volume_sampling: int,
        sigma: float = 0.01,
        with_surface_points_noise: bool = True,
    ) -> np.ndarray:
        """
        Sample a given number of points uniformly from the surface of a mesh.

        Args:
            mesh (trimesh.Trimesh): The mesh from which to sample points.
            n_surface_sampling (int): The number of points to sample from the surface.
            n_bbox_sampling (int): The number of points to sample from the bounding box.
            n_volume_sampling (int): The number of points to sample from the volume.

        Returns:
            np.ndarray: An array of sampled points (shape: [num_samples, 3]).
        """

        if not with_surface_points_noise:
            sigma = 0

        surface_points_sampled, _ = trimesh.sample.sample_surface(mesh, n_surface_sampling)
        surface_points_sampled += np.random.normal(0, sigma, surface_points_sampled.shape)

        bbox_points_sampled = np.random.uniform(low=mesh.bounds[0], high=mesh.bounds[1], size=[n_bbox_sampling, 3])

        volume_points_sampled = np.random.rand(n_volume_sampling, 3)

        xyz = np.concatenate([surface_points_sampled, bbox_points_sampled, volume_points_sampled], axis=0)

        return xyz

    @staticmethod
    def load_mesh(
        path: str,
        normalize: bool = False,
        map_z_to_y: bool = False,
        check_watertight: bool = True,
        max_length: float = None,
        translate_mode: TYPES = CENTER_WITHOUT_Z,
    ) -> trimesh.Trimesh:
        """Load mesh data from .obj file

        Args:
            path (str): Path to load
            normalize (bool, optional): Whether normalizing mesh. Defaults to False.
            map_y_to_z (bool, optional): Change axes (y to z, z to y). Defaults to False.

        Returns:
            trimesh.Trimesh: Loaded mesh
        """

        mesh = trimesh.load(path)

        if isinstance(mesh, trimesh.Scene):
            geo_list = []
            for g in mesh.geometry.values():
                geo_list.append(g)
            mesh = trimesh.util.concatenate(geo_list)

        mesh.fix_normals(multibody=True)

        if check_watertight and not mesh.is_watertight:
            vertices, faces = pcu.make_mesh_watertight(mesh.vertices, mesh.faces, resolution=100000)
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        if map_z_to_y:
            mesh.vertices[:, [1, 2]] = mesh.vertices[:, [2, 1]]

        if translate_mode == DataCreatorHelper.MIN_BOUND:
            vector = mesh.bounds[0]
        elif translate_mode == DataCreatorHelper.CENTER:
            vector = np.mean(mesh.vertices, axis=0)
        elif translate_mode == DataCreatorHelper.CENTER_WITHOUT_Z:
            vector = mesh.bounds.sum(axis=0) * 0.5
            vector[2] = mesh.bounds[0][2]
        else:
            raise ValueError(f"Invalid translate mode: {translate_mode}")

        mesh.vertices -= vector

        if normalize:
            mesh = DataCreatorHelper.get_normalized_mesh(mesh, max_length=max_length)

        mesh.path = path

        return mesh


class DataCreator(DataCreatorHelper):
    def __init__(
        self,
        n_surface_sampling: int,
        n_bbox_sampling: int,
        n_volume_sampling: int,
        raw_data_path: str,
        save_path: str,
        translate_mode: str,
        dynamic_sampling: bool,
        is_debug_mode: bool = False,
    ) -> None:
        self.raw_data_path = raw_data_path
        self.save_path = save_path
        self.translate_mode = translate_mode
        self.dynamic_sampling = dynamic_sampling
        self.is_debug_mode = is_debug_mode

        self.n_surface_sampling = n_surface_sampling
        self.n_bbox_sampling = n_bbox_sampling
        self.n_volume_sampling = n_volume_sampling

        if self.is_debug_mode:
            utils.add_debugvisualizer(globals())

    @utils.runtime_calculator
    def _load_meshes_and_compute_max_norm(
        self,
        map_z_to_y: bool = False,
        check_watertight: bool = True,
        translate_mode: DataCreatorHelper.TYPES = DataCreatorHelper.CENTER_WITHOUT_Z,
        save_html: bool = False,
    ):
        paths = [
            os.path.join(self.raw_data_path, file) for file in os.listdir(self.raw_data_path) if file.endswith(".obj")
        ]

        tasks = [(path, map_z_to_y, check_watertight, translate_mode, save_html) for path in paths]
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            results = pool.starmap(DataCreatorHelper.load_mesh_and_compute_max_norm, tasks)

        meshes, lengths = zip(*results)
        max_length = max(lengths)

        return meshes, max_length

    @utils.runtime_calculator
    def create(self) -> None:
        """Create data for training sdf decoder"""

        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)

        meshes, max_length = self._load_meshes_and_compute_max_norm(
            map_z_to_y=True, check_watertight=True, translate_mode=self.translate_mode, save_html=False
        )

        cls = 0
        for mesh in tqdm(meshes, desc="Preprocessing"):
            normalized_mesh = self.get_normalized_mesh(mesh, max_length=max_length)

            centralized_mesh = normalized_mesh.copy()
            centralized_mesh.vertices += np.array([0.5, 0.5, 0])

            if self.dynamic_sampling:
                (
                    self.n_surface_sampling,
                    self.n_bbox_sampling,
                    self.n_volume_sampling,
                ) = Configuration.get_dynamic_sampling_size(mesh_vertices_count=mesh.vertices.shape[0])

            print(
                f"mesh_vertices_count: {mesh.vertices.shape[0]}",
                f"n_total_sampling: {self.n_surface_sampling + self.n_bbox_sampling + self.n_volume_sampling}",
            )

            xyz = self.sample_pts(
                centralized_mesh, self.n_surface_sampling, self.n_bbox_sampling, self.n_volume_sampling
            )

            sdf, *_ = pcu.signed_distance_to_mesh(xyz, centralized_mesh.vertices, centralized_mesh.faces)
            sdf = np.expand_dims(sdf, axis=1)

            cls_name = os.path.basename(mesh.path).split(".")[0]

            np.savez(
                os.path.join(self.save_path, f"{cls_name}.npz"),
                xyz=xyz,
                sdf=sdf,
                cls=cls,
                cls_name=cls_name,
            )

            cls += 1
