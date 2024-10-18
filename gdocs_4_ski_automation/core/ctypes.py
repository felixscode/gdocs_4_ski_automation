from dataclasses import dataclass
from enum import Enum   

class Course(Enum):
    ZWEGERL = "Zwergel"
    ZWEGERL_SNOWBOARD = "Zwergel Snowboard"
    SKI = "Ski"
    SNOWBOARD = "Snowboard"

@dataclass
class Name:
    first :str
    last: str

    

@dataclass
class ContactPerson:
    name : Name
    adress: str
    mail: str
    tel: str


@dataclass
class Participant:
    name: Name
    age: int
    course: Course
    pre_course: str
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

