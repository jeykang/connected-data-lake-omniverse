'''FileSystem nuScenes Dataset Loader Module'''

import os

from cdlake import Cdl  # pylint: disable=import-error
import pandas as pd
from typing_extensions import final, override

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
    def _list(
        self,
        key: str,
        column_name: str,
        sql: str,
    ) -> list[str]:
        # Try to hit cache
        cache_path = os.path.join(
            self._cache_dir, column_name, f'{key}.parquet',
        )
        if os.path.exists(cache_path):
            df = pd.read_parquet(cache_path)
        else:
            # Fetch the values
            df = self._fs.sql(sql).to_pandas()

            # Store to the cache
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            df.to_parquet(cache_path)

        # Return the selected column
        return df[column_name].to_list()

    @final
    def _list_scenes(
        self,
        kind: str,
        ext: str,
    ) -> list[str]:
        assert ext.startswith('.')
        path = os.path.join(self._category_dir, kind)
        column_name = 'scene'
        sql = f'''
            SELECT DISTINCT
                SUBSTR(name, 1, INSTR(name, '__{kind}__') - 1) AS {column_name}
            FROM
                rootfs
            WHERE
                name LIKE 'n%{ext}'
                    AND parent == '{path}'
            ORDER BY
                {column_name} ASC
        '''
        return self._list(
            key=kind,
            column_name=column_name,
            sql=sql,
        )

    @final
    def _list_timestamps(
        self,
        kind: str,
        scene: str,
        ext: str,
    ) -> list[str]:
        assert ext.startswith('.')
        path = os.path.join(self._category_dir, kind)
        column_name = 'name'
        sql = f'''
            SELECT DISTINCT
                {column_name}
            FROM
                rootfs
            WHERE
                name LIKE '{scene}__{kind}__%{ext}'
                    AND parent == '{path}'
            ORDER BY
                {column_name} ASC
        '''
        filenames = self._list(
            key=f'{scene}__{kind}__',
            column_name=column_name,
            sql=sql,
        )
        timestamps = [
            int(filename.split(f'__{kind}__')[1][:-len(ext)])
            for filename in filenames
        ]
        return path, timestamps, filenames

    @final
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
