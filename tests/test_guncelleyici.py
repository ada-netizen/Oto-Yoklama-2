import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from guncelleyici import surum_parse


def test_surumler_sayisal_siralanir():
    assert surum_parse("v1.10") > surum_parse("v1.9")
    assert surum_parse("1.1") == surum_parse("v1.1")
