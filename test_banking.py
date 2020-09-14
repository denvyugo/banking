import banking
import pytest


def test_chek_card():
    """check card number by Luhn algorithm"""
    assert banking.check_card_number(4000008449433403) == True
