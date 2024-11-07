'''FileSystem nuScenes Dataset Loader Module'''

import os

from cdlake import Cdl, CdlFS  # pylint: disable=import-error
from typing_extensions import override

from .base import BaseDataLoader, Category
from ..utils.timestamp_seek import seek_by

__all__ = ['CdlDataLoader']


class CdlDataLoader(BaseDataLoader):
    '''Connected Data Lake nuScenes Dataset Loader'''

    def __init__(
        self,
        cache_dir: str = './cache/omniverse',
        category: Category = 'samples',
        url: str = './data/nuscenes',
    ) -> None:
        super().__init__(
            category=category,
        )
        self._cache_dir = os.path.realpath(cache_dir)
        self._cdl = Cdl()
        self._fs = self._cdl.open(url)
        self._url = url

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
        return self._load(
            parent=self._cam_front_base,
            filename=filename,
        )

    @override
    def lookup_lidar_top(self, timestamp: str) -> str:
        '''Returns a the top lidar USD file path
        within the specific timestamp as URL'''
        filename = seek_by(
            timestamp=timestamp,
            timestamps=self._lidar_top_timestamps,
            values=self._lidar_top_filenames,
        )
        return self._load(
            parent=self._lidar_top_base,
            filename=filename,
        )

    @override
    def _checkout_category(self, category: Category) -> None:
        # Load scenes
        self._category_dir = f'/{category}'
        self._lidar_top_scenes = _list_scenes(
            fs=self._fs,
            base_dir=self._category_dir,
            kind='LIDAR_TOP',
            ext='.usd',
        )

    @override
    def _checkout_scene(self, scene: str) -> None:
        # Load timestamps
        self._cam_front_base, \
            self._cam_front_timestamps, \
            self._cam_front_filenames = _list_timestamps(
                fs=self._fs,
                base_dir=self._category_dir,
                kind='CAM_FRONT',
                scene=scene,
                ext='.jpg',
            )
        self._lidar_top_base, \
            self._lidar_top_timestamps, \
            self._lidar_top_filenames = _list_timestamps(
                fs=self._fs,
                base_dir=self._category_dir,
                kind='LIDAR_TOP',
                scene=scene,
                ext='.usd',
            )

    @override
    def _seek(self, timestamp: int) -> None:
        # Load data
        self._cam_front_path = self.lookup_cam_front(timestamp)
        self._lidar_top_path = self.lookup_lidar_top(timestamp)

    def _load(self, parent: str, filename: str) -> str:
        # Create a directory
        path = os.path.join(self._cache_dir, parent[1:], filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if not os.path.exists(path):
            # Load data
            df = self._fs.sql(f'''
                SELECT
                    data
                FROM
                    rootfs
                WHERE
                    name == '{filename}' AND parent == '{parent}'
                LIMIT 1
            ''')
            data = df['data'].to_pylist().pop()

            # Store the data
            with open(path, 'wb') as f:
                f.write(data)
                del data

        # Return the stored path
        return f'file://{path}'

    @override
    def __repr__(self) -> str:
        return self._url

    @override
    def __del__(self) -> None:
        super().__del__()


def _list_scenes(
    fs: CdlFS,
    base_dir: str,
    kind: str,
    ext: str,
) -> list[str]:
    df = fs.sql(f'''
        SELECT DISTINCT
            SUBSTR(name, 1, INSTR(name, '__{kind}__') - 1) AS scene
        FROM
            rootfs
        WHERE
            name LIKE 'n%{ext}'
                AND parent == '{base_dir}/{kind}'
        ORDER BY
            scene ASC
    ''')
    return df['scene'].to_pylist()


def _list_timestamps(
    fs: CdlFS,
    base_dir: str,
    kind: str,
    scene: str,
    ext: str,
) -> tuple[str, list[int], list[str]]:
    assert ext.startswith('.')
    path = os.path.join(base_dir, kind)
    df = fs.sql(f'''
        SELECT DISTINCT
            name
        FROM
            rootfs
        WHERE
            name LIKE '{scene}%{ext}'
                AND parent == '{path}'
        ORDER BY
            name ASC
    ''')
    filenames = df['name'].to_pylist()
    timestamps = [
        int(filename.split(f'__{kind}__')[1][:-len(ext)])
        for filename in filenames
    ]
    return path, timestamps, filenames
