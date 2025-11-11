from collections import UserDict
from datetime import datetime, timedelta
import pickle  


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value: str):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            dt = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(dt)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        for i, p in enumerate(self.phones):
            if p.value == phone:
                self.phones.pop(i)
                break

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                break

    def find_phone(self, phone: str) -> Phone | None:
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "-"
        bday_str = str(self.birthday) if self.birthday else "-"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday: {bday_str}"


class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> list[dict]:
        today = datetime.today().date()
        horizon = today + timedelta(days=7)
        result: list[dict] = []
        for record in self.data.values():
            if not record.birthday:
                continue
            bday_this_year = record.birthday.value.replace(year=today.year)
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
            if today <= bday_this_year <= horizon:
                congratulation_date = bday_this_year
                wd = congratulation_date.weekday()
                if wd == 5:  
                    congratulation_date += timedelta(days=2)
                elif wd == 6:  
                    congratulation_date += timedelta(days=1)
                result.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%Y.%m.%d"),
                })
        result.sort(key=lambda d: (d["congratulation_date"], d["name"]))
        return result


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) if str(e) else "Give me name and phone please."
        except IndexError:
            return "Enter user name."
        except KeyError:
            return "Contact not found."
    return inner


def parse_input(user_input: str):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.phones:
        return "No phones."
    return f"{record.name.value}: " + "; ".join(p.value for p in record.phones)


@input_error
def show_all(args, book: AddressBook):
    if not book.data:
        return "No contacts saved."
    return "\n".join(str(rec) for rec in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    name, bday_str, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(bday_str)
    return "Birthday set."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.birthday:
        return "Birthday not set."
    return f"{record.name.value}: {record.birthday}"


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    by_date: dict[str, list[str]] = {}
    for item in upcoming:
        by_date.setdefault(item["congratulation_date"], []).append(item["name"])
    lines = []
    for day in sorted(by_date.keys()):
        names = ", ".join(sorted(by_date[day]))
        lines.append(f"{day}: {names}")
    return "\n".join(lines)


def main():
    book = load_data("addressbook.pkl")
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            continue

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book, "addressbook.pkl")
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()