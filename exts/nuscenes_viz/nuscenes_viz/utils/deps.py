'''A module for supporing installing python PIP packages'''

import omni.kit.pipapi  # pylint: disable=import-error


def install_dependencies() -> None:
    '''Install python package dependencies'''

    omni.kit.pipapi.install(
        package='cdlake',
        version='0.1.3',
        ignore_import_check=True,
    )
    omni.kit.pipapi.install(
        package='nuscenes-devkit',
        module='nuscenes',
    )
    omni.kit.pipapi.install(
        package='open3d',
    )
    omni.kit.pipapi.install(
        package='pandas',
    )
    omni.kit.pipapi.install(
        package='requests',
    )
    omni.kit.pipapi.install(
        package='usd-core',
        module='pxr',
    )
