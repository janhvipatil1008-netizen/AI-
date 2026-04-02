"""
python_curriculum.py — Structured Python problem set for Forge Practice Mode.

30 problems across 3 levels (10 each), ordered by difficulty.
Each problem is a dict with keys:
    id, level, order, title, concept, description,
    example_in, example_out, hint1, hint2, starter
"""

# ── Problem definitions ────────────────────────────────────────────────────────

_PROBLEMS: list[dict] = [

    # ── BEGINNER (0–9) ─────────────────────────────────────────────────────────

    {
        "id": "b0", "level": "beginner", "order": 0,
        "title": "Hello, World!",
        "concept": "print() basics",
        "description": "Write a program that prints exactly: Hello, World!",
        "example_in": "(none)",
        "example_out": "Hello, World!",
        "hint1": "Use the print() function with the text inside quotes.",
        "hint2": 'print("Hello, World!") — make sure the comma and exclamation match exactly.',
        "starter": '# Print "Hello, World!" to the console\n',
    },
    {
        "id": "b1", "level": "beginner", "order": 1,
        "title": "Store Your Name",
        "concept": "variables and strings",
        "description": 'Create a variable called `name` and assign your name to it. Then print: Hello, <name>!',
        "example_in": "(none)",
        "example_out": "Hello, Alice!",
        "hint1": "Variables store values. Use = to assign: name = \"Alice\"",
        "hint2": 'Use an f-string: print(f"Hello, {name}!")',
        "starter": "# Store your name in a variable and print a greeting\nname = \n",
    },
    {
        "id": "b2", "level": "beginner", "order": 2,
        "title": "Sum Two Numbers",
        "concept": "integers and arithmetic",
        "description": "Ask the user for two numbers (using input()), convert them to integers, and print their sum.",
        "example_in": "3\n7",
        "example_out": "10",
        "hint1": "input() returns a string — use int() to convert it to a number.",
        "hint2": "a = int(input()) then b = int(input()) then print(a + b)",
        "starter": "# Read two numbers from the user and print their sum\n",
    },
    {
        "id": "b3", "level": "beginner", "order": 3,
        "title": "Even or Odd",
        "concept": "if/else and modulo operator",
        "description": "Ask the user for a number. Print 'Even' if it is divisible by 2, otherwise print 'Odd'.",
        "example_in": "4",
        "example_out": "Even",
        "hint1": "The modulo operator % gives the remainder: 4 % 2 == 0 means even.",
        "hint2": "if n % 2 == 0: print('Even') else: print('Odd')",
        "starter": "# Read a number and print 'Even' or 'Odd'\nn = int(input())\n",
    },
    {
        "id": "b4", "level": "beginner", "order": 4,
        "title": "Countdown",
        "concept": "while loop",
        "description": "Ask the user for a positive integer n. Print numbers from n down to 1, one per line.",
        "example_in": "5",
        "example_out": "5\n4\n3\n2\n1",
        "hint1": "Start with n and subtract 1 each time until you reach 1.",
        "hint2": "while n > 0: print(n) then n -= 1",
        "starter": "# Count down from n to 1\nn = int(input())\n",
    },
    {
        "id": "b5", "level": "beginner", "order": 5,
        "title": "Multiplication Table",
        "concept": "for loop with range()",
        "description": "Ask the user for a number n. Print the multiplication table for n (1×n through 10×n).",
        "example_in": "3",
        "example_out": "3 x 1 = 3\n3 x 2 = 6\n3 x 3 = 9\n3 x 4 = 12\n3 x 5 = 15\n3 x 6 = 18\n3 x 7 = 21\n3 x 8 = 24\n3 x 9 = 27\n3 x 10 = 30",
        "hint1": "Use range(1, 11) to loop from 1 to 10 inclusive.",
        "hint2": 'for i in range(1, 11): print(f"{n} x {i} = {n * i}")',
        "starter": "# Print the multiplication table for n\nn = int(input())\n",
    },
    {
        "id": "b6", "level": "beginner", "order": 6,
        "title": "Sum a List",
        "concept": "lists and accumulation",
        "description": "Given this list: [4, 7, 2, 9, 1], calculate and print the sum without using the built-in sum() function.",
        "example_in": "(none)",
        "example_out": "23",
        "hint1": "Create a variable total = 0, then add each item with a for loop.",
        "hint2": "for num in numbers: total += num",
        "starter": "numbers = [4, 7, 2, 9, 1]\ntotal = 0\n# Add up all numbers without using sum()\n",
    },
    {
        "id": "b7", "level": "beginner", "order": 7,
        "title": "FizzBuzz",
        "concept": "conditions with multiple branches",
        "description": (
            "Print numbers from 1 to 20. For multiples of 3 print 'Fizz', "
            "for multiples of 5 print 'Buzz', for multiples of both print 'FizzBuzz'."
        ),
        "example_in": "(none)",
        "example_out": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n16\n17\nFizz\n19\nBuzz",
        "hint1": "Check the 'both' case (divisible by 3 AND 5) first, before the individual checks.",
        "hint2": "if n % 15 == 0: ... elif n % 3 == 0: ... elif n % 5 == 0: ... else: ...",
        "starter": "# FizzBuzz from 1 to 20\nfor n in range(1, 21):\n    pass  # replace with your logic\n",
    },
    {
        "id": "b8", "level": "beginner", "order": 8,
        "title": "Reverse a String",
        "concept": "string slicing",
        "description": "Ask the user for a word and print it reversed.",
        "example_in": "python",
        "example_out": "nohtyp",
        "hint1": "Python strings support slicing: s[start:stop:step]",
        "hint2": "s[::-1] reverses any sequence in Python.",
        "starter": "# Reverse the user's input string\nword = input()\n",
    },
    {
        "id": "b9", "level": "beginner", "order": 9,
        "title": "Define a Function",
        "concept": "defining and calling functions",
        "description": (
            "Write a function called `greet(name)` that returns the string 'Hello, <name>!'. "
            "Call it with 'World' and print the result."
        ),
        "example_in": "(none)",
        "example_out": "Hello, World!",
        "hint1": "Use the def keyword: def greet(name):",
        "hint2": 'Inside the function: return f"Hello, {name}!" then print(greet("World"))',
        "starter": "# Define the greet function and call it\ndef greet(name):\n    pass  # replace with your code\n\nprint(greet('World'))\n",
    },

    # ── INTERMEDIATE (10–19) ───────────────────────────────────────────────────

    {
        "id": "i0", "level": "intermediate", "order": 0,
        "title": "List Comprehension",
        "concept": "list comprehensions",
        "description": "Using a list comprehension, create a list of squares of even numbers from 1 to 20. Print it.",
        "example_in": "(none)",
        "example_out": "[4, 16, 36, 64, 100, 144, 196, 256, 324, 400]",
        "hint1": "A list comprehension has the form: [expression for item in iterable if condition]",
        "hint2": "[x**2 for x in range(1, 21) if x % 2 == 0]",
        "starter": "# Squares of even numbers from 1 to 20 using a list comprehension\n",
    },
    {
        "id": "i1", "level": "intermediate", "order": 1,
        "title": "Word Counter",
        "concept": "dictionaries and string methods",
        "description": (
            "Write a function `word_count(text)` that returns a dict mapping each word to "
            "the number of times it appears. Ignore case. Test with: "
            "'the cat sat on the mat the cat'."
        ),
        "example_in": "(none)",
        "example_out": "{'the': 3, 'cat': 2, 'sat': 1, 'on': 1, 'mat': 1}",
        "hint1": "Use text.lower().split() to get a list of lowercase words.",
        "hint2": "counts[word] = counts.get(word, 0) + 1 inside a for loop.",
        "starter": (
            "def word_count(text):\n"
            "    counts = {}\n"
            "    # fill in the loop\n"
            "    return counts\n\n"
            "print(word_count('the cat sat on the mat the cat'))\n"
        ),
    },
    {
        "id": "i2", "level": "intermediate", "order": 2,
        "title": "Safe Division",
        "concept": "try/except error handling",
        "description": (
            "Write a function `safe_divide(a, b)` that returns a / b, "
            "but catches ZeroDivisionError and returns None instead of crashing."
        ),
        "example_in": "(none)",
        "example_out": "5.0\nNone",
        "hint1": "Wrap the division in a try block and handle ZeroDivisionError in the except block.",
        "hint2": "try: return a / b except ZeroDivisionError: return None",
        "starter": (
            "def safe_divide(a, b):\n"
            "    pass  # your code here\n\n"
            "print(safe_divide(10, 2))\n"
            "print(safe_divide(5, 0))\n"
        ),
    },
    {
        "id": "i3", "level": "intermediate", "order": 3,
        "title": "Rectangle Class",
        "concept": "classes and methods",
        "description": (
            "Create a class `Rectangle` with width and height. "
            "Add methods area() and perimeter(). Print both for a 4×6 rectangle."
        ),
        "example_in": "(none)",
        "example_out": "Area: 24\nPerimeter: 20",
        "hint1": "Define __init__(self, width, height) to store the dimensions.",
        "hint2": "area = width * height; perimeter = 2 * (width + height)",
        "starter": (
            "class Rectangle:\n"
            "    def __init__(self, width, height):\n"
            "        pass  # store width and height\n\n"
            "    def area(self):\n"
            "        pass\n\n"
            "    def perimeter(self):\n"
            "        pass\n\n"
            "r = Rectangle(4, 6)\n"
            "print(f'Area: {r.area()}')\n"
            "print(f'Perimeter: {r.perimeter()}')\n"
        ),
    },
    {
        "id": "i4", "level": "intermediate", "order": 4,
        "title": "Fibonacci Generator",
        "concept": "generators and yield",
        "description": (
            "Write a generator function `fibonacci(n)` that yields the first n "
            "Fibonacci numbers. Print the first 10."
        ),
        "example_in": "(none)",
        "example_out": "0 1 1 2 3 5 8 13 21 34",
        "hint1": "Use yield instead of return. A generator remembers its state between calls.",
        "hint2": "Track a, b = 0, 1 then yield a; a, b = b, a + b in a loop.",
        "starter": (
            "def fibonacci(n):\n"
            "    pass  # use yield\n\n"
            "print(*fibonacci(10))\n"
        ),
    },
    {
        "id": "i5", "level": "intermediate", "order": 5,
        "title": "File Word Count",
        "concept": "file I/O",
        "description": (
            "Write a function `count_words_in_file(filename)` that reads a text file "
            "and returns the total number of words. Handle FileNotFoundError gracefully."
            " For this exercise, write the file inline and then count it."
        ),
        "example_in": "(none)",
        "example_out": "The file has 9 words.",
        "hint1": "Use open(filename) as f: then f.read().split() to get words.",
        "hint2": (
            "Write the test file first: Path('test.txt').write_text('the quick brown fox ')\n"
            "then count words with len(f.read().split())"
        ),
        "starter": (
            "from pathlib import Path\n\n"
            "# Create a test file\n"
            "Path('test.txt').write_text('the quick brown fox jumps over the lazy dog')\n\n"
            "def count_words_in_file(filename):\n"
            "    try:\n"
            "        pass  # open and count\n"
            "    except FileNotFoundError:\n"
            "        return 0\n\n"
            "n = count_words_in_file('test.txt')\n"
            "print(f'The file has {n} words.')\n"
        ),
    },
    {
        "id": "i6", "level": "intermediate", "order": 6,
        "title": "Timer Decorator",
        "concept": "decorators and functools",
        "description": (
            "Write a decorator `@timer` that prints how long a function takes to run. "
            "Apply it to a function that sums range(10_000_000)."
        ),
        "example_in": "(none)",
        "example_out": "sum_range took 0.XXs\n49999995000000",
        "hint1": "A decorator is a function that takes a function and returns a wrapper function.",
        "hint2": (
            "import time; use time.perf_counter() before and after func(*args, **kwargs); "
            "print the difference."
        ),
        "starter": (
            "import time\nfrom functools import wraps\n\n"
            "def timer(func):\n"
            "    @wraps(func)\n"
            "    def wrapper(*args, **kwargs):\n"
            "        pass  # add timing logic\n"
            "    return wrapper\n\n"
            "@timer\n"
            "def sum_range():\n"
            "    return sum(range(10_000_000))\n\n"
            "print(sum_range())\n"
        ),
    },
    {
        "id": "i7", "level": "intermediate", "order": 7,
        "title": "Lambda, Map, Filter",
        "concept": "functional programming tools",
        "description": (
            "Given numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:\n"
            "1. Use filter() to keep only even numbers.\n"
            "2. Use map() to square them.\n"
            "3. Print the result as a list."
        ),
        "example_in": "(none)",
        "example_out": "[4, 16, 36, 64, 100]",
        "hint1": "filter(lambda x: x % 2 == 0, numbers) returns an iterator of even numbers.",
        "hint2": "Chain them: list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers)))",
        "starter": (
            "numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n"
            "# Filter evens, square them, print as list\n"
        ),
    },
    {
        "id": "i8", "level": "intermediate", "order": 8,
        "title": "Recursive Factorial",
        "concept": "recursion",
        "description": (
            "Write a recursive function `factorial(n)` that returns n!. "
            "Print factorial(6). Do NOT use a loop."
        ),
        "example_in": "(none)",
        "example_out": "720",
        "hint1": "Base case: if n == 0 or n == 1, return 1.",
        "hint2": "Recursive case: return n * factorial(n - 1)",
        "starter": (
            "def factorial(n):\n"
            "    pass  # base case + recursive case\n\n"
            "print(factorial(6))\n"
        ),
    },
    {
        "id": "i9", "level": "intermediate", "order": 9,
        "title": "Context Manager",
        "concept": "__enter__ and __exit__",
        "description": (
            "Write a context manager class `Timer` that records how long a code block runs. "
            "Use it with `with Timer() as t:` and print the elapsed time after the block."
        ),
        "example_in": "(none)",
        "example_out": "Elapsed: 0.XXs",
        "hint1": "Implement __enter__ (start timer, return self) and __exit__ (stop timer, print).",
        "hint2": "import time; self.start = time.perf_counter() in __enter__; print in __exit__.",
        "starter": (
            "import time\n\n"
            "class Timer:\n"
            "    def __enter__(self):\n"
            "        self.start = time.perf_counter()\n"
            "        return self\n\n"
            "    def __exit__(self, *args):\n"
            "        pass  # calculate and print elapsed\n\n"
            "with Timer():\n"
            "    total = sum(range(5_000_000))\n"
        ),
    },

    # ── ADVANCED (20–29) ──────────────────────────────────────────────────────

    {
        "id": "a0", "level": "advanced", "order": 0,
        "title": "Typed Stack",
        "concept": "generics and type hints",
        "description": (
            "Implement a generic Stack[T] class using Python's typing module. "
            "It should support push(item), pop() -> T, peek() -> T, and is_empty() -> bool. "
            "Demonstrate with a Stack[int]."
        ),
        "example_in": "(none)",
        "example_out": "3\n2\nFalse",
        "hint1": "from typing import Generic, TypeVar; T = TypeVar('T'); class Stack(Generic[T]):",
        "hint2": "Store items in a list self._items: list[T] = []",
        "starter": (
            "from typing import Generic, TypeVar\n\n"
            "T = TypeVar('T')\n\n"
            "class Stack(Generic[T]):\n"
            "    def __init__(self) -> None:\n"
            "        self._items: list[T] = []\n\n"
            "    def push(self, item: T) -> None: ...\n"
            "    def pop(self) -> T: ...\n"
            "    def peek(self) -> T: ...\n"
            "    def is_empty(self) -> bool: ...\n\n"
            "s: Stack[int] = Stack()\n"
            "s.push(1); s.push(2); s.push(3)\n"
            "print(s.pop())   # 3\n"
            "print(s.peek())  # 2\n"
            "print(s.is_empty())  # False\n"
        ),
    },
    {
        "id": "a1", "level": "advanced", "order": 1,
        "title": "Async HTTP Fetch",
        "concept": "asyncio and aiohttp",
        "description": (
            "Write an async function `fetch_urls(urls)` that fetches multiple URLs "
            "concurrently using asyncio.gather(). Print status codes. "
            "Use httpx (available without install in this environment) or mock it."
        ),
        "example_in": "(none)",
        "example_out": "https://httpbin.org/get -> 200\nhttps://httpbin.org/status/404 -> 404",
        "hint1": "import asyncio; define async def fetch_one(url) using httpx.AsyncClient.",
        "hint2": "results = await asyncio.gather(*[fetch_one(u) for u in urls])",
        "starter": (
            "import asyncio\n\n"
            "async def fetch_urls(urls: list[str]) -> list[tuple[str, int]]:\n"
            "    \"\"\"Fetch all URLs concurrently, return (url, status_code) pairs.\"\"\"\n"
            "    # Try using httpx.AsyncClient or simulate with asyncio.sleep\n"
            "    results = []\n"
            "    # your async code here\n"
            "    return results\n\n"
            "# Simulate if no network access:\n"
            "async def fetch_one(url: str) -> tuple[str, int]:\n"
            "    await asyncio.sleep(0.01)  # simulate latency\n"
            "    return url, 200  # mock\n\n"
            "async def main():\n"
            "    urls = ['https://example.com/a', 'https://example.com/b']\n"
            "    results = await asyncio.gather(*[fetch_one(u) for u in urls])\n"
            "    for url, status in results:\n"
            "        print(f'{url} -> {status}')\n\n"
            "asyncio.run(main())\n"
        ),
    },
    {
        "id": "a2", "level": "advanced", "order": 2,
        "title": "LRU Cache",
        "concept": "functools.lru_cache and memoization",
        "description": (
            "Implement the Fibonacci sequence two ways: "
            "1) naive recursion (measure time for fib(35)), "
            "2) with @functools.lru_cache. Compare the speeds."
        ),
        "example_in": "(none)",
        "example_out": "Naive fib(35): 9227465 in ~1.5s\nCached fib(35): 9227465 in ~0.00001s",
        "hint1": "import functools; add @functools.lru_cache(maxsize=None) above the function.",
        "hint2": "Use time.perf_counter() before and after each call to measure elapsed time.",
        "starter": (
            "import functools\nimport time\n\n"
            "def fib_naive(n):\n"
            "    if n <= 1: return n\n"
            "    return fib_naive(n-1) + fib_naive(n-2)\n\n"
            "@functools.lru_cache(maxsize=None)\n"
            "def fib_cached(n):\n"
            "    if n <= 1: return n\n"
            "    return fib_cached(n-1) + fib_cached(n-2)\n\n"
            "# Time both and print comparison\n"
            "N = 35\n"
            "t0 = time.perf_counter()\n"
            "r1 = fib_naive(N)\n"
            "print(f'Naive  fib({N}): {r1} in {time.perf_counter()-t0:.4f}s')\n\n"
            "t0 = time.perf_counter()\n"
            "r2 = fib_cached(N)\n"
            "print(f'Cached fib({N}): {r2} in {time.perf_counter()-t0:.8f}s')\n"
        ),
    },
    {
        "id": "a3", "level": "advanced", "order": 3,
        "title": "Dataclass Validation",
        "concept": "dataclasses and __post_init__",
        "description": (
            "Create a `@dataclass` called `User` with fields: "
            "name: str, age: int, email: str. "
            "In __post_init__, validate that age >= 0 and email contains '@'. "
            "Raise ValueError for invalid data."
        ),
        "example_in": "(none)",
        "example_out": "User(name='Alice', age=30, email='alice@example.com')\nValueError: Invalid email",
        "hint1": "from dataclasses import dataclass; add @dataclass above the class definition.",
        "hint2": "def __post_init__(self): if '@' not in self.email: raise ValueError('Invalid email')",
        "starter": (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class User:\n"
            "    name: str\n"
            "    age: int\n"
            "    email: str\n\n"
            "    def __post_init__(self):\n"
            "        pass  # add validation here\n\n"
            "# Test valid user\n"
            "u = User('Alice', 30, 'alice@example.com')\n"
            "print(u)\n\n"
            "# Test invalid user\n"
            "try:\n"
            "    bad = User('Bob', 25, 'not-an-email')\n"
            "except ValueError as e:\n"
            "    print(f'ValueError: {e}')\n"
        ),
    },
    {
        "id": "a4", "level": "advanced", "order": 4,
        "title": "Iterator Protocol",
        "concept": "__iter__ and __next__",
        "description": (
            "Implement a class `CountUp` that acts as an iterator, yielding integers "
            "from `start` to `stop` (inclusive). Use the iterator protocol (__iter__ + __next__)."
        ),
        "example_in": "(none)",
        "example_out": "1 2 3 4 5",
        "hint1": "__iter__ should return self; __next__ should return the next value or raise StopIteration.",
        "hint2": "Keep self.current = start in __init__; increment and return it in __next__.",
        "starter": (
            "class CountUp:\n"
            "    def __init__(self, start: int, stop: int):\n"
            "        self.current = start\n"
            "        self.stop = stop\n\n"
            "    def __iter__(self):\n"
            "        return self\n\n"
            "    def __next__(self):\n"
            "        pass  # return next value or raise StopIteration\n\n"
            "print(*CountUp(1, 5))\n"
        ),
    },
    {
        "id": "a5", "level": "advanced", "order": 5,
        "title": "Property and Setter",
        "concept": "@property and validation",
        "description": (
            "Create a class `Temperature` with a private `_celsius` attribute. "
            "Add a `celsius` property with a setter that raises ValueError if < -273.15. "
            "Add a `fahrenheit` read-only property."
        ),
        "example_in": "(none)",
        "example_out": "100°C = 212.0°F\nValueError: Temperature below absolute zero",
        "hint1": "Use @property for the getter and @celsius.setter for the setter.",
        "hint2": "fahrenheit = celsius * 9/5 + 32",
        "starter": (
            "class Temperature:\n"
            "    def __init__(self, celsius: float = 0.0):\n"
            "        self.celsius = celsius  # triggers setter\n\n"
            "    @property\n"
            "    def celsius(self) -> float:\n"
            "        return self._celsius\n\n"
            "    @celsius.setter\n"
            "    def celsius(self, value: float) -> None:\n"
            "        pass  # validate and store\n\n"
            "    @property\n"
            "    def fahrenheit(self) -> float:\n"
            "        pass  # return converted value\n\n"
            "t = Temperature(100)\n"
            "print(f'{t.celsius}°C = {t.fahrenheit}°F')\n"
            "try:\n"
            "    t.celsius = -300\n"
            "except ValueError as e:\n"
            "    print(f'ValueError: {e}')\n"
        ),
    },
    {
        "id": "a6", "level": "advanced", "order": 6,
        "title": "Singleton via Metaclass",
        "concept": "metaclasses",
        "description": (
            "Implement a `SingletonMeta` metaclass that ensures only one instance of "
            "a class is ever created. Demonstrate with a `Config` class."
        ),
        "example_in": "(none)",
        "example_out": "True",
        "hint1": "Override __call__ in the metaclass to check if an instance already exists.",
        "hint2": (
            "class SingletonMeta(type): _instances = {}; "
            "def __call__(cls, *a, **kw): if cls not in cls._instances: ..."
        ),
        "starter": (
            "class SingletonMeta(type):\n"
            "    _instances = {}\n\n"
            "    def __call__(cls, *args, **kwargs):\n"
            "        pass  # return existing or create new\n\n"
            "class Config(metaclass=SingletonMeta):\n"
            "    def __init__(self):\n"
            "        self.debug = False\n\n"
            "a = Config()\n"
            "b = Config()\n"
            "print(a is b)  # True\n"
        ),
    },
    {
        "id": "a7", "level": "advanced", "order": 7,
        "title": "Descriptor Protocol",
        "concept": "__get__, __set__, __delete__",
        "description": (
            "Implement a `Positive` descriptor that only allows positive numbers to be assigned. "
            "Use it in a `Circle` class for the `radius` attribute."
        ),
        "example_in": "(none)",
        "example_out": "Area: 78.54\nValueError: Value must be positive",
        "hint1": "A descriptor is an object that implements __get__ and/or __set__.",
        "hint2": "Store values in instance.__dict__ using the attribute name as key.",
        "starter": (
            "import math\n\n"
            "class Positive:\n"
            "    def __set_name__(self, owner, name):\n"
            "        self.name = name\n\n"
            "    def __get__(self, obj, objtype=None):\n"
            "        if obj is None: return self\n"
            "        return obj.__dict__.get(self.name, 0)\n\n"
            "    def __set__(self, obj, value):\n"
            "        pass  # validate and store\n\n"
            "class Circle:\n"
            "    radius = Positive()\n\n"
            "    def __init__(self, radius):\n"
            "        self.radius = radius\n\n"
            "    def area(self):\n"
            "        return round(math.pi * self.radius ** 2, 2)\n\n"
            "c = Circle(5)\n"
            "print(f'Area: {c.area()}')\n"
            "try:\n"
            "    c.radius = -1\n"
            "except ValueError as e:\n"
            "    print(f'ValueError: {e}')\n"
        ),
    },
    {
        "id": "a8", "level": "advanced", "order": 8,
        "title": "Custom Exception Hierarchy",
        "concept": "exception design",
        "description": (
            "Design a small exception hierarchy for a banking app: "
            "BankError (base) → InsufficientFundsError, AccountLockedError. "
            "Implement a `withdraw(amount)` function that raises the appropriate error."
        ),
        "example_in": "(none)",
        "example_out": "Withdrew £50\nInsufficient funds: need £200 but only £50 available\nAccount is locked",
        "hint1": "Inherit custom exceptions from Exception (or from each other for hierarchy).",
        "hint2": "class InsufficientFundsError(BankError): def __init__(self, needed, available): ...",
        "starter": (
            "class BankError(Exception): pass\n\n"
            "class InsufficientFundsError(BankError):\n"
            "    def __init__(self, needed, available):\n"
            "        super().__init__(f'need £{needed} but only £{available} available')\n\n"
            "class AccountLockedError(BankError): pass\n\n"
            "def withdraw(amount: float, balance: float, locked: bool = False) -> float:\n"
            "    pass  # raise errors or return new balance\n\n"
            "# Tests\n"
            "try:\n"
            "    bal = withdraw(50, 100)\n"
            "    print(f'Withdrew £50')\n"
            "    bal = withdraw(200, bal)\n"
            "except InsufficientFundsError as e:\n"
            "    print(f'Insufficient funds: {e}')\n\n"
            "try:\n"
            "    withdraw(10, 100, locked=True)\n"
            "except AccountLockedError:\n"
            "    print('Account is locked')\n"
        ),
    },
    {
        "id": "a9", "level": "advanced", "order": 9,
        "title": "Abstract Base Class",
        "concept": "abc.ABC and abstract methods",
        "description": (
            "Using `abc.ABC`, create an abstract class `Shape` with abstract methods "
            "area() and perimeter(). Implement `Circle` and `Square` subclasses. "
            "Show that instantiating Shape directly raises TypeError."
        ),
        "example_in": "(none)",
        "example_out": "Circle area: 78.54, perimeter: 31.42\nSquare area: 25, perimeter: 20\nTypeError: Can't instantiate abstract class",
        "hint1": "from abc import ABC, abstractmethod; decorate each abstract method with @abstractmethod.",
        "hint2": "Subclasses MUST implement all abstract methods or they also become abstract.",
        "starter": (
            "import math\n"
            "from abc import ABC, abstractmethod\n\n"
            "class Shape(ABC):\n"
            "    @abstractmethod\n"
            "    def area(self) -> float: ...\n\n"
            "    @abstractmethod\n"
            "    def perimeter(self) -> float: ...\n\n"
            "class Circle(Shape):\n"
            "    def __init__(self, r): self.r = r\n"
            "    def area(self): pass\n"
            "    def perimeter(self): pass\n\n"
            "class Square(Shape):\n"
            "    def __init__(self, s): self.s = s\n"
            "    def area(self): pass\n"
            "    def perimeter(self): pass\n\n"
            "c = Circle(5)\n"
            "print(f'Circle area: {round(c.area(),2)}, perimeter: {round(c.perimeter(),2)}')\n"
            "s = Square(5)\n"
            "print(f'Square area: {s.area()}, perimeter: {s.perimeter()}')\n"
            "try:\n"
            "    Shape()\n"
            "except TypeError as e:\n"
            "    print(f'TypeError: {str(e)[:40]}')\n"
        ),
    },
]


# ── Helper functions ───────────────────────────────────────────────────────────

def get_problems_for_level(level: str) -> list[dict]:
    """Return problems for the given level sorted by difficulty order."""
    return sorted(
        [p for p in _PROBLEMS if p["level"] == level],
        key=lambda p: p["order"],
    )


def get_next_problem(level: str, done_ids: set) -> dict | None:
    """Return the next unsolved problem for this level, or None if all done."""
    for problem in get_problems_for_level(level):
        if problem["id"] not in done_ids:
            return problem
    return None


def get_level_progress(level: str, done_ids: set) -> tuple[int, int]:
    """Return (done_count, total_count) for the given level."""
    problems = get_problems_for_level(level)
    done = sum(1 for p in problems if p["id"] in done_ids)
    return done, len(problems)
