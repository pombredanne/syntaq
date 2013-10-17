#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011-2013 Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import unicode_literals

import codecs
import sys

from . import Syntaq


if __name__ == "__main__":
    for arg in sys.argv:
        markup = codecs.open(sys.argv[1], "r", "UTF-8").read()
        sys.stdout.write(Syntaq(markup).html)
