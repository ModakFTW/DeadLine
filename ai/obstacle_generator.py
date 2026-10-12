import json
import random
import os

class MarkovChain:
    """A Markov chain obstacle generator with 3 difficulty-tiered transition tables."""
    
    def __init__(self) -> None:
        """Initializes empty transition tables dict keyed by difficulty."""
        self.tables: dict[str, dict[str, dict[str, float]]] = {
            'easy': {},
            'medium': {},
            'hard': {}
        }
        self.obstacle_types: list[str] = []

    def train(self, sequences: list[list[str]]) -> None:
        """
        Trains the Markov chain based on the provided sequences and builds
        the easy, medium, and hard transition tables.
        """
        # Count transitions
        counts: dict[str, dict[str, int]] = {}
        types_set = set()
        
        for seq in sequences:
            for i in range(len(seq) - 1):
                current = seq[i]
                nxt = seq[i+1]
                types_set.add(current)
                types_set.add(nxt)
                if current not in counts:
                    counts[current] = {}
                if nxt not in counts[current]:
                    counts[current][nxt] = 0
                counts[current][nxt] += 1
                
        self.obstacle_types = list(types_set)
        
        # Build base (medium) table
        base_table: dict[str, dict[str, float]] = {}
        for current, transitions in counts.items():
            total = sum(transitions.values())
            base_table[current] = {}
            for nxt, count in transitions.items():
                base_table[current][nxt] = count / total if total > 0 else 0.0
                
        self.tables['medium'] = base_table
        
        # Build easy table
        easy_table: dict[str, dict[str, float]] = {}
        for current, transitions in base_table.items():
            easy_table[current] = {}
            for nxt, prob in transitions.items():
                new_prob = prob
                if nxt in ['gap', 'moving_platform']:
                    new_prob *= 1.5
                elif nxt in ['spike', 'enemy']:
                    new_prob *= 0.6
                easy_table[current][nxt] = new_prob
                
            # Normalize
            total = sum(easy_table[current].values())
            for nxt in easy_table[current]:
                easy_table[current][nxt] = easy_table[current][nxt] / total if total > 0 else 0.0
                
        self.tables['easy'] = easy_table
        
        # Build hard table
        hard_table: dict[str, dict[str, float]] = {}
        for current, transitions in base_table.items():
            hard_table[current] = {}
            for nxt, prob in transitions.items():
                new_prob = prob
                if nxt in ['spike', 'enemy']:
                    new_prob *= 1.5
                elif nxt in ['gap', 'moving_platform']:
                    new_prob *= 0.6
                hard_table[current][nxt] = new_prob
                
            # Normalize
            total = sum(hard_table[current].values())
            for nxt in hard_table[current]:
                hard_table[current][nxt] = hard_table[current][nxt] / total if total > 0 else 0.0
                
        self.tables['hard'] = hard_table

    def generate_next(self, current_obstacle: str, difficulty: str = 'medium') -> str:
        """
        Generates the next obstacle based on the current obstacle and difficulty.
        """
        table = self.tables.get(difficulty, self.tables['medium'])
        transitions = table.get(current_obstacle, {})
        
        if not transitions:
            # Fallback if no transitions found for current obstacle
            return random.choice(self.obstacle_types) if self.obstacle_types else ""
            
        population = list(transitions.keys())
        weights = list(transitions.values())
        return random.choices(population, weights=weights, k=1)[0]

    def get_transition_table(self, difficulty: str) -> dict:
        """Returns the transition table for the given difficulty for debug display."""
        return self.tables.get(difficulty, {})
        
    def get_obstacle_types(self) -> list[str]:
        """Returns the list of known obstacle types."""
        return self.obstacle_types


if __name__ == '__main__':
    import os
    import json
    
    # 1. Load data/training_sequences.json
    try:
        with open('data/training_sequences.json', 'r') as f:
            sequences = json.load(f)
    except FileNotFoundError:
        print("Could not find 'data/training_sequences.json'. Please ensure you are running from the project root.")
        sequences = []
        
    if sequences:
        # 2. Train the chain
        chain = MarkovChain()
        chain.train(sequences)
        
        for diff in ['easy', 'medium', 'hard']:
            print(f"\\n--- {diff.upper()} DIFFICULTY ---")
            
            # 3. Generate and print 15 obstacles for each difficulty tier
            curr = random.choice(chain.get_obstacle_types())
            res = [curr]
            for _ in range(14):
                curr = chain.generate_next(curr, diff)
                res.append(curr)
            print("Generated 15 obstacles:", res)
            
            # 4. Print the transition tables
            print(f"\\nTransition table ({diff}):")
            table = chain.get_transition_table(diff)
            for current_obs, transitions in table.items():
                print(f"  {current_obs}:")
                for next_obs, prob in transitions.items():
                    print(f"    -> {next_obs}: {prob:.3f}")
