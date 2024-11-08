'''FileSystem nuScenes Dataset Loader Module'''

import os.path

from typing_extensions import final, override

from .base import BaseDataLoader, Category
from ..utils.download_datasets import load_or_download_and_extract
from ..utils.timestamp_seek import seek_by

__all__ = ['FileSystemDataLoader']


class FileSystemDataLoader(BaseDataLoader):
    '''FileSystem nuScenes Dataset Loader'''

    def __init__(
        self,
        category: Category = 'samples',
        path: str = './data/nuscenes',
        download_if_not_exists: bool = True,
    ) -> None:
        super().__init__(
            category=category,
        )
        self._download_if_not_exists = download_if_not_exists
        self._path = os.path.realpath(path)

        # Prefetch scenes
        self._category_dir: str
        self._lidar_top_scenes: list[str]

        # Prefetch timestamps
        self._cam_front_base: str
        self._cam_front_timestamps: list[int]
        self._cam_front_filenames: list[str]
        self._lidar_top_base: str
        self._lidar_top_timestamps: list[int]
        self._lidar_top_filenames: list[str]

        # Fetch now
        self._cam_front_path: str
        self._lidar_top_path: str
        self.checkout_dataset()

    @property
    @override
    def scenes(self) -> list[str]:
        '''Returns the all available scenes'''
        return self._lidar_top_scenes

    @property
    @override
    def timestamps(self) -> range:
        '''Returns the range of available timestamps as milliseconds'''
        return range(
            self._lidar_top_timestamps[0],
            self._lidar_top_timestamps[-1],
        )

    @property
    @override
    def cam_front(self) -> str:
        '''Returns the front camera image file path as URL'''
        return self._cam_front_path

    @property
    @override
    def lidar_top(self) -> str:
        '''Returns the top lidar USD file path as URL'''
        return self._lidar_top_path

    @override
    def lookup_cam_front(self, timestamp: str) -> str:
        '''Returns a front camera image file path
        within the specific timestamp as URL'''
        filename = seek_by(
            timestamp=timestamp,
            timestamps=self._cam_front_timestamps,
            values=self._cam_front_filenames,
        )
        return f'file://{self._cam_front_base}/{filename}'

    @override
    def lookup_lidar_top(self, timestamp: str) -> str:
        '''Returns a the top lidar USD file path
        within the specific timestamp as URL'''
        filename = seek_by(
            timestamp=timestamp,
            timestamps=self._lidar_top_timestamps,
            values=self._lidar_top_filenames,
        )
        return f'file://{self._lidar_top_base}/{filename}'

    @override
    def _checkout_dataset(self) -> None:
        # Download the dataset if not exists
        if self._download_if_not_exists:
            self._path = load_or_download_and_extract(
                path=self._path,
                download_samples=self.category == 'samples',
                download_sweeps=self.category == 'sweeps',
            )
        if not os.path.exists(self._path):
            raise FileNotFoundError(
                f'No such nuScenes dataset on: {self._path!r}'
            )

    @override
    def _checkout_category(self, category: Category) -> None:
        # Load scenes
        self._category_dir = os.path.join(self._path, category)
        self._lidar_top_scenes = self._list_scenes(
            kind='LIDAR_TOP',
            ext='.usd',
        )

    @override
    def _checkout_scene(self, scene: str) -> None:
        # Load timestamps
        self._cam_front_base, \
            self._cam_front_timestamps, \
            self._cam_front_filenames = self._list_timestamps(
                kind='CAM_FRONT',
                scene=scene,
                ext='.jpg',
            )
        self._lidar_top_base, \
            self._lidar_top_timestamps, \
            self._lidar_top_filenames = self._list_timestamps(
                kind='LIDAR_TOP',
                scene=scene,
                ext='.usd',
            )

    @override
    def _seek(self, timestamp: int) -> None:
        # Load data
        self._cam_front_path = self.lookup_cam_front(timestamp)
        self._lidar_top_path = self.lookup_lidar_top(timestamp)

    @final
    def _list_scenes(
        self,
        kind: str,
        ext: str,
    ) -> list[str]:
        assert ext.startswith('.')
        path = os.path.join(self._category_dir, kind)
        return sorted(set(
            filename.split('__')[0]
            for filename in os.listdir(path)
            if filename.startswith('n') and filename.endswith(ext)
        ))

    @final
    def _list_timestamps(
        self,
        kind: str,
        scene: str,
        ext: str,
    ) -> tuple[str, list[int], list[str]]:
        assert ext.startswith('.')
        path = os.path.join(self._category_dir, kind)
        filenames = sorted(
            filename
            for filename in os.listdir(path)
            if filename.startswith(scene) and filename.endswith(ext)
        )
        timestamps = [
            int(filename.split(f'__{kind}__')[1][:-len(ext)])
            for filename in filenames
        ]
        return path, timestamps, filenames

    @override
    def __repr__(self) -> str:
        return self._path

    @override
    def __del__(self) -> None:
        super().__del__()
