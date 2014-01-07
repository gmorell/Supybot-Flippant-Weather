###
# Copyright (c) 2014, Gabriel Morell-Pacheco
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class Weather2014(callbacks.Plugin):
    """Add the help for "@plugin help Weather2014" here
    This should describe *how* to use this plugin."""
    threaded = True


Class = Weather2014


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
