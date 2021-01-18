#!/usr/bin/env python3
import typing
import os
import sys
import argparse
import logging
import itertools
from collections import namedtuple
from functools import cmp_to_key

try:
    import jinja2
except ImportError:
    print('Jinja2 required; Abort execution')
    print(' Use python3 -m pip install jinja2')
    sys.exit(os.EX_OSFILE)

# Logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# Icons per row
DEFAULT_ELEMENTS_PER_ROW = 3
# Keep group order
ICON_GROUP_ORDER = ['small', 'medium', 'large', 'cover', 'notification', ]
ICON_GROUP_MARKS = {
    'l': 'large',
    's': 'small',
    'm': 'medium',
    'cover': 'cover',
    'lock': 'notification',
}

IconDetails = namedtuple('IconDetails', ['name', 'group', 'relpath'])
IconDetails.__new__.__defaults__ = (None,) * len(IconDetails._fields)


def fs_path_exists(path):
    # type: (str) -> typing.Optional[str]
    _path = fs_path(path)
    return _path if os.path.exists(_path) else None


def fs_path(path):
    # type: (str) -> typing.Optional[str]
    return os.path.abspath(os.path.expanduser(path))


def configure_parser(parser=None):
    # type: (typing.Optional[argparse.ArgumentParser]) -> argparse.ArgumentParser
    parser = parser or argparse.ArgumentParser(description='Icon preview generator CLI tool')
    parser.add_argument('icons', type=fs_path_exists, default=None, help='Icons path')
    parser.add_argument('template', type=fs_path_exists, default=None, help='Template path')
    parser.add_argument('result', type=fs_path, default=None, help='Result path (with filename)')
    parser.add_argument('--small', action='store_true', help='Small icons')
    parser.add_argument('--medium', action='store_true', help='Medium icons')
    parser.add_argument('--large', action='store_true', help='Large icons')
    parser.add_argument('--cover', action='store_true', help='Cover icons')
    return parser


def split_by(entries, length=DEFAULT_ELEMENTS_PER_ROW):
    # type: (typing.Collection[typing.Any], int) -> typing.Generator[typing.Collection]
    """Jinja2 filter"""
    items = iter(entries)
    piece = list(itertools.islice(items, length))
    while piece:
        yield piece
        piece = list(itertools.islice(items, length))


def cmp_groups(a, b):
    """Custom sort function"""
    a_i = ICON_GROUP_ORDER.index(a)
    b_i = ICON_GROUP_ORDER.index(b)
    if a_i > b_i:
        return 1
    elif a_i == b_i:
        return 0
    else:
        return -1


def icon_group_order(items):
    """Jinja2 filter"""
    items.sort(key=cmp_to_key(cmp_groups))
    return items


def get_template(template_name, template_path):
    # type: (str, typing.Optional[str]) -> jinja2.Template
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    env.filters.update(
        split_by=split_by,
        icon_group_order=icon_group_order,
    )
    return env.get_template(template_name)


def get_groups(flags):
    # type: (argparse.Namespace) -> typing.Collection[str]
    suggested = [group for group in ['small', 'medium', 'large', 'cover'] if getattr(flags, group, False)]
    return suggested if len(suggested) else list(ICON_GROUP_MARKS.values())


def get_icons(icons_path, result_dir):
    # type: (str, str) -> typing.Dict
    """Collect icons info"""
    icons = {}
    for (root, dirs, files) in os.walk(icons_path, topdown=True):
        for filename in files:
            fname = os.path.join(root, filename)
            if fname.lower().endswith('.svg'):
                icon_name = os.path.basename(fname).rsplit('.', 1)[0]
                details = IconDetails(
                    name=icon_name,
                    group=ICON_GROUP_MARKS.get(icon_name.split('-')[1], 'unknown'),
                    relpath=os.path.relpath(fname, result_dir)
                )
                if details.group not in icons:
                    icons[details.group] = []
                icons[details.group].append(details)
    for _group in icons.keys():
        icons[_group] = sorted(icons[_group], reverse=False, key=lambda item: item.name)
    return icons


def main():
    flags = configure_parser().parse_args()
    logger.debug(flags)
    if flags.icons is None:
        logger.error('Icons path not found')
        sys.exit(os.EX_DATAERR)
    if flags.template is None:
        logger.error('Template not found')
        sys.exit(os.EX_DATAERR)

    icons = get_icons(flags.icons, os.path.dirname(flags.result))
    groups = get_groups(flags)
    template = get_template(os.path.basename(flags.template), os.path.dirname(flags.template))
    try:
        os.makedirs(os.path.dirname(flags.result), exist_ok=True)
        with open(flags.result, 'wt', encoding='utf-8') as fp:
            fp.write(template.render(
                icons=icons,
                groups=groups,
                row_size=DEFAULT_ELEMENTS_PER_ROW,
            ))
        logger.info('Result file stored at: %s', flags.result)
    except Exception as exc:
        logger.error('Error: %s', exc, exc_info=exc)
        sys.exit(1)
    sys.exit(os.EX_OK)


if __name__ == '__main__':
    main()
