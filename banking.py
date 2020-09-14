"""Module for working with bank account"""
import abc
from random import randint
from sys import exit

from . import dblink


class BankCabinetStateBase(abc.ABC):
    """abstract class for bank cabinet states"""
    def __init__(self):
        self.bank_cabinet = None
        self._menu = ()
        self._menu_items = ''
        self._menu_commands = {}

    def enter_state(self, bank_cabinet):
        self.bank_cabinet = bank_cabinet

    def _working(self):
        """working loop in state"""
        working = True
        while working:
            user_command = self._show_menu()
            select_command = self._menu_commands[user_command]
            working = select_command()

    def _show_menu(self):
        """print user menu, wait command"""
        print(*self._menu, sep='\n')
        command = ' '
        while command not in self._menu_items:
            command = input('> ')
        return int(command)

    @abc.abstractmethod
    def accept(self, bank_cabinet, instance=None):
        pass

    @abc.abstractmethod
    def cancel(self):
        pass


class BankCabinetLogoutState(BankCabinetStateBase):
    def __init__(self):
        super().__init__()
        self._menu = (
            "1. Create an account",
            "2. Log into account",
            "0. Exit"
        )
        self._menu_items = '012'

    def enter_state(self, bank_cabinet):
        super().enter_state(bank_cabinet)
        self._menu_commands = {
            0: self.cancel,
            1: self.bank_cabinet.create_account,
            2: self.bank_cabinet.login
        }
        self._working()

    def accept(self, bank_cabinet, account):
        bank_cabinet.set_user_account(account)
        bank_cabinet.transition_state(BankCabinetLoginState())

    def cancel(self):
        print('Bye!')
        exit()


class BankCabinetLoginState(BankCabinetStateBase):
    def __init__(self):
        super().__init__()
        self._menu = (
            "1. Balance",
            "2. Add income",
            "3. Do transfer",
            "4. Close account",
            "5. Log out",
            "0. Exit"
        )
        self._menu_items = '012345'

    def enter_state(self, bank_cabinet):
        super().enter_state(bank_cabinet)
        self._menu_commands = {
            0: self.cancel,
            1: self.bank_cabinet.user_balance,
            2: self.bank_cabinet.add_income,
            3: self.bank_cabinet.transfer,
            4: self.bank_cabinet.close_account,
            5: self.bank_cabinet.logout
        }
        self._working()

    def accept(self, bank_cabinet, instance):
        bank_cabinet.set_user_account(None)
        bank_cabinet.transition_state(BankCabinetLogoutState())

    def cancel(self):
        exit()


class Account:
    """class for bank account: card"""
    def __init__(self, card_number, pin, balance=0):
        self.card_number = card_number
        self.pin = pin
        self.balance = balance


class BankUser:
    """class for bank user"""
    def __init__(self):
        self.db = dblink.DB()
        self.current_account = None
        self.accounts = {}
        self._get_accounts()

    def cards(self):
        """get all cards numbers from user account"""
        return self.db.get_cards_numbers()

    def add_account(self, account):
        """add new account, make commit to db"""
        self.accounts[account.card_number] = account
        card_id = len(self.accounts)
        self.db.create_card(card_id, account.card_number,
                            account.pin, account.balance)

    def del_account(self):
        """delete current account from db"""
        account = self.accounts.pop(self.current_account.card_number)
        self.db.delete_card(account.card_number)

    def save_current_balance(self):
        """save balance of current account to db"""
        self.db.new_balance(self.current_account.card_number,
                            self.current_account.balance)

    def fund(self, income):
        """add income to current account, write to db new balance"""
        self.current_account.balance += income
        self.save_current_balance()

    def transfer(self, card, expend):
        """transfer funds from current account to card"""
        card_info = self.db.get_card_info(card)
        card_account = Account(card_number=card_info[0],
                               pin=card_info[1],
                               balance=card_info[2])
        self.current_account.balance -= expend
        self.save_current_balance()
        card_account.balance += expend
        self.db.new_balance(card_account.card_number, card_account.balance)

    def _get_accounts(self):
        for card in self.db.get_cards_info():
            account = Account(card_number=card[0],
                              pin=card[1],
                              balance=card[2])
            self.accounts[card[0]] = account


class BankCabinet:
    """class for bank cabinet to interface with user"""
    BIN = 400000

    def __init__(self):
        self.user = BankUser()
        self.state = BankCabinetLogoutState()
        self.transition_state(self.state)

    def transition_state(self, bank_cabinet_state):
        self.state = bank_cabinet_state
        bank_cabinet_state.enter_state(self)

    @staticmethod
    def calc_check_sum(card_number):
        """get check sum with Luhn algorithm"""
        digits = list(map(int, str(card_number)))
        for i in range(0, len(digits), 2):
            digits[i] = digits[i] * 2
        for i in range(0, len(digits)):
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits)

    @staticmethod
    def check_card_number(card_number):
        """Luhn algorithm card number validating"""
        check_sum = BankCabinet.calc_check_sum(card_number)
        return check_sum % 10 == 0

    def _create_card_number(self):
        """create new card number"""
        card = randint(1, 999_999_999)
        check_sum = \
            10 - self.__class__.calc_check_sum(
                int(f'{self.BIN}{card:0>9}0')) % 10
        if check_sum == 10:
            check_sum = 0
        return f'{self.BIN}{card:0>9}{check_sum}'

    def get_new_card(self):
        """get new card number"""
        card_number = self._create_card_number()
        cards = self.user.cards()
        while card_number in cards:
            card_number = self._create_card_number()
        return card_number

    def create_account(self):
        """create a user account, card number and PIN"""
        new_card = self.get_new_card()
        new_pin = f'{randint(0, 9999):0>4}'
        new_account = Account(new_card, new_pin)
        self.user.add_account(new_account)
        print('Your card has been created')
        print('Your card number:')
        print(new_card)
        print('Your card PIN:')
        print(new_pin)
        return True

    def user_balance(self):
        if self.user.current_account:
            print(f'Balance: {self.user.current_account.balance}')
        return True

    def set_user_account(self, account):
        """set current account to bank user"""
        self.user.current_account = account

    def add_income(self):
        """add funds on current user account"""
        print('Enter income:')
        income = int(input('>'))
        self.user.fund(income)
        return True

    def transfer(self):
        """do transfer from current user account"""
        print('Transfer')
        print('Enter card number:')
        card = input('>')
        if self.check_card_number(int(card)):
            if card == self.user.current_account.card_number:
                print("You can't transfer money to the same account!")
            elif card not in self.user.cards():
                print('Such a card does not exist.')
            else:
                print('Enter how much money you want to transfer:')
                expend = int(input('>'))
                if self.user.current_account.balance < expend:
                    print('Not enough money!')
                else:
                    self.user.transfer(card, expend)
                    print('Success!')
        else:
            print('Probably you made a mistake in the card number.',
                  'Please try again!')
        return True

    def close_account(self):
        """close current user account"""
        self.user.del_account()
        print('The account has been closed!')
        self.state.accept(self, None)
        return True

    def login(self):
        """log into account by card number and PIN"""
        print('Enter your card number:')
        card_number = input('>')
        cards = self.user.cards()
        wrong = False
        if card_number in cards:
            account = self.user.accounts[card_number]
            print('Enter your PIN:')
            pin = input('>')
            if pin == account.pin:
                print('You have successfully logged in!')
                self.state.accept(self, account)
            else:
                wrong = True
        else:
            wrong = True
        if wrong:
            print('Wrong card number or PIN!')
        return True

    def logout(self):
        self.state.cancel()
        return True


if __name__ == '__main__':
    cabinet = BankCabinet()
