'''Generic nuScenes Dataset Loader Module'''

from abc import ABCMeta, abstractmethod
from hashlib import sha256
from logging import info, warning
import os.path

from cdlake import Cdl  # pylint: disable=import-error
from typing_extensions import Literal, final

__all__ = ['BaseDataLoader', 'Category']

Category = Literal['samples', 'sweeps']


class BaseDataLoader(metaclass=ABCMeta):
    '''Generic nuScenes Dataset Loader'''

    def __init__(
        self,
        cache_dir: str = './cache',
        category: Category = 'samples',
    ) -> None:
        self._cache_dir = cache_dir
        self._cdl: Cdl | None = None
        self._current_category = category
        self._current_scene_index = -1
        self._current_timestamp = -1
        self._is_loaded = False
        self._uid: str | None = None

    @property
    @final
    def category(self) -> Category:
        '''Returns the current category'''
        return self._current_category
    
    @property
    @final
    def cdl(self) -> Category:
        '''Returns the current connected data lake instance'''
        if self._cdl is None:
            self._cdl = Cdl(
                cache_dir=os.path.join(self._cache_dir, self.uid),
            )
        return self._cdl

    @property
    @final
    def scene(self) -> str:
        '''Returns the current scene'''
        if not self.scenes:
            raise ValueError('Empty dataset')
        return self.scenes[self._current_scene_index]

    @property
    @abstractmethod
    def scenes(self) -> list[str]:
        '''Returns the all available scenes'''
        raise NotImplementedError()

    @property
    @final
    def timestamp(self) -> int:
        '''Returns the current timestamp as milliseconds'''
        return self._current_timestamp

    @property
    @abstractmethod
    def timestamps(self) -> range:
        '''Returns the range of available timestamps as milliseconds'''
        raise NotImplementedError()

    @property
    @final
    def uid(self) -> str:
        '''Returns the unique hashed ID of this data loader'''
        if not hasattr(self, '_uid') or self._uid is None:
            self._uid = sha256(repr(self).encode()).hexdigest()
        return self._uid

    @property
    @abstractmethod
    def cam_front(self) -> str:
        '''Returns the front camera image file path as URL'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def lidar_top(self) -> str:
        '''Returns the top lidar USD file path as URL'''
        raise NotImplementedError()

    def lookup_cam_front(self, _timestamp: str) -> str | None:
        '''Returns a front camera image file path
        within the specific timestamp as URL'''
        return None

    def lookup_lidar_top(self, _timestamp: str) -> str | None:
        '''Returns a the top lidar USD file path
        within the specific timestamp as URL'''
        return None

    @final
    def checkout_dataset(self) -> bool:
        '''Checkout the category'''
        if self._is_loaded:
            return False

        warning(f'Reloading nuScenes dataset: {self!r}')
        self._checkout_dataset()

        # Checkout to the selected category
        self.checkout_category(self.category)
        self._is_loaded = True
        warning(f'Reloaded nuScenes dataset: {self!r}')
        return True

    def _checkout_dataset(self) -> None:
        pass

    @final
    def checkout_category(self, category: Category) -> bool:
        '''Checkout the category'''
        if self._is_loaded and self._current_category == category:
            return False
        self._current_category = category

        warning(f'Reloading nuScenes category: {category}')
        self._checkout_category(self.category)

        # Seek to the first scene
        self._current_scene_index = -1
        return self.checkout_scene(0)

    @abstractmethod
    def _checkout_category(self, category: Category) -> None:
        raise NotImplementedError()

    @final
    def checkout_scene(self, scene_index: int) -> bool:
        '''Checkout the scene with the given index'''
        if self._is_loaded and self._current_scene_index == scene_index:
            return False
        self._current_scene_index = scene_index

        warning(f'Reloading nuScenes scene: {self.scene}')
        self._checkout_scene(self.scene)

        # Seek to the first scene
        self._current_timestamp = -1
        self._seek(self.timestamps.start)
        return True

    @abstractmethod
    def _checkout_scene(self, scene: str) -> None:
        raise NotImplementedError()

    @final
    def seek(self, timestamp: int) -> bool:
        '''Browse to the specific timestamp'''
        if self._is_loaded and self._current_timestamp == timestamp:
            return False
        self._current_timestamp = timestamp

        info(f'Seeking to the timestamp: {timestamp}')
        self._seek(self.timestamp)
        return True

    @abstractmethod
    def _seek(self, timestamp: int) -> None:
        '''Browse to the specific timestamp'''
        raise NotImplementedError()

    @final
    def seek_next(self) -> bool:
        '''Browse to the next timestamp'''
        return self.seek(self.timestamp + 1)

    @final
    def seek_to_start(self) -> bool:
        '''Browse to the first timestamp'''
        return self.seek(self.timestamps.start)

    @final
    def seek_to_end(self) -> bool:
        '''Browse to the last timestamp'''
        return self.seek(self.timestamps.stop)

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()

    def __del__(self) -> None:
        info(f'Finalizing nuScenes dataset: {self!r}')
