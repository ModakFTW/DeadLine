"""adaptive_quiz/questions.py - Hardcoded question bank and startup validator."""

QUESTIONS = [
    # ── Level 1: Easy (Foundations) ──
    {
        "question": "What is 7 + 5?",
        "options": ["10", "11", "12", "13"],
        "answer": 2,
        "level": 1,
        "explanation": "7 + 5 equals 12."
    },
    {
        "question": "What is the primary binary digit representation of zero voltage or 'off'?",
        "options": ["0", "1", "-1", "null"],
        "answer": 0,
        "level": 1,
        "explanation": "In binary logic, 0 represents low voltage or false/off."
    },
    {
        "question": "How many bits are in one standard byte?",
        "options": ["4", "8", "16", "32"],
        "answer": 1,
        "level": 1,
        "explanation": "One byte consists of exactly 8 bits."
    },
    {
        "question": "What is the square root of 64?",
        "options": ["6", "7", "8", "9"],
        "answer": 2,
        "level": 1,
        "explanation": "8 multiplied by 8 equals 64."
    },
    {
        "question": "Which data structure operates on a First-In, First-Out (FIFO) basis?",
        "options": ["Stack", "Queue", "Tree", "Graph"],
        "answer": 1,
        "level": 1,
        "explanation": "A Queue services items in the order they arrived (FIFO)."
    },
    {
        "question": "What is 15 minus 8?",
        "options": ["5", "6", "7", "8"],
        "answer": 2,
        "level": 1,
        "explanation": "15 - 8 = 7."
    },
    {
        "question": "In decimal, what is 2 to the power of 3 (2^3)?",
        "options": ["6", "8", "9", "16"],
        "answer": 1,
        "level": 1,
        "explanation": "2 * 2 * 2 = 8."
    },

    # ── Level 2: Medium (Intermediate Concepts) ──
    {
        "question": "What is the decimal equivalent of the binary number 1010?",
        "options": ["8", "10", "12", "14"],
        "answer": 1,
        "level": 2,
        "explanation": "1*(8) + 0*(4) + 1*(2) + 0*(1) = 8 + 2 = 10."
    },
    {
        "question": "Which sorting algorithm typically has average-case O(n log n) time complexity?",
        "options": ["Bubble Sort", "Insertion Sort", "Merge Sort", "Selection Sort"],
        "answer": 2,
        "level": 2,
        "explanation": "Merge Sort reliably divides and merges in O(n log n) time."
    },
    {
        "question": "In Python, which built-in function returns the number of elements in a list?",
        "options": ["count()", "size()", "len()", "length()"],
        "answer": 2,
        "level": 2,
        "explanation": "len() returns the length of a sequence or collection."
    },
    {
        "question": "What is the hexadecimal equivalent of decimal 15?",
        "options": ["E", "F", "10", "A"],
        "answer": 1,
        "level": 2,
        "explanation": "Hexadecimal counts 0-9 followed by A(10), B(11), C(12), D(13), E(14), F(15)."
    },
    {
        "question": "Which logic gate outputs True (1) if and only if its two inputs differ?",
        "options": ["AND", "OR", "XOR", "NAND"],
        "answer": 2,
        "level": 2,
        "explanation": "Exclusive OR (XOR) outputs 1 when inputs are distinct."
    },
    {
        "question": "If a train travels 60 miles in 45 minutes, what is its average speed in mph?",
        "options": ["75 mph", "80 mph", "85 mph", "90 mph"],
        "answer": 1,
        "level": 2,
        "explanation": "Speed = 60 miles / 0.75 hours = 80 mph."
    },
    {
        "question": "Which data structure uses pointers/nodes where each element references the next?",
        "options": ["Array", "Linked List", "Tuple", "Bitmap"],
        "answer": 1,
        "level": 2,
        "explanation": "A Linked List connects nodes sequentially via pointer references."
    },

    # ── Level 3: Hard (Advanced Analysis) ──
    {
        "question": "What is the worst-case time complexity of quickselect algorithm for finding the k-th smallest element?",
        "options": ["O(log n)", "O(n)", "O(n log n)", "O(n^2)"],
        "answer": 3,
        "level": 3,
        "explanation": "With repeatedly poor pivot selections, quickselect degrades to O(n^2)."
    },
    {
        "question": "Which condition is NOT one of the Coffman conditions required for system deadlock?",
        "options": ["Mutual Exclusion", "Hold and Wait", "Preemption Allowed", "Circular Wait"],
        "answer": 2,
        "level": 3,
        "explanation": "Deadlock requires No Preemption; allowing preemption prevents deadlock."
    },
    {
        "question": "In a balanced AVL tree with N nodes, what is the tight asymptotic bound on height?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n^0.5)"],
        "answer": 1,
        "level": 3,
        "explanation": "AVL balance factor constraints guarantee height bounded by ~1.44 log2(N)."
    },
    {
        "question": "What is the value of 2^10?",
        "options": ["512", "1000", "1024", "2048"],
        "answer": 2,
        "level": 3,
        "explanation": "2^10 = 1024 (commonly 1 Kibibyte)."
    },
    {
        "question": "Which OSI layer is responsible for logical IP packet routing across multiple networks?",
        "options": ["Data Link (Layer 2)", "Network (Layer 3)", "Transport (Layer 4)", "Session (Layer 5)"],
        "answer": 1,
        "level": 3,
        "explanation": "Network Layer 3 handles end-to-end IP routing."
    },
    {
        "question": "What is the derivative of f(x) = 3x^2 + 5x with respect to x?",
        "options": ["6x + 5", "3x + 5", "6x^2 + 5", "x^3 + 5x"],
        "answer": 0,
        "level": 3,
        "explanation": "d/dx(3x^2) = 6x and d/dx(5x) = 5, yielding 6x + 5."
    },
    {
        "question": "In relational databases, which normal form eliminates transitive dependencies?",
        "options": ["1NF", "2NF", "3NF", "BCNF"],
        "answer": 2,
        "level": 3,
        "explanation": "Third Normal Form (3NF) requires 2NF plus no transitive functional dependencies."
    }
]


def validate_questions(questions: list[dict]) -> None:
    """Validates question bank schema at startup.

    Raises ValueError with a clear, helpful explanation if corrupted.
    """
    if not isinstance(questions, list) or len(questions) < 15:
        raise ValueError(
            f"Question bank must contain at least 15 questions. Found {len(questions) if isinstance(questions, list) else 0}."
        )

    levels_found = set()
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f"Question #{idx+1} is not a dictionary.")

        # Question text
        if "question" not in q or not isinstance(q["question"], str) or not q["question"].strip():
            raise ValueError(f"Question #{idx+1} is missing valid 'question' text.")

        # Options
        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Question #{idx+1} must contain exactly 4 options. Found: {options}")
        for opt_idx, opt in enumerate(options):
            if not isinstance(opt, str) or not opt.strip():
                raise ValueError(f"Question #{idx+1} option #{opt_idx+1} must be a non-empty string.")

        # Answer
        answer = q.get("answer")
        if not isinstance(answer, int) or answer not in (0, 1, 2, 3):
            raise ValueError(f"Question #{idx+1} 'answer' must be an integer index in 0..3. Got: {answer}")

        # Level
        lvl = q.get("level")
        if not isinstance(lvl, int) or lvl not in (1, 2, 3):
            raise ValueError(f"Question #{idx+1} 'level' must be 1, 2, or 3. Got: {lvl}")
        levels_found.add(lvl)

        # Explanation
        explanation = q.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(f"Question #{idx+1} is missing a valid non-empty 'explanation'.")

    # Ensure all 3 difficulty tiers exist
    missing_levels = {1, 2, 3} - levels_found
    if missing_levels:
        raise ValueError(f"Question bank must have questions for all 3 levels. Missing: {missing_levels}")
