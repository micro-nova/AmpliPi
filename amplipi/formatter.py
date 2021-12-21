# AmpliPi Home Audio
# Copyright (C) 2021 MicroNova LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""AmpliPi Help Formatter

Common argparse help formatter
"""

import argparse

class AmpliPiHelpFormatter(argparse.HelpFormatter):
  """ Custom help formatter that shows default values
      and doesn't show duplicate metavars.
  """
  # https://stackoverflow.com/a/23941599/8055271
  def _format_action_invocation(self, action):
    if not action.option_strings:
      metavar, = self._metavar_formatter(action, action.dest)(1)
      return metavar
    parts = []
    if action.nargs == 0:                   # -s, --long
      parts.extend(action.option_strings)
    else:                                   # -s, --long ARGS
      args_string = self._format_args(action, action.dest.upper())
      for option_string in action.option_strings:
        parts.append(f'{option_string}')
      parts[-1] += f' {args_string}'
    return ', '.join(parts)

  def _get_help_string(self, action):
    help_str = action.help
    if '%(default)' not in action.help:
      if action.default is not argparse.SUPPRESS and action.default is not None:
        defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
        if action.option_strings or action.nargs in defaulting_nargs:
          help_str += ' (default: %(default)s)'
    return help_str
