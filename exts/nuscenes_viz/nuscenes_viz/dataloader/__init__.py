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
    cache_dir: str = './cache',
    category: Category = 'samples',
    url: str = './data/nuscenes',
) -> BaseDataLoader:
    '''Loads a proper DataLoader with given URL'''
    if url.startswith('s3://') or url.startswith('s3a://'):
        return CdlDataLoader(
            cache_dir=cache_dir,
            category=category,
            url=url,
        )
    elif url.startswith('file://'):
        return FileSystemDataLoader(
            cache_dir=cache_dir,
            category=category,
            path=url[len('file://'):],
        )
    else:
        return FileSystemDataLoader(
            cache_dir=cache_dir,
            category=category,
            path=url,
        )
