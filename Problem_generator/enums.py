from enum import Enum


class Category(str, Enum):
    basic = "Basic/Introductory"
    algorithm = "Algorithm/Data Structure"
    sql = "SQL"


class Difficulty(str, Enum):
    level0 = "0"
    level1 = "1"
    level2 = "2"


class Language(str, Enum):
    python = "Python"
    java = "Java"
    cpp = "C++"
    sql = "SQL"


class Style(str, Enum):
    general = "General"
    kakao = "Kakao"
    contest = "Contest"