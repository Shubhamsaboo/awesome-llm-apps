#!/usr/bin/env python3
"""
Simple performance monitor for tracking quiz generation metrics.
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class GenerationMetrics:
    """Track quiz generation performance metrics."""
    model_name: str
    question_type: str
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    total_time: float = 0.0
    json_parse_failures: int = 0
    validation_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.successes / self.attempts * 100) if self.attempts > 0 else 0.0
    
    @property
    def avg_time(self) -> float:
        """Calculate average generation time."""
        return (self.total_time / self.successes) if self.successes > 0 else 0.0

class PerformanceMonitor:
    """Monitor and track quiz generation performance."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.metrics: Dict[str, GenerationMetrics] = {}
        self.log_file = Path(log_file) if log_file else Path("quiz_performance.json")
        self.load_existing_metrics()
    
    def get_key(self, model_name: str, question_type: str) -> str:
        """Generate key for metrics storage."""
        return f"{model_name}_{question_type}"
    
    def start_generation(self, model_name: str, question_type: str) -> str:
        """Start tracking a generation attempt."""
        key = self.get_key(model_name, question_type)
        
        if key not in self.metrics:
            self.metrics[key] = GenerationMetrics(
                model_name=model_name,
                question_type=question_type
            )
        
        self.metrics[key].attempts += 1
        return key
    
    def record_success(self, key: str, generation_time: float):
        """Record a successful generation."""
        if key in self.metrics:
            self.metrics[key].successes += 1
            self.metrics[key].total_time += generation_time
    
    def record_failure(self, key: str, failure_type: str = "general"):
        """Record a failed generation."""
        if key in self.metrics:
            self.metrics[key].failures += 1
            
            if failure_type == "json_parse":
                self.metrics[key].json_parse_failures += 1
            elif failure_type == "validation":
                self.metrics[key].validation_failures += 1
    
    def get_summary(self) -> Dict:
        """Get performance summary."""
        summary = {
            "total_attempts": sum(m.attempts for m in self.metrics.values()),
            "total_successes": sum(m.successes for m in self.metrics.values()),
            "overall_success_rate": 0.0,
            "by_model": {},
            "by_question_type": {}
        }
        
        if summary["total_attempts"] > 0:
            summary["overall_success_rate"] = (
                summary["total_successes"] / summary["total_attempts"] * 100
            )
        
        # Group by model
        models = set(m.model_name for m in self.metrics.values())
        for model in models:
            model_metrics = [m for m in self.metrics.values() if m.model_name == model]
            model_attempts = sum(m.attempts for m in model_metrics)
            model_successes = sum(m.successes for m in model_metrics)
            
            summary["by_model"][model] = {
                "attempts": model_attempts,
                "successes": model_successes,
                "success_rate": (model_successes / model_attempts * 100) if model_attempts > 0 else 0.0,
                "avg_time": sum(m.total_time for m in model_metrics) / model_successes if model_successes > 0 else 0.0
            }
        
        # Group by question type
        q_types = set(m.question_type for m in self.metrics.values())
        for q_type in q_types:
            type_metrics = [m for m in self.metrics.values() if m.question_type == q_type]
            type_attempts = sum(m.attempts for m in type_metrics)
            type_successes = sum(m.successes for m in type_metrics)
            
            summary["by_question_type"][q_type] = {
                "attempts": type_attempts,
                "successes": type_successes,
                "success_rate": (type_successes / type_attempts * 100) if type_attempts > 0 else 0.0
            }
        
        return summary
    
    def load_existing_metrics(self):
        """Load existing metrics from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    for key, metric_data in data.items():
                        self.metrics[key] = GenerationMetrics(**metric_data)
                logger.info(f"Loaded {len(self.metrics)} existing metrics")
            except Exception as e:
                logger.warning(f"Could not load existing metrics: {e}")
    
    def save_metrics(self):
        """Save metrics to file."""
        try:
            data = {key: asdict(metric) for key, metric in self.metrics.items()}
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved metrics to {self.log_file}")
        except Exception as e:
            logger.warning(f"Could not save metrics: {e}")
    
    def print_report(self):
        """Print a formatted performance report."""
        summary = self.get_summary()
        
        print("\n📊 Quiz Generation Performance Report")
        print("=" * 50)
        print(f"Total Attempts: {summary['total_attempts']}")
        print(f"Total Successes: {summary['total_successes']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        print("\n🤖 By Model:")
        for model, stats in summary["by_model"].items():
            print(f"  {model}:")
            print(f"    Success Rate: {stats['success_rate']:.1f}% ({stats['successes']}/{stats['attempts']})")
            print(f"    Avg Time: {stats['avg_time']:.2f}s")
        
        print("\n❓ By Question Type:")
        for q_type, stats in summary["by_question_type"].items():
            print(f"  {q_type}:")
            print(f"    Success Rate: {stats['success_rate']:.1f}% ({stats['successes']}/{stats['attempts']})")

# Global instance for easy use
performance_monitor = PerformanceMonitor()

def track_generation(model_name: str, question_type: str):
    """Decorator for tracking quiz generation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = performance_monitor.start_generation(model_name, question_type)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                generation_time = time.time() - start_time
                
                if result is not None:
                    performance_monitor.record_success(key, generation_time)
                else:
                    performance_monitor.record_failure(key, "general")
                
                return result
                
            except Exception as e:
                performance_monitor.record_failure(key, "exception")
                raise
        
        return wrapper
    return decorator
