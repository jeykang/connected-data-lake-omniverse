'''An Omniverse Kit Extension module for NuScenes Visualization
'''

from logging import info, warning

from typing_extensions import final, override
from pxr import Sdf  # pylint: disable=import-error

import omni.ext  # pylint: disable=import-error
import omni.kit.commands  # pylint: disable=import-error
import omni.kit.viewport  # pylint: disable=import-error
import omni.ui as ui  # pylint: disable=import-error
import omni.usd  # pylint: disable=import-error

try:
    from .utils.deps import install_dependencies
    install_dependencies()
except ImportError as e:
    raise e

from .dataloader import FileSystemDataLoader  # noqa: E501, pylint: disable=no-name-in-module

__all__ = [
    'RGBLiDARVisualizerExtension',
]


class RGBLiDARVisualizerExtension(omni.ext.IExt):
    '''An Omniverse Kit Extension for NuScenes Visualization'''

    # UI
    _ui_cam_front: ui.Image
    _ui_scene_selector: ui.ComboBox
    _ui_timestamp_slider: ui.IntSlider
    _window: ui.Window

    # States
    _data_loader: FileSystemDataLoader

    @final
    @override
    def on_startup(self, _ext_id: str) -> None:
        '''Initialize the extension'''
        info('[RGBLiDARVisualizer] Extension started')

        # Download nuScenes dataset
        self._data_loader = FileSystemDataLoader(category='samples')
        self._data_loader.checkout_dataset()

        # Define window
        self._window = ui.Window(
            title='NuScenes RGB & LiDAR Visualizer',
            width=400,
            height=600,
        )
        with self._window.frame:
            with ui.VStack():
                ui.Label('Select Scene:')
                self._ui_scene_selector = ui.ComboBox()

                ui.Label('Select Timestamp:')
                self._ui_timestamp_slider = ui.IntSlider(
                    model=ui.SimpleIntModel(),
                )

                # Register callbacks
                self._ui_scene_selector.model.add_item_changed_fn(
                    self._on_scene_changed,
                )
                self._ui_timestamp_slider.model.add_value_changed_fn(
                    self._on_timestamp_changed,
                )

                # Display Image
                ui.Label('RGB Image:')
                self._ui_cam_front = ui.Image('', width=380, height=280)

                # Instructions
                ui.Label(
                    'LiDAR Pointcloud is displayed in the main viewport.',
                    height=20,
                )

                # Fetch the scenes
                self._reload_scenes()

    @final
    @override
    def on_shutdown(self) -> None:
        '''Finalize the extension'''
        info('[RGBLiDARVisualizer] Extension shutdown')
        self._window = None
        self._data_loader = None

    def _reload_scenes(self) -> None:
        # Reload scenes
        for scene in self._ui_scene_selector.model.get_item_children():
            self._ui_scene_selector.model.remove_item(scene)
        for scene in self._data_loader.scenes:
            self._ui_scene_selector.model.append_child_item(
                None,
                ui.SimpleStringModel(scene),
            )

        # Reload timestamps
        self._reload_timestamps()

    def _reload_timestamps(self) -> None:
        timestamps = self._data_loader.timestamps
        self._ui_timestamp_slider.min = timestamps.start
        self._ui_timestamp_slider.max = timestamps.stop
        self._ui_timestamp_slider.model.set_min(timestamps.start)
        self._ui_timestamp_slider.model.set_max(timestamps.stop)
        self._ui_timestamp_slider.model.set_value(self._data_loader.timestamp)

        # Reload the screen
        self._reload_screen()

    def _reload_screen(self) -> None:
        # Display the image and pointcloud at the selected timestamp
        self._ui_cam_front.source_url = self._data_loader.cam_front
        self._display_pointcloud(self._data_loader.lidar_top)

    def _on_scene_changed(self, model, *_args) -> None:
        # Propagate value to the DataLoader
        index = model.get_item_value_model().as_int
        if not self._data_loader.checkout_scene(index):
            return  # nothing changed

        # Reload timestamps
        self._reload_timestamps()

    def _on_timestamp_changed(self, model) -> None:
        # Propagate value to the DataLoader
        timestamp = model.get_value_as_int()
        if not self._data_loader.seek(timestamp):
            return  # nothing changed

        # Reload the screen
        self._reload_screen()

    def _display_pointcloud(self, url: str) -> None:
        # Load the USD file into the stage
        stage = omni.usd.get_context().get_stage()
        if stage is None:
            warning('No active stage found.')
            return

        # Remove existing pointcloud prim if any
        pointcloud_prim_path = Sdf.Path('/World/LiDARPointCloud')
        if pointcloud_prim_path and stage.GetPrimAtPath(pointcloud_prim_path):
            # Remove the existing prim
            omni.kit.commands.execute(
                'DeletePrims',
                paths=[str(pointcloud_prim_path)],
            )

        # Reference the pointcloud USD file
        pointcloud_prim = stage.DefinePrim(pointcloud_prim_path, 'Points')
        pointcloud_prim.GetReferences().AddReference(
            assetPath=url,
            primPath='/Root/PointCloud',
        )
        # Focus the camera on the point cloud
        # self.focus_on_prim(pointcloud_prim_path)
