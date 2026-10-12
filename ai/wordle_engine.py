# ai/wordle_engine.py — Information-Theoretic Shannon Entropy Wordle Engine
import math
from collections import Counter


# 5-letter vocabulary curated from General Knowledge and common standard English words
GK_WORDLE_TARGETS = [
    "PARIS", "EARTH", "SOLAR", "HEART", "POUND",
    "DELHI", "OCEAN", "OZONE", "RIVER", "LIGHT",
    "VENUS", "WATER", "BRAIN", "RADAR", "PLANT",
    "TIGER", "INDIA", "TOWER", "LASER", "STORM",
    "GRAVY", "LUNAR", "MANGO", "NOBEL", "PIANO",
]

# Standard allowed 5-letter guess lexicon
ALLOWED_GUESSES = set(GK_WORDLE_TARGETS).union({
    "ABOUT", "ABOVE", "ACTOR", "ADULT", "AFTER", "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM",
    "ALBUM", "ALERT", "ALIEN", "ALIGN", "ALIKE", "ALIVE", "ALLOW", "ALONE", "ALONG", "ALPHA",
    "ALTER", "AMONG", "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY", "ARENA",
    "ARGUE", "ARISE", "ARRAY", "ARROW", "ASIDE", "ASSET", "AUDIO", "AUDIT", "AVOID", "AWAIT",
    "AWAKE", "AWARD", "AWARE", "BADLY", "BAKER", "BASIC", "BASIS", "BEACH", "BEGIN", "BEING",
    "BELOW", "BENCH", "BIRTH", "BLACK", "BLAME", "BLIND", "BLOCK", "BLOOD", "BOARD", "BOAST",
    "BOOST", "BOOTH", "BOUND", "BRAIN", "BRAND", "BREAD", "BREAK", "BREED", "BRIEF", "BRING",
    "BROAD", "BROWN", "BUILD", "BUILT", "BUYER", "CABLE", "CALIF", "CARRY", "CATCH", "CAUSE",
    "CHAIN", "CHAIR", "CHART", "CHASE", "CHEAP", "CHECK", "CHEST", "CHIEF", "CHILD", "CHINA",
    "CHOSE", "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLICK", "CLOCK", "CLOSE", "COACH",
    "COAST", "COULD", "COUNT", "COURT", "COVER", "CRAFT", "CRANE", "CRASH", "CREAM", "CRIME",
    "CROSS", "CROWD", "CROWN", "CURVE", "CYCLE", "DAILY", "DANCE", "DATED", "DEALT", "DEATH",
    "DEBUT", "DELAY", "DEPTH", "DOING", "DOUBT", "DOZEN", "DRAFT", "DRAMA", "DRAWN", "DREAM",
    "DRESS", "DRILL", "DRINK", "DRIVE", "DROVE", "DYING", "EAGER", "EARLY", "EARTH", "EIGHT",
    "ELITE", "EMPTY", "ENEMY", "ENJOY", "ENTER", "ENTRY", "EQUAL", "ERROR", "EVENT", "EVERY",
    "EXACT", "EXIST", "EXTRA", "FAITH", "FALSE", "FAULT", "FIBER", "FIELD", "FIFTH", "FIFTY",
    "FIGHT", "FINAL", "FIRST", "FIXED", "FLASH", "FLEET", "FLOOR", "FLUID", "FOCUS", "FORCE",
    "FORTH", "FORTY", "FORUM", "FOUND", "FRAME", "FRANK", "FRAUD", "FRESH", "FRONT", "FRUIT",
    "FULLY", "FUNNY", "GIANT", "GIVEN", "GLASS", "GLOBE", "GOING", "GRACE", "GRADE", "GRAND",
    "GRANT", "GRASS", "GREAT", "GREEN", "GROSS", "GROUP", "GROWN", "GUARD", "GUESS", "GUEST",
    "GUIDE", "HAPPY", "HARRY", "HEART", "HEAVY", "HENCE", "HORSE", "HOTEL", "HOUSE", "HUMAN",
    "IDEAL", "IMAGE", "INDEX", "INNER", "INPUT", "ISSUE", "JAPAN", "JOINT", "JUDGE", "JUICE",
    "KNOWN", "LABEL", "LARGE", "LASER", "LATER", "LAUGH", "LAYER", "LEARN", "LEASE", "LEAST",
    "LEAVE", "LEGAL", "LEVEL", "LIGHT", "LIMIT", "LOCAL", "LOGIC", "LOOSE", "LOWER", "LUCKY",
    "LUNCH", "LYING", "MAGIC", "MAJOR", "MAKER", "MARCH", "MATCH", "MAYBE", "MAYOR", "MEANT",
    "MEDIA", "METAL", "MIGHT", "MINOR", "MINUS", "MIXED", "MODEL", "MONEY", "MONTH", "MORAL",
    "MOTOR", "MOUNT", "MOUSE", "MOUTH", "MOVIE", "MUSIC", "NEEDS", "NEVER", "NIGHT", "NOISE",
    "NORTH", "NOTED", "NOVEL", "NURSE", "OCCUR", "OCEAN", "OFFER", "OFTEN", "ORDER", "OTHER",
    "OUGHT", "PAINT", "PANEL", "PAPER", "PARTY", "PEACE", "PETER", "PHASE", "PHONE", "PHOTO",
    "PIECE", "PILOT", "PITCH", "PLACE", "PLAIN", "PLANE", "PLANT", "PLATE", "POINT", "POUND",
    "POWER", "PRESS", "PRICE", "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE", "PROOF", "PROUD",
    "PROVE", "QUEEN", "QUICK", "QUIET", "QUITE", "RADIO", "RAISE", "RANGE", "RAPID", "RATIO",
    "REACH", "READY", "REFER", "RIGHT", "RIVAL", "RIVER", "ROBIN", "ROGER", "ROMAN", "ROUGH",
    "ROUND", "ROUTE", "ROYAL", "RURAL", "SCALE", "SCENE", "SCOPE", "SCORE", "SENSE", "SERVE",
    "SEVEN", "SHALL", "SHAPE", "SHARE", "SHARP", "SHEET", "SHELF", "SHELL", "SHIFT", "SHIRT",
    "SHOCK", "SHOOT", "SHORT", "SHOWN", "SIGHT", "SINCE", "SIXTH", "SIXTY", "SIZED", "SKILL",
    "SLEEP", "SLIDE", "SMALL", "SMART", "SMILE", "SMITH", "SMOKE", "SOLID", "SOLVE", "SORRY",
    "SOUND", "SOUTH", "SPACE", "SPARE", "SPEAK", "SPEED", "SPEND", "SPENT", "SPLIT", "SPOKE",
    "SPORT", "STAFF", "STAGE", "STAKE", "STAND", "START", "STATE", "STEAM", "STEEL", "STICK",
    "STILL", "STOCK", "STONE", "STOOD", "STORE", "STORM", "STORY", "STRIP", "STUCK", "STUDY",
    "STUFF", "STYLE", "SUGAR", "SUITE", "SUPER", "SWEET", "TABLE", "TAKEN", "TASTE", "TAXES",
    "TEACH", "TEETH", "TERRY", "TEXAS", "THANK", "THEFT", "THEIR", "THEME", "THERE", "THESE",
    "THICK", "THING", "THINK", "THIRD", "THOSE", "THREE", "THREW", "THROW", "TIGHT", "TIMES",
    "TIRED", "TITLE", "TODAY", "TOPIC", "TOTAL", "TOUCH", "TOUGH", "TOWER", "TRACK", "TRADE",
    "TRAIN", "TREAT", "TREND", "TRIAL", "TRIED", "TRIES", "TRUCK", "TRULY", "TRUST", "TRUTH",
    "TWICE", "UNDER", "UNDUE", "UNION", "UNITY", "UNTIL", "UPPER", "UPSET", "URBAN", "USAGE",
    "USUAL", "VALID", "VALUE", "VIDEO", "VIRUS", "VISIT", "VITAL", "VOICE", "WASTE", "WATCH",
    "WATER", "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WOMAN", "WOMEN",
    "WORLD", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WOUND", "WRITE", "WRONG", "WROTE",
    "YIELD", "YOUNG", "YOUTH"
})


# Pattern color representations
COLOR_ABSENT = 0    # Gray / Slate
COLOR_PRESENT = 1   # Yellow (letter in word, wrong position)
COLOR_CORRECT = 2   # Green (correct letter in exact position)


def evaluate_guess(guess: str, target: str) -> tuple[int, ...]:
    """
    Evaluates a 5-letter guess against a target word using standard Wordle rules.
    Properly handles duplicate letters by marking greens first, then yellows.
    Returns a tuple of 5 pattern integers (0=absent, 1=present, 2=correct).
    """
    guess = guess.upper()
    target = target.upper()
    result = [COLOR_ABSENT] * 5
    target_letter_counts = Counter(target)

    # First pass: find exact matches (Greens)
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = COLOR_CORRECT
            target_letter_counts[guess[i]] -= 1

    # Second pass: find partial matches (Yellows)
    for i in range(5):
        if result[i] == COLOR_CORRECT:
            continue
        g_char = guess[i]
        if target_letter_counts.get(g_char, 0) > 0:
            result[i] = COLOR_PRESENT
            target_letter_counts[g_char] -= 1

    return tuple(result)


def filter_candidates(candidates: list[str], guess: str, pattern: tuple[int, ...]) -> list[str]:
    """Prunes candidate pool to only words that produce the exact pattern for the guess."""
    return [word for word in candidates if evaluate_guess(guess, word) == pattern]


def calculate_entropy(guess: str, candidates: list[str]) -> float:
    """
    Computes Shannon Entropy H(guess) in bits over the remaining candidate distribution:
        E[I(guess)] = sum_{p} P(p) * log2(1 / P(p))
    """
    if not candidates:
        return 0.0

    total = len(candidates)
    pattern_counts: Counter[tuple[int, ...]] = Counter()

    for word in candidates:
        pat = evaluate_guess(guess, word)
        pattern_counts[pat] += 1

    entropy = 0.0
    for count in pattern_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def get_best_hint(candidates: list[str], search_pool: list[str] | None = None) -> tuple[str, float]:
    """
    Finds the guess with the highest Shannon Entropy (maximum expected information gain).
    """
    if not candidates:
        return ("PARIS", 0.0)
    if len(candidates) == 1:
        return (candidates[0], 0.0)

    # Use candidates pool if search pool not provided
    pool = search_pool if search_pool else candidates
    best_word = pool[0]
    best_entropy = -1.0

    for word in pool:
        ent = calculate_entropy(word, candidates)
        if ent > best_entropy:
            best_entropy = ent
            best_word = word

    return (best_word, best_entropy)
