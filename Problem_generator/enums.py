from enum import Enum


class Category(str, Enum):
    basic = "Basic/Introductory"
    algorithm = "Algorithm/Data Structure"
    sql = "SQL"


class AlgorithmSubcategory(str, Enum):
    hash = "Hash"
    stack_queue = "Stack/Queue"
    heap = "Heap"
    sort = "Sort"
    brute_force = "Brute Force"
    greedy = "Greedy"
    dynamic_programming = "Dynamic Programming"
    dfs_bfs = "DFS/BFS"
    binary_search = "Binary Search"
    graph = "Graph"


class SQLSubcategory(str, Enum):
    select = "SELECT"
    sum_max_min = "SUM/MAX/MIN"
    group_by = "GROUP BY"
    is_null = "IS NULL"
    join = "JOIN"
    string_date = "String/Date"


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