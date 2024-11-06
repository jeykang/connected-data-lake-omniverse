'''Generic nuScenes Dataset Loader Module'''

from abc import ABCMeta, abstractmethod
from typing import Iterable

from typing_extensions import Literal, final

__all__ = ['BaseDataLoader', 'Category']

Category = Literal['samples', 'sweeps']


class BaseDataLoader(metaclass=ABCMeta):
    '''Generic nuScenes Dataset Loader'''

    def __init__(
        self,
        category: Category = 'samples',
    ) -> None:
        self._current_category = category

    @property
    @final
    def category(self) -> Category:
        '''Returns the current category'''
        return self._current_category

    @property
    @abstractmethod
    def scene(self) -> str:
        '''Returns the current scene'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def scenes(self) -> Iterable[str]:
        '''Returns the all available scenes'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def timestamp(self) -> int:
        '''Return the current timestamp as milliseconds'''
        raise NotImplementedError()

    @property
    @abstractmethod
    def timestamps(self) -> range:
        '''Return the range of available timestamps as milliseconds'''
        raise NotImplementedError()

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

    @final
    def checkout_category(self, category: Category) -> bool:
        '''Checkout the category'''
        if self._current_category == category:
            return False
        self._current_category = category
        return self._checkout_category(category)

    @abstractmethod
    def _checkout_category(self, category: Category) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def checkout_scene(self, scene_index: int) -> bool:
        '''Checkout the scene with the given index'''
        raise NotImplementedError()

    @abstractmethod
    def seek(self, timestamp: int) -> bool:
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
    def __del__(self) -> None:
        raise NotImplementedError()
