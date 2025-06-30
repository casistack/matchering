#!/usr/bin/env python3
"""
Comprehensive Test Runner for Hybrid AI Mastering System.

This script runs the complete test suite including unit tests, integration tests,
performance benchmarks, and A/B testing validation.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import json


class TestRunner:
    """Comprehensive test runner for the hybrid AI mastering system."""
    
    def __init__(self):
        self.backend_path = Path(__file__).parent / "backend"
        self.test_results = {}
        self.start_time = time.time()
    
    def run_test_suite(self, test_categories: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive test suite.
        
        Args:
            test_categories: List of test categories to run. If None, runs all.
                           Options: ['unit', 'integration', 'performance', 'ab_testing']
        """
        if test_categories is None:
            test_categories = ['unit', 'integration', 'performance', 'ab_testing']
        
        print("🚀 Starting Comprehensive Test Suite for Hybrid AI Mastering System")
        print("=" * 80)
        
        total_results = {
            "start_time": self.start_time,
            "test_categories": test_categories,
            "results": {},
            "summary": {}
        }
        
        # Run each test category
        for category in test_categories:
            print(f"\n📋 Running {category.upper()} Tests...")
            print("-" * 60)
            
            try:
                if category == 'unit':
                    result = self.run_unit_tests()
                elif category == 'integration':
                    result = self.run_integration_tests()
                elif category == 'performance':
                    result = self.run_performance_tests()
                elif category == 'ab_testing':
                    result = self.run_ab_testing()
                else:
                    print(f"⚠️ Unknown test category: {category}")
                    continue
                
                total_results["results"][category] = result
                
                if result["success"]:
                    print(f"✅ {category.upper()} tests completed successfully")
                else:
                    print(f"❌ {category.upper()} tests failed")
                    
            except Exception as e:
                print(f"❌ Error running {category} tests: {e}")
                total_results["results"][category] = {
                    "success": False,
                    "error": str(e),
                    "execution_time": 0.0
                }
        
        # Generate summary
        total_results["summary"] = self.generate_summary(total_results["results"])
        total_results["end_time"] = time.time()
        total_results["total_duration"] = total_results["end_time"] - total_results["start_time"]
        
        # Print final summary
        self.print_final_summary(total_results)
        
        return total_results
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests for hybrid processing engine."""
        start_time = time.time()
        
        try:
            # Run unit tests
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.backend_path / "tests" / "test_hybrid_processing_engine.py"),
                "-v", "--tb=short", "--json-report", "--json-report-file=unit_test_results.json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_path)
            
            # Parse results
            test_result = {
                "success": result.returncode == 0,
                "execution_time": time.time() - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
            # Try to load JSON report if available
            json_report_path = self.backend_path / "unit_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path) as f:
                        json_report = json.load(f)
                        test_result["detailed_results"] = json_report
                except Exception as e:
                    test_result["json_parse_error"] = str(e)
            
            return test_result
            
        except Exception as e:
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run end-to-end integration tests."""
        start_time = time.time()
        
        try:
            # Run integration tests
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.backend_path / "tests" / "test_integration_e2e.py"),
                "-v", "--tb=short", "-m", "integration"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_path)
            
            return {
                "success": result.returncode == 0,
                "execution_time": time.time() - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        start_time = time.time()
        
        try:
            # Run performance tests
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.backend_path / "tests" / "test_performance_benchmarks.py"),
                "-v", "--tb=short", "-m", "performance"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_path)
            
            return {
                "success": result.returncode == 0,
                "execution_time": time.time() - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    def run_ab_testing(self) -> Dict[str, Any]:
        """Run A/B testing framework validation."""
        start_time = time.time()
        
        try:
            # Run A/B testing tests
            cmd = [
                sys.executable, "-m", "pytest",
                str(self.backend_path / "tests" / "test_ab_testing_framework.py"),
                "-v", "--tb=short"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_path)
            
            return {
                "success": result.returncode == 0,
                "execution_time": time.time() - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }
    
    def generate_summary(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate test summary statistics."""
        summary = {
            "total_categories": len(results),
            "successful_categories": 0,
            "failed_categories": 0,
            "total_execution_time": 0.0,
            "category_details": {}
        }
        
        for category, result in results.items():
            summary["total_execution_time"] += result.get("execution_time", 0.0)
            
            if result.get("success", False):
                summary["successful_categories"] += 1
                status = "PASSED"
            else:
                summary["failed_categories"] += 1
                status = "FAILED"
            
            summary["category_details"][category] = {
                "status": status,
                "execution_time": result.get("execution_time", 0.0),
                "error": result.get("error")
            }
        
        summary["success_rate"] = (
            summary["successful_categories"] / summary["total_categories"] * 100
            if summary["total_categories"] > 0 else 0
        )
        
        return summary
    
    def print_final_summary(self, results: Dict[str, Any]):
        """Print comprehensive final summary."""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST SUITE RESULTS")
        print("=" * 80)
        
        summary = results["summary"]
        
        print(f"📊 OVERVIEW:")
        print(f"   Total Duration: {results['total_duration']:.2f}s")
        print(f"   Categories Tested: {summary['total_categories']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Successful: {summary['successful_categories']}")
        print(f"   Failed: {summary['failed_categories']}")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, details in summary["category_details"].items():
            status_icon = "✅" if details["status"] == "PASSED" else "❌"
            print(f"   {status_icon} {category.upper()}: {details['status']} ({details['execution_time']:.2f}s)")
            if details.get("error"):
                print(f"      Error: {details['error']}")
        
        # Overall result
        if summary["failed_categories"] == 0:
            print(f"\n🎉 ALL TESTS PASSED! The Hybrid AI Mastering System is ready for deployment.")
        else:
            print(f"\n⚠️ Some tests failed. Please review the results above.")
        
        print(f"\n💾 Detailed results saved to test results")
    
    def save_results(self, results: Dict[str, Any], output_path: str = "test_results.json"):
        """Save test results to file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📁 Test results saved to {output_path}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {e}")


def main():
    """Main test runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner for Hybrid AI Mastering System")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["unit", "integration", "performance", "ab_testing"],
        help="Test categories to run (default: all)"
    )
    parser.add_argument(
        "--save-results",
        default="test_results.json",
        help="File to save results (default: test_results.json)"
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner()
    results = runner.run_test_suite(test_categories=args.categories)
    
    # Save results
    if args.save_results:
        runner.save_results(results, args.save_results)
    
    # Exit with appropriate code
    if results["summary"]["failed_categories"] == 0:
        print("\n🚀 All tests passed! System ready for deployment.")
        sys.exit(0)
    else:
        print(f"\n❌ {results['summary']['failed_categories']} test categories failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()