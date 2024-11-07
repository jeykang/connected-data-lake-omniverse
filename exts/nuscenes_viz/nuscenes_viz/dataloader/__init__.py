'''nuScenes DataLoader collection module'''

from .base import BaseDataLoader, Category
from .cdl import CdlDataLoader
from .filesystem import FileSystemDataLoader

__all__ = [
    'BaseDataLoader',
    'Category',
    'CdlDataLoader',
    'FileSystemDataLoader',
    'load_dataset',
]


def load_dataset(
    url: str = './data/nuscenes',
    category: Category = 'samples',
) -> BaseDataLoader:
    '''Loads a proper DataLoader with given URL'''
    if url.startswith('s3://') or url.startswith('s3a://'):
        return CdlDataLoader(
            category=category,
            url=url,
        )
    elif url.startswith('file://'):
        return FileSystemDataLoader(
            category=category,
            path=url[len('file://'):],
        )
    else:
        return FileSystemDataLoader(
            category=category,
            path=url,
        )
