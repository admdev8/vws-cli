"""
A CLI for the Vuforia Cloud Recognition Service API.
"""

import dataclasses
import io
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union

import click
import click_pathlib
import wrapt
import yaml
from vws import CloudRecoService
from vws.exceptions.cloud_reco_exceptions import (
    AuthenticationFailure,
    BadImage,
    InactiveProject,
    MatchProcessing,
    RequestTimeTooSkewed,
)
from vws.exceptions.custom_exceptions import (
    ConnectionErrorPossiblyImageTooLarge,
)
from vws.include_target_data import CloudRecoIncludeTargetData

from vws_cli import __version__
from vws_cli.options.credentials import (
    client_access_key_option,
    client_secret_key_option,
)


@wrapt.decorator
def handle_vwq_exceptions(  # noqa:E501 pylint:disable=too-many-branches,too-many-statements
    wrapped: Callable[..., str],
    instance: Any,
    args: Tuple,
    kwargs: Dict,
) -> None:
    """
    Show error messages and catch exceptions for errors from the ``VWS-Python``
    library.
    """
    assert not instance  # This is to satisfy the "vulture" linter.
    try:
        wrapped(*args, **kwargs)
    except BadImage:
        error_message = (
            'Error: The given image is corrupted or the format is not '
            'supported.'
        )
    except InactiveProject:
        error_message = (
            'Error: The project associated with the given keys is inactive.'
        )
    except AuthenticationFailure:
        error_message = 'The given secret key was incorrect.'
    except RequestTimeTooSkewed:
        error_message = (
            'Error: Vuforia reported that the time given with this request '
            'was outside the expected range. '
            'This may be because the system clock is out of sync.'
        )
    except ConnectionErrorPossiblyImageTooLarge:
        error_message = 'Error: The given image is too large.'
    except MatchProcessing:
        error_message = (
            'Error: The given image matches a target which was recently '
            'added, updated or deleted and Vuforia returns an error in this '
            'case.'
        )
    else:
        return

    click.echo(error_message, err=True)
    sys.exit(1)


def image_argument(command: Callable[..., None]) -> Callable[..., None]:
    """
    An argument decorator for choosing a query image.
    """
    click_option_function = click.argument(
        'image',
        type=click_pathlib.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    )

    return click_option_function(command)


def max_num_results_option(
    command: Callable[..., None],
) -> Callable[..., None]:
    """
    An option decorator for choosing the maximum number of query results.
    """
    maximum = 50
    click_option_function = click.option(
        '--max-num-results',
        type=click.IntRange(min=1, max=maximum),
        default=1,
        help=(
            'The maximum number of matching targets to be returned. '
            f'Must be <= {maximum}.'
        ),
        show_default=True,
    )

    return click_option_function(command)


def include_target_data_callback(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: str,
) -> CloudRecoIncludeTargetData:
    """
    Use as a callback for active flag options.
    """
    # This is to satisfy the "vulture" linter.
    assert ctx
    assert param

    return {
        'top': CloudRecoIncludeTargetData.TOP,
        'none': CloudRecoIncludeTargetData.NONE,
        'all': CloudRecoIncludeTargetData.ALL,
    }[value]


def include_target_data_option(
    command: Callable[..., None],
) -> Callable[..., None]:
    """
    An option decorator for choosing whether to include target data.
    """
    click_option_function = click.option(
        '--include-target-data',
        type=click.Choice(['top', 'none', 'all'], case_sensitive=True),
        default='top',
        callback=include_target_data_callback,
        help=(
            'Whether target_data records shall be returned for the matched '
            'targets. Accepted values are top (default value, only return '
            'target_data for top ranked match), none (return no target_data), '
            'all (for all matched targets).'
        ),
        show_default=True,
    )

    return click_option_function(command)


def base_vwq_url_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for choosing the base VWQ URL.
    """
    click_option_function = click.option(
        '--base-vwq-url',
        type=click.STRING,
        default='https://cloudreco.vuforia.com',
        help='The base URL for the VWQ API.',
        show_default=True,
    )

    return click_option_function(command)


@click.command(name='vuforia-cloud-reco')
@image_argument
@client_access_key_option
@client_secret_key_option
@include_target_data_option
@max_num_results_option
@base_vwq_url_option
@handle_vwq_exceptions
# We set the ``version`` parameter because in PyInstaller binaries,
# ``pkg_resources`` is not available.
#
# Click uses ``pkg_resources`` to determine the version if it is not given.
@click.version_option(version=__version__)
def vuforia_cloud_reco(
    image: Path,
    client_access_key: str,
    client_secret_key: str,
    max_num_results: int,
    include_target_data: CloudRecoIncludeTargetData,
    base_vwq_url: str,
) -> None:
    """
    Make a request to the Vuforia Cloud Recognition Service API.
    """
    client = CloudRecoService(
        client_access_key=client_access_key,
        client_secret_key=client_secret_key,
        base_vwq_url=base_vwq_url,
    )
    query_result = client.query(
        image=io.BytesIO(image.read_bytes()),
        max_num_results=max_num_results,
        include_target_data=include_target_data,
    )
    query_result_dict_list = [dataclasses.asdict(res) for res in query_result]
    yaml_list = yaml.dump(query_result_dict_list)
    click.echo(yaml_list)
