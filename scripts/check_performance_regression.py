#!/usr/bin/env python3
"""
Performance regression checker for SQL Genius AI
Compares current benchmark results with baseline to detect regressions
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class RegressionSeverity(Enum):
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major" 
    CRITICAL = "critical"


@dataclass
class BenchmarkResult:
    name: str
    min_duration: float
    max_duration: float
    mean_duration: float
    median_duration: float
    std_dev: float
    iterations: int
    ops_per_second: Optional[float] = None


@dataclass
class RegressionResult:
    test_name: str
    baseline_mean: float
    current_mean: float
    change_percent: float
    severity: RegressionSeverity
    threshold_exceeded: bool


class PerformanceRegressionChecker:
    """Performance regression detection and analysis"""
    
    def __init__(self):
        # Regression thresholds (percentage increase from baseline)
        self.thresholds = {
            RegressionSeverity.MINOR: 10.0,    # 10% slower
            RegressionSeverity.MAJOR: 25.0,    # 25% slower  
            RegressionSeverity.CRITICAL: 50.0  # 50% slower
        }
        
        # Critical performance tests that should never regress significantly
        self.critical_tests = {
            'test_sql_generation_performance',
            'test_api_response_time',
            'test_database_query_performance',
            'test_cache_performance',
            'test_authentication_performance'
        }
        
        # Performance budget (maximum acceptable duration in seconds)
        self.performance_budget = {
            'test_sql_generation_performance': 5.0,
            'test_api_response_time': 1.0,
            'test_database_query_performance': 0.5,
            'test_cache_performance': 0.1,
            'test_authentication_performance': 0.2
        }
    
    def load_benchmark_results(self, file_path: str) -> List[BenchmarkResult]:
        """Load benchmark results from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            results = []
            
            # Handle pytest-benchmark format
            if 'benchmarks' in data:
                for benchmark in data['benchmarks']:
                    stats = benchmark['stats']
                    result = BenchmarkResult(
                        name=benchmark['name'],
                        min_duration=stats['min'],
                        max_duration=stats['max'],
                        mean_duration=stats['mean'],
                        median_duration=stats['median'],
                        std_dev=stats['stddev'],
                        iterations=stats['rounds'],
                        ops_per_second=1.0 / stats['mean'] if stats['mean'] > 0 else None
                    )
                    results.append(result)
            
            # Handle custom format
            elif isinstance(data, list):
                for item in data:
                    result = BenchmarkResult(**item)
                    results.append(result)
            
            return results
            
        except FileNotFoundError:
            logger.error(f"Benchmark file {file_path} not found")
            return []
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing benchmark file {file_path}: {e}")
            return []
    
    def load_baseline(self, baseline_path: str = 'baseline_performance.json') -> Dict[str, BenchmarkResult]:
        """Load baseline performance data"""
        if not os.path.exists(baseline_path):
            logger.warning(f"Baseline file {baseline_path} not found, creating new baseline")
            return {}
        
        baseline_results = self.load_benchmark_results(baseline_path)
        return {result.name: result for result in baseline_results}
    
    def save_baseline(self, results: List[BenchmarkResult], baseline_path: str = 'baseline_performance.json'):
        """Save current results as new baseline"""
        baseline_data = []
        for result in results:
            baseline_data.append({
                'name': result.name,
                'min_duration': result.min_duration,
                'max_duration': result.max_duration,
                'mean_duration': result.mean_duration,
                'median_duration': result.median_duration,
                'std_dev': result.std_dev,
                'iterations': result.iterations,
                'ops_per_second': result.ops_per_second
            })
        
        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        logger.info(f"Saved baseline to {baseline_path}")
    
    def detect_regressions(
        self, 
        current_results: List[BenchmarkResult],
        baseline_results: Dict[str, BenchmarkResult]
    ) -> List[RegressionResult]:
        """Detect performance regressions"""
        regressions = []
        
        for current in current_results:
            if current.name not in baseline_results:
                logger.warning(f"No baseline found for test {current.name}")
                continue
            
            baseline = baseline_results[current.name]
            
            # Calculate percentage change
            change_percent = ((current.mean_duration - baseline.mean_duration) / baseline.mean_duration) * 100
            
            # Determine severity
            severity = RegressionSeverity.NONE
            threshold_exceeded = False
            
            if change_percent > self.thresholds[RegressionSeverity.CRITICAL]:
                severity = RegressionSeverity.CRITICAL
                threshold_exceeded = True
            elif change_percent > self.thresholds[RegressionSeverity.MAJOR]:
                severity = RegressionSeverity.MAJOR
                threshold_exceeded = True
            elif change_percent > self.thresholds[RegressionSeverity.MINOR]:
                severity = RegressionSeverity.MINOR
                threshold_exceeded = True
            
            regression = RegressionResult(
                test_name=current.name,
                baseline_mean=baseline.mean_duration,
                current_mean=current.mean_duration,
                change_percent=change_percent,
                severity=severity,
                threshold_exceeded=threshold_exceeded
            )
            
            regressions.append(regression)
        
        return regressions
    
    def check_performance_budget(self, results: List[BenchmarkResult]) -> List[str]:
        """Check if results exceed performance budget"""
        budget_violations = []
        
        for result in results:
            if result.name in self.performance_budget:
                budget = self.performance_budget[result.name]
                if result.mean_duration > budget:
                    violation = (
                        f"Performance budget exceeded for {result.name}: "
                        f"{result.mean_duration:.3f}s > {budget:.3f}s "
                        f"({((result.mean_duration - budget) / budget * 100):+.1f}%)"
                    )
                    budget_violations.append(violation)
        
        return budget_violations
    
    def generate_report(
        self, 
        current_results: List[BenchmarkResult],
        regressions: List[RegressionResult],
        budget_violations: List[str]
    ) -> None:
        """Generate detailed performance report"""
        print("\n" + "="*80)
        print("PERFORMANCE REGRESSION ANALYSIS REPORT")
        print("="*80)
        
        # Summary statistics
        total_tests = len(current_results)
        total_regressions = len([r for r in regressions if r.threshold_exceeded])
        critical_regressions = len([r for r in regressions if r.severity == RegressionSeverity.CRITICAL])
        major_regressions = len([r for r in regressions if r.severity == RegressionSeverity.MAJOR])
        minor_regressions = len([r for r in regressions if r.severity == RegressionSeverity.MINOR])
        
        print(f"\nSUMMARY:")
        print(f"  Total tests analyzed: {total_tests}")
        print(f"  Performance regressions: {total_regressions}")
        print(f"    - Critical: {critical_regressions}")
        print(f"    - Major: {major_regressions}")
        print(f"    - Minor: {minor_regressions}")
        print(f"  Budget violations: {len(budget_violations)}")
        
        # Current performance results
        print(f"\n" + "-"*80)
        print("CURRENT PERFORMANCE RESULTS:")
        print("-"*80)
        
        for result in sorted(current_results, key=lambda x: x.mean_duration, reverse=True):
            ops_str = f" ({result.ops_per_second:.1f} ops/sec)" if result.ops_per_second else ""
            print(f"  {result.name}:")
            print(f"    Mean: {result.mean_duration:.3f}s ± {result.std_dev:.3f}s{ops_str}")
            print(f"    Range: {result.min_duration:.3f}s - {result.max_duration:.3f}s")
            print(f"    Iterations: {result.iterations}")
        
        # Regression analysis
        if regressions:
            print(f"\n" + "-"*80)
            print("REGRESSION ANALYSIS:")
            print("-"*80)
            
            # Group by severity
            for severity in [RegressionSeverity.CRITICAL, RegressionSeverity.MAJOR, RegressionSeverity.MINOR]:
                severity_regressions = [r for r in regressions if r.severity == severity]
                if not severity_regressions:
                    continue
                
                severity_icon = {
                    RegressionSeverity.CRITICAL: "🔴",
                    RegressionSeverity.MAJOR: "🟠", 
                    RegressionSeverity.MINOR: "🟡"
                }
                
                print(f"\n{severity_icon[severity]} {severity.value.upper()} REGRESSIONS:")
                
                for regression in sorted(severity_regressions, key=lambda x: x.change_percent, reverse=True):
                    print(f"  {regression.test_name}:")
                    print(f"    Baseline: {regression.baseline_mean:.3f}s")
                    print(f"    Current:  {regression.current_mean:.3f}s")
                    print(f"    Change:   {regression.change_percent:+.1f}%")
        
        # Performance improvements
        improvements = [r for r in regressions if r.change_percent < -5.0]  # >5% improvement
        if improvements:
            print(f"\n" + "-"*80)
            print("🟢 PERFORMANCE IMPROVEMENTS:")
            print("-"*80)
            
            for improvement in sorted(improvements, key=lambda x: x.change_percent):
                print(f"  {improvement.test_name}:")
                print(f"    Baseline: {improvement.baseline_mean:.3f}s")
                print(f"    Current:  {improvement.current_mean:.3f}s")
                print(f"    Improvement: {abs(improvement.change_percent):.1f}% faster")
        
        # Budget violations
        if budget_violations:
            print(f"\n" + "-"*80)
            print("💰 PERFORMANCE BUDGET VIOLATIONS:")
            print("-"*80)
            
            for violation in budget_violations:
                print(f"  ❌ {violation}")
        
        # Recommendations
        print(f"\n" + "-"*80)
        print("RECOMMENDATIONS:")
        print("-"*80)
        
        if critical_regressions > 0:
            print("  🔴 CRITICAL: Immediate action required!")
            print("     - Review recent changes that may impact performance")
            print("     - Consider rolling back problematic commits")
            print("     - Profile critical paths to identify bottlenecks")
        
        if major_regressions > 0:
            print("  🟠 MAJOR: Performance degradation detected")
            print("     - Schedule performance optimization work")
            print("     - Review and optimize slow operations")
        
        if minor_regressions > 0:
            print("  🟡 MINOR: Monitor these tests closely")
            print("     - Track trend over multiple builds")
            print("     - Consider optimization if trend continues")
        
        if budget_violations:
            print("  💰 BUDGET: Performance budget exceeded")
            print("     - Optimize slow operations to meet SLA requirements")
            print("     - Consider increasing infrastructure resources")
        
        if total_regressions == 0 and not budget_violations:
            print("  ✅ All performance tests within acceptable limits")
            print("     - Continue monitoring performance trends")
    
    def export_results(
        self, 
        current_results: List[BenchmarkResult],
        regressions: List[RegressionResult],
        budget_violations: List[str],
        output_file: str = 'performance_report.json'
    ) -> None:
        """Export results for CI/CD pipeline"""
        
        # Determine overall status
        critical_count = len([r for r in regressions if r.severity == RegressionSeverity.CRITICAL])
        major_count = len([r for r in regressions if r.severity == RegressionSeverity.MAJOR])
        
        if critical_count > 0 or len(budget_violations) > 0:
            status = "FAIL"
        elif major_count > 0:
            status = "WARNING"
        else:
            status = "PASS"
        
        report = {
            'status': status,
            'summary': {
                'total_tests': len(current_results),
                'total_regressions': len([r for r in regressions if r.threshold_exceeded]),
                'critical_regressions': critical_count,
                'major_regressions': major_count,
                'minor_regressions': len([r for r in regressions if r.severity == RegressionSeverity.MINOR]),
                'budget_violations': len(budget_violations)
            },
            'current_results': [
                {
                    'name': r.name,
                    'mean_duration': r.mean_duration,
                    'std_dev': r.std_dev,
                    'ops_per_second': r.ops_per_second
                }
                for r in current_results
            ],
            'regressions': [
                {
                    'test_name': r.test_name,
                    'baseline_mean': r.baseline_mean,
                    'current_mean': r.current_mean,
                    'change_percent': r.change_percent,
                    'severity': r.severity.value,
                    'threshold_exceeded': r.threshold_exceeded
                }
                for r in regressions
            ],
            'budget_violations': budget_violations,
            'thresholds': {s.value: t for s, t in self.thresholds.items()},
            'performance_budget': self.performance_budget
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Performance report exported to {output_file}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for performance regressions')
    parser.add_argument('benchmark_file', help='Current benchmark results file')
    parser.add_argument('--baseline', default='baseline_performance.json',
                       help='Baseline performance file')
    parser.add_argument('--output', default='performance_report.json',
                       help='Output report file')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update baseline with current results')
    parser.add_argument('--fail-on-regression', action='store_true', default=True,
                       help='Fail on performance regressions')
    parser.add_argument('--fail-on-budget', action='store_true', default=True,
                       help='Fail on budget violations')
    
    args = parser.parse_args()
    
    checker = PerformanceRegressionChecker()
    
    # Load current results
    logger.info(f"Loading benchmark results from {args.benchmark_file}")
    current_results = checker.load_benchmark_results(args.benchmark_file)
    
    if not current_results:
        logger.error("No benchmark results found")
        sys.exit(1)
    
    # Load baseline
    baseline_results = checker.load_baseline(args.baseline)
    
    # Detect regressions
    regressions = checker.detect_regressions(current_results, baseline_results)
    
    # Check budget violations
    budget_violations = checker.check_performance_budget(current_results)
    
    # Generate report
    checker.generate_report(current_results, regressions, budget_violations)
    
    # Export results
    checker.export_results(current_results, regressions, budget_violations, args.output)
    
    # Update baseline if requested
    if args.update_baseline:
        checker.save_baseline(current_results, args.baseline)
    
    # Determine exit code
    exit_code = 0
    
    critical_regressions = len([r for r in regressions if r.severity == RegressionSeverity.CRITICAL])
    major_regressions = len([r for r in regressions if r.severity == RegressionSeverity.MAJOR])
    
    if args.fail_on_regression and (critical_regressions > 0 or major_regressions > 0):
        logger.error(f"Performance regressions detected: {critical_regressions} critical, {major_regressions} major")
        exit_code = 1
    
    if args.fail_on_budget and budget_violations:
        logger.error(f"Performance budget violations: {len(budget_violations)}")
        exit_code = 1
    
    if exit_code == 0:
        logger.info("✅ Performance regression check PASSED")
    else:
        logger.error("❌ Performance regression check FAILED")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()