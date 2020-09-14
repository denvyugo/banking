import sqlite3
import os


db_file = 'card.s3db'


class Singleton(type):
    __instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


class DB(metaclass=Singleton):
    """class for working with db"""
    def __init__(self):
        self.connection = self._connect_db()

    def create_card(self, card_id, number, pin, balance=0):
        """create a record in db of new card """
        cursor = self.connection.cursor()
        cursor.execute("""
        INSERT INTO card (id, number, pin, balance)
        VALUES (:id, :card, :pin, :balance)""",
                       {'id': card_id, 'card': number,
                        'pin': pin, 'balance': balance})
        self.connection.commit()

    def new_balance(self, number, balance):
        """add new balance on card"""
        cursor = self.connection.cursor()
        cursor.execute("""
        UPDATE card SET balance = :balance
        WHERE number = :number;""",
                       {'number': number, 'balance': balance})
        self.connection.commit()

    def delete_card(self, number):
        """delete a card from db"""
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM card WHERE card.number = :number',
                       {'number': number})
        self.connection.commit()

    def get_card_info(self, number):
        """get information from db about a card"""
        cursor = self.connection.cursor()
        cursor.execute("""
        SELECT number, pin, balance FROM card
        WHERE number = :number""", {'number': number})
        card = cursor.fetchone()
        return card

    def get_cards_info(self):
        """get all card numbers from db"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT number, pin, balance FROM card;')
        cards = cursor.fetchall()
        return cards

    def get_cards_numbers(self):
        """get all card numbers from db"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT number FROM card;')
        cards = cursor.fetchall()
        return [card[0] for card in cards]

    @staticmethod
    def _connect_db():
        """"check if db file exists, than connect"""
        create_table = os.path.exists(db_file)
        conn = sqlite3.connect(db_file)
        if not create_table:
            conn.execute('''CREATE TABLE card
            (id INTEGER NOT NULL,
            number TEXT NOT NULL,
            pin TEXT NOT NULL,
            balance INTEGER DEFAULT 0);''')
            conn.commit()
        return conn
