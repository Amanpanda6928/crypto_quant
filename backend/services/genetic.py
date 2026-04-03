# Genetic Algorithm for Strategy Optimization
import numpy as np
import random
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from portfolio_engine import run_portfolio, calculate_portfolio_metrics

class GeneticOptimizer:
    """Genetic Algorithm for Portfolio Strategy Optimization"""
    
    def __init__(self, population_size=50, generations=100, mutation_rate=0.1, crossover_rate=0.8):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = int(population_size * 0.1)  # Top 10% preserved
        
    def random_individual(self, num_strategies):
        """Generate random individual (strategy weights)"""
        weights = np.random.random(num_strategies)
        return weights / np.sum(weights)  # Normalize
    
    def fitness_function(self, individual, prices, strategies):
        """Calculate fitness (final balance) for an individual"""
        weights_dict = {strategy: weight for strategy, weight in zip(strategies, individual)}
        
        try:
            result = run_portfolio(prices, weights_dict, strategies)
            return result['final_balance']
        except:
            return 10000  # Return initial balance if error
    
    def tournament_selection(self, population, fitness_scores, tournament_size=3):
        """Tournament selection for choosing parents"""
        selected = []
        
        for _ in range(len(population)):
            # Random tournament participants
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            
            # Select winner (highest fitness)
            winner_index = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(population[winner_index])
        
        return selected
    
    def crossover(self, parent1, parent2):
        """Crossover operation to create offspring"""
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        # Single-point crossover
        crossover_point = random.randint(1, len(parent1) - 1)
        
        child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
        child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])
        
        # Normalize children
        child1 = child1 / np.sum(child1)
        child2 = child2 / np.sum(child2)
        
        return child1, child2
    
    def mutate(self, individual):
        """Mutation operation"""
        if random.random() > self.mutation_rate:
            return individual.copy()
        
        # Random mutation
        mutation_point = random.randint(0, len(individual) - 1)
        mutation_value = np.random.normal(0, 0.1)  # Small random change
        
        individual[mutation_point] += mutation_value
        individual = np.abs(individual)  # Ensure non-negative
        individual = individual / np.sum(individual)  # Renormalize
        
        return individual
    
    def optimize(self, prices, strategies):
        """Main genetic optimization loop"""
        num_strategies = len(strategies)
        
        # Initialize population
        population = [self.random_individual(num_strategies) for _ in range(self.population_size)]
        
        best_individual = None
        best_fitness = 0
        evolution_history = []
        
        for generation in range(self.generations):
            # Calculate fitness for entire population
            fitness_scores = [self.fitness_function(ind, prices, strategies) for ind in population]
            
            # Track best individual
            current_best_idx = np.argmax(fitness_scores)
            current_best_fitness = fitness_scores[current_best_idx]
            
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_individual = population[current_best_idx].copy()
            
            # Store generation statistics
            avg_fitness = np.mean(fitness_scores)
            evolution_history.append({
                "generation": generation + 1,
                "best_fitness": current_best_fitness,
                "average_fitness": avg_fitness,
                "best_weights": population[current_best_idx].tolist()
            })
            
            print(f"Generation {generation + 1}: Best = {current_best_fitness:.2f}, Avg = {avg_fitness:.2f}")
            
            # Selection
            selected_parents = self.tournament_selection(population, fitness_scores)
            
            # Create next generation
            next_generation = []
            
            # Elitism - preserve best individuals
            elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
            for idx in elite_indices:
                next_generation.append(population[idx].copy())
            
            # Crossover and mutation
            while len(next_generation) < self.population_size:
                parent1, parent2 = random.sample(selected_parents, 2)
                child1, child2 = self.crossover(parent1, parent2)
                
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                next_generation.append(child1)
                if len(next_generation) < self.population_size:
                    next_generation.append(child2)
            
            population = next_generation
        
        # Calculate final metrics for best individual
        best_weights_dict = {strategy: weight for strategy, weight in zip(strategies, best_individual)}
        final_result = run_portfolio(prices, best_weights_dict, strategies)
        final_metrics = calculate_portfolio_metrics(final_result["equity"])
        
        return {
            "best_weights": best_weights_dict,
            "best_individual": best_individual.tolist(),
            "best_fitness": best_fitness,
            "final_balance": final_result["final_balance"],
            "total_return": final_metrics["total_return"],
            "sharpe_ratio": final_metrics["sharpe_ratio"],
            "max_drawdown": final_metrics["max_drawdown"],
            "evolution_history": evolution_history,
            "generations": self.generations,
            "population_size": self.population_size
        }

def multi_objective_genetic(prices, strategies):
    """
    Multi-objective genetic algorithm optimizing both return and risk
    """
    class MultiObjectiveGA(GeneticOptimizer):
        def fitness_function(self, individual, prices, strategies):
            """Multi-objective fitness: maximize return, minimize risk"""
            weights_dict = {strategy: weight for strategy, weight in zip(strategies, individual)}
            
            try:
                result = run_portfolio(prices, weights_dict, strategies)
                metrics = calculate_portfolio_metrics(result["equity"])
                
                # Combine objectives (you can use Pareto ranking)
                return_score = metrics["total_return"] - (metrics["max_drawdown"] * 0.5)
                return return_score
            except:
                return 0
    
    ga = MultiObjectiveGA(population_size=100, generations=150)
    return ga.optimize(prices, strategies)

def adaptive_genetic(prices, strategies):
    """
    Adaptive genetic algorithm with dynamic parameters
    """
    class AdaptiveGA(GeneticOptimizer):
        def __init__(self):
            super().__init__()
            self.initial_mutation_rate = 0.1
            self.initial_crossover_rate = 0.8
            self.diversity_threshold = 0.01
        
        def calculate_diversity(self, population):
            """Calculate population diversity"""
            if len(population) < 2:
                return 0
            
            diversity = 0
            for i in range(len(population)):
                for j in range(i + 1, len(population)):
                    diversity += np.sum(np.abs(population[i] - population[j]))
            
            return diversity / (len(population) * (len(population) - 1))
        
        def adapt_parameters(self, population, generation):
            """Adapt mutation and crossover rates based on diversity"""
            diversity = self.calculate_diversity(population)
            
            if diversity < self.diversity_threshold:
                # Low diversity - increase mutation
                self.mutation_rate = min(0.3, self.initial_mutation_rate * 1.5)
                self.crossover_rate = max(0.5, self.initial_crossover_rate * 0.8)
            else:
                # Good diversity - use initial rates
                self.mutation_rate = self.initial_mutation_rate
                self.crossover_rate = self.initial_crossover_rate
            
            print(f"Generation {generation}: Diversity={diversity:.4f}, Mutation={self.mutation_rate:.3f}, Crossover={self.crossover_rate:.3f}")
    
    ga = AdaptiveGA()
    return ga.optimize(prices, strategies)

def parallel_genetic_optimization(price_data, strategies, num_runs=5):
    """
    Run multiple genetic algorithms in parallel and pick best result
    """
    results = []
    
    for run in range(num_runs):
        print(f"Running genetic algorithm {run + 1}/{num_runs}")
        ga = GeneticOptimizer(population_size=30, generations=50)
        result = ga.optimize(price_data, strategies)
        result["run_number"] = run + 1
        results.append(result)
    
    # Find best result across all runs
    best_result = max(results, key=lambda x: x["best_fitness"])
    
    return {
        "parallel_results": results,
        "best_overall": best_result,
        "num_runs": num_runs,
        "average_fitness": np.mean([r["best_fitness"] for r in results]),
        "fitness_std": np.std([r["best_fitness"] for r in results])
    }

def genetic_walk_forward(prices, strategies, window_size=200, step_size=50):
    """
    Combine genetic algorithm with walk-forward validation
    """
    results = []
    
    for i in range(window_size, len(prices) - step_size, step_size):
        train_data = prices[i-window_size:i]
        test_data = prices[i:i+step_size]
        
        print(f"Window {len(results)+1}: Optimizing on training data...")
        
        # Run genetic optimization on training data
        ga = GeneticOptimizer(population_size=20, generations=30)
        optimization_result = ga.optimize(train_data, strategies)
        
        # Test optimized weights on test data
        test_weights = optimization_result["best_weights"]
        test_result = run_portfolio(test_data, test_weights, strategies)
        test_metrics = calculate_portfolio_metrics(test_result["equity"])
        
        window_result = {
            "window": len(results) + 1,
            "train_period": f"{i-window_size}-{i}",
            "test_period": f"{i}-{i+step_size}",
            "optimized_weights": test_weights,
            "test_return": test_metrics["total_return"],
            "test_sharpe": test_metrics["sharpe_ratio"],
            "test_drawdown": test_metrics["max_drawdown"],
            "optimization_generations": 30,
            "best_training_fitness": optimization_result["best_fitness"]
        }
        
        results.append(window_result)
    
    return {
        "genetic_walk_forward": results,
        "overall_performance": calculate_walk_forward_genetic_metrics(results)
    }

def calculate_walk_forward_genetic_metrics(results):
    """Calculate metrics for genetic walk-forward results"""
    if not results:
        return {}
    
    test_returns = [r["test_return"] for r in results]
    test_sharpes = [r["test_sharpe"] for r in results]
    test_drawdowns = [r["test_drawdown"] for r in results]
    
    return {
        "average_test_return": np.mean(test_returns),
        "average_test_sharpe": np.mean(test_sharpes),
        "average_test_drawdown": np.mean(test_drawdowns),
        "return_stability": np.std(test_returns),
        "best_window": max(results, key=lambda x: x["test_return"]) if results else None,
        "worst_window": min(results, key=lambda x: x["test_return"]) if results else None,
        "success_rate": len([r for r in results if r["test_return"] > 0]) / len(results) * 100
    }

# Simple functions for basic genetic operations
def random_weights(num_strategies):
    """Generate random normalized weights"""
    weights = np.random.random(num_strategies)
    return weights / np.sum(weights)

def fitness(weights, prices, strategies):
    """Simple fitness function"""
    weights_dict = {strategy: weight for strategy, weight in zip(strategies, weights)}
    
    try:
        result = run_portfolio(prices, weights_dict, strategies)
        return result['final_balance']
    except:
        return 10000

def evolve_simple(prices, strategies, generations=10):
    """Simple evolution function"""
    population_size = 10
    population = [random_weights(len(strategies)) for _ in range(population_size)]
    
    for generation in range(generations):
        # Calculate fitness
        fitness_scores = [fitness(ind, prices, strategies) for ind in population]
        
        # Sort by fitness
        scored_population = list(zip(fitness_scores, population))
        scored_population.sort(reverse=True)
        
        # Select top 50%
        population = [ind for fit, ind in scored_population[:int(population_size/2)]]
        
        # Repopulate with mutations
        while len(population) < population_size:
            parent = random.choice(population)
            child = parent.copy()
            
            # Simple mutation
            mutation_point = random.randint(0, len(child) - 1)
            child[mutation_point] += np.random.normal(0, 0.1)
            child = np.abs(child)
            child = child / np.sum(child)
            
            population.append(child)
        
        best_fitness = scored_population[0][0]
        print(f"Generation {generation + 1}: Best fitness = {best_fitness:.2f}")
    
    return {
        "best_weights": {strategy: weight for strategy, weight in zip(strategies, scored_population[0][1])},
        "best_fitness": scored_population[0][0],
        "generations": generations
    }
