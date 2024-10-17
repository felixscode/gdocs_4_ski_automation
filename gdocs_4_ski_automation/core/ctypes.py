from dataclasses import dataclass
from enum import Enum   

class Course(Enum):
    ZWEGERL = "Zwergel"
    NORMAL = "Normal"

@dataclass
class Name:
    first :str
    last: str

@dataclass
class Adress:
    street: str
    number: str
    plz: str
    city: str
    

@dataclass
class ContactPerson:
    name : Name
    adress: Adress
    mail: str
    tel: str


@dataclass
class Participant:
    name: Name
    age: int
    course: Course
    member: bool
    notes: str

@dataclass
class Payment:
    amount: float
    payed: bool


@dataclass 
class Registration:

    time_stemp: int
    _id:int
    contact: ContactPerson
    participants: tuple[Participant]
    payment: Payment
    registration_mail_sent: bool
    payment_mail_sent: bool

