#!./app/python/python
'''nuScenes Dataset Downloader
'''

from concurrent.futures import ProcessPoolExecutor
from logging import debug, warning
from multiprocessing import cpu_count
import os
import tarfile

from nuscenes.utils.data_classes import LidarPointCloud
import open3d as o3d
from pxr import Usd, UsdGeom, Gf
import requests

__all__ = ['load_or_download_and_extract']


# Function to convert a .pcd.bin file to .pcd
def _convert_bin_to_pcd(file_path) -> o3d.geometry.PointCloud:
    # Load the .pcd.bin file.
    pc = LidarPointCloud.from_file(file_path)
    bin_pcd = pc.points.T

    # Reshape and get only values for x, y and z.
    bin_pcd = bin_pcd.reshape((-1, 4))[:, 0:3]

    # Convert to Open3D point cloud.
    return o3d.geometry.PointCloud(o3d.utility.Vector3dVector(bin_pcd))


def _convert_pcd_to_usd(
    pcd: o3d.geometry.PointCloud,
    path: str,
):
    # Create a new USD stage
    stage = Usd.Stage.CreateNew(path)  # pylint: disable=no-member

    # Define a root Xform in the USD stage to store point cloud
    # pylint: disable=no-member, unused-variable
    root = UsdGeom.Xform.Define(stage, '/Root')  # noqa: F841

    # Create a PointBased geometry at "/Root/PointCloud" in USD
    # pylint: disable=no-member
    points_prim = UsdGeom.Points.Define(stage, '/Root/PointCloud', )

    # Convert Open3D point cloud data to USD-compatible format
    # pylint: disable=no-member
    points = [Gf.Vec3f(*p) for p in pcd.points]
    points_prim.GetPointsAttr().Set(points)

    # Optionally add color data if available
    if pcd.has_colors():
        # pylint: disable=no-member
        colors = [Gf.Vec3f(*c) for c in pcd.colors]
        points_prim.GetDisplayColorAttr().Set(colors)

    # Save the USD stage
    stage.GetRootLayer().Save()
    debug(f'Converted to USD: {path!r}')


def _extract(name: str, path: str, content: bytes):
    debug(f'Processing file: {name}')
    with open(path, 'wb') as f:
        f.write(content)

    if path.endswith('.pcd.bin'):
        usd_path = path[:-8] + '.usd'
        pcd = _convert_bin_to_pcd(path)
        _convert_pcd_to_usd(pcd, usd_path)


def _download_and_extract(
    base_url: str,
    filename: str,
    version: str,
    dest: str,
):
    meta_file = os.path.join(dest, './.downloaded')
    if not os.path.exists(meta_file):
        with open(meta_file, 'w', encoding='utf-8') as f:
            pass
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta_downloaded = (
            line
            for line in (
                line.strip()
                for line in f.readlines()
            )
            if line
        )

    url = f'{base_url}/v{version}/v{version}-{filename}'
    if url in meta_downloaded:
        return  # Skip re-downloading

    warning(f'Downloading dataset: {url!r}')
    # pylint: disable=missing-timeout
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with tarfile.open(fileobj=response.raw, mode='r|gz') as tar:
            with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                for member in tar:
                    path = os.path.join(dest, member.name)
                    if member.isdir():
                        os.makedirs(path, exist_ok=True)
                    elif member.isfile():
                        executor.submit(
                            _extract,
                            name=member.name,
                            path=path,
                            content=tar.extractfile(member).read(),
                        )

    with open(meta_file, 'a', encoding='utf-8') as f:
        f.write(f'{url}\n')


def load_or_download_and_extract(
    path: str = './data/nuscenes',
    download_samples: bool = True,
    download_sweeps: bool = True,
) -> str:
    '''Load a nuScenes dataset or download and extract it.
    '''

    path = os.path.realpath(path)
    warning(f'Downloading nuScenes dataset to {path}')
    os.makedirs(path, exist_ok=True)

    # Download the file
    files = ['trainval_meta.tgz']
    if download_samples:
        files += ['mini.tgz']
    if download_sweeps:
        files += [f'trainval{i+1:02d}_blobs.tgz' for i in range(10)]
    for file in files:
        _download_and_extract(
            base_url='https://d36yt3mvayqw5m.cloudfront.net/public',
            filename=file,
            version='1.0',
            dest=path,
        )
    debug('Loaded nuScenes dataset')
    return path


if __name__ == '__main__':
    # Init logger
    import logging
    logging.basicConfig(level=logging.INFO)

    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--path',
        help='Destination directory to save the dataset',
        default='../../../../../data/nuscenes',
    )
    parser.add_argument(
        '--samples',
        help='Download samples',
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        '--sweeps',
        help='Download sweeps',
        action=argparse.BooleanOptionalAction,
    )
    args = parser.parse_args()

    # Specify the directory you want to start the conversion from
    root_directory = os.path.join(__file__, args.path)
    load_or_download_and_extract(
        path=root_directory,
        download_samples=args.samples,
        download_sweeps=args.sweeps,
    )
