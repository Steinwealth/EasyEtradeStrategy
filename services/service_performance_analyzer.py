# services/service_performance_analyzer.py

"""
Service Performance Analyzer for ETrade Strategy
Analyzes and optimizes service performance for maximum trading gains
Provides real-time performance monitoring and optimization recommendations
"""

from __future__ import annotations
import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading

from .base_service import BaseService, ServiceHealth
from modules.prime_data_manager import get_prime_data_manager
from modules.prime_trading_system import get_prime_trading_system
from modules.prime_market_manager import get_prime_market_manager
from modules.prime_news_manager import get_prime_news_manager
from modules.prime_trading_manager import get_prime_trading_manager
from modules.production_signal_generator import get_enhanced_production_signal_generator

log = logging.getLogger("service_performance_analyzer")

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: str
    service_name: str
    metric_name: str
    value: float
    unit: str
    category: str  # 'signal', 'execution', 'data', 'system'
    metadata: Dict[str, Any]

@dataclass
class PerformanceAnalysis:
    """Performance analysis results"""
    service_name: str
    analysis_timestamp: str
    overall_score: float
    performance_trend: str  # 'improving', 'stable', 'degrading'
    bottlenecks: List[str]
    optimization_opportunities: List[str]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]
    alerts: List[str]

class ServicePerformanceAnalyzer(BaseService):
    """Analyzes and optimizes service performance for maximum trading gains"""
    
    def __init__(self):
        super().__init__("service_performance_analyzer")
        
        # Performance tracking
        self.metrics_history = []
        self.analysis_history = []
        self.optimization_recommendations = []
        
        # Performance thresholds
        self.thresholds = {
            'signal_accuracy': {'min': 0.80, 'target': 0.90, 'excellent': 0.95},
            'processing_time': {'max': 1.0, 'target': 0.5, 'excellent': 0.1},
            'execution_success_rate': {'min': 0.90, 'target': 0.95, 'excellent': 0.98},
            'cache_hit_rate': {'min': 0.70, 'target': 0.85, 'excellent': 0.95},
            'memory_usage': {'max': 0.80, 'target': 0.60, 'excellent': 0.40},
            'cpu_usage': {'max': 0.80, 'target': 0.60, 'excellent': 0.40}
        }
        
        # Service performance tracking
        self.service_metrics = {}
        
        log.info("Service Performance Analyzer initialized")
    
    def _start_service(self) -> bool:
        """Start the performance analyzer service"""
        try:
            log.info("Starting Service Performance Analyzer...")
            
            # Start performance monitoring thread
            self._start_performance_monitoring()
            
            return True
            
        except Exception as e:
            log.error(f"Error starting performance analyzer: {e}")
            return False
    
    def _stop_service(self) -> bool:
        """Stop the performance analyzer service"""
        try:
            log.info("Stopping Service Performance Analyzer...")
            self.stop_event.set()
            return True
            
        except Exception as e:
            log.error(f"Error stopping performance analyzer: {e}")
            return False
    
    def _check_health(self) -> ServiceHealth:
        """Check performance analyzer health"""
        try:
            if not self.is_running:
                return ServiceHealth(
                    name=self.name,
                    status="stopped",
                    uptime=0,
                    last_check=time.time(),
                    error_count=self.error_count,
                    message="Service is not running",
                    metadata={}
                )
            
            return ServiceHealth(
                name=self.name,
                status="healthy",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count,
                message="Performance analyzer operational",
                metadata={
                    'metrics_collected': len(self.metrics_history),
                    'analyses_performed': len(self.analysis_history),
                    'services_monitored': len(self.service_metrics)
                }
            )
            
        except Exception as e:
            log.error(f"Health check failed: {e}")
            return ServiceHealth(
                name=self.name,
                status="unhealthy",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count + 1,
                message=f"Health check error: {e}",
                metadata={}
            )
    
    def _start_performance_monitoring(self):
        """Start performance monitoring thread"""
        def monitor_performance():
            while not self.stop_event.is_set():
                try:
                    # Collect performance metrics from all services
                    self._collect_service_metrics()
                    
                    # Analyze performance trends
                    self._analyze_performance_trends()
                    
                    # Generate optimization recommendations
                    self._generate_optimization_recommendations()
                    
                    # Wait before next monitoring cycle
                    self.stop_event.wait(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    log.error(f"Performance monitoring error: {e}")
                    self.stop_event.wait(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
        monitor_thread.start()
        log.info("Performance monitoring thread started")
    
    def _collect_service_metrics(self):
        """Collect performance metrics from all services"""
        try:
            # This would collect metrics from all running services
            # For now, we'll simulate metric collection
            
            current_time = datetime.utcnow().isoformat()
            
            # Simulate collecting metrics from different service types
            service_types = [
                'enhanced_ultra_performance_service',
                'optimized_signal_service',
                'position_tracking_service',
                'alert_only_service'
            ]
            
            for service_type in service_types:
                if service_type in self.service_metrics:
                    # Collect real metrics from service
                    metrics = self._collect_metrics_from_service(service_type)
                    self._store_metrics(service_type, metrics, current_time)
                else:
                    # Simulate metrics for demonstration
                    simulated_metrics = self._simulate_service_metrics(service_type)
                    self._store_metrics(service_type, simulated_metrics, current_time)
            
        except Exception as e:
            log.error(f"Error collecting service metrics: {e}")
    
    def _collect_metrics_from_service(self, service_name: str) -> List[PerformanceMetric]:
        """Collect metrics from a specific service"""
        try:
            # This would use the service's health check and performance methods
            # For now, return empty list
            return []
            
        except Exception as e:
            log.error(f"Error collecting metrics from {service_name}: {e}")
            return []
    
    def _simulate_service_metrics(self, service_name: str) -> List[PerformanceMetric]:
        """Simulate metrics for demonstration purposes"""
        current_time = datetime.utcnow().isoformat()
        
        # Simulate different performance profiles for different services
        if 'ultra' in service_name:
            # High-performance service
            return [
                PerformanceMetric(current_time, service_name, 'signal_accuracy', 0.92, '%', 'signal', {}),
                PerformanceMetric(current_time, service_name, 'processing_time', 0.05, 's', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'execution_success_rate', 0.96, '%', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'cache_hit_rate', 0.88, '%', 'data', {}),
                PerformanceMetric(current_time, service_name, 'memory_usage', 0.65, '%', 'system', {}),
                PerformanceMetric(current_time, service_name, 'cpu_usage', 0.55, '%', 'system', {}),
                PerformanceMetric(current_time, service_name, 'ml_predictions_per_second', 150, 'predictions/s', 'signal', {}),
                PerformanceMetric(current_time, service_name, 'multi_timeframe_confirmations', 0.78, '%', 'signal', {})
            ]
        elif 'optimized' in service_name:
            # Optimized service
            return [
                PerformanceMetric(current_time, service_name, 'signal_accuracy', 0.85, '%', 'signal', {}),
                PerformanceMetric(current_time, service_name, 'processing_time', 0.15, 's', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'execution_success_rate', 0.93, '%', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'cache_hit_rate', 0.82, '%', 'data', {}),
                PerformanceMetric(current_time, service_name, 'memory_usage', 0.45, '%', 'system', {}),
                PerformanceMetric(current_time, service_name, 'cpu_usage', 0.35, '%', 'system', {})
            ]
        elif 'alert' in service_name:
            # Alert-only service
            return [
                PerformanceMetric(current_time, service_name, 'signal_accuracy', 0.80, '%', 'signal', {}),
                PerformanceMetric(current_time, service_name, 'processing_time', 0.8, 's', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'execution_success_rate', 1.0, '%', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'cache_hit_rate', 0.75, '%', 'data', {}),
                PerformanceMetric(current_time, service_name, 'memory_usage', 0.25, '%', 'system', {}),
                PerformanceMetric(current_time, service_name, 'cpu_usage', 0.15, '%', 'system', {})
            ]
        else:
            # Standard service
            return [
                PerformanceMetric(current_time, service_name, 'signal_accuracy', 0.78, '%', 'signal', {}),
                PerformanceMetric(current_time, service_name, 'processing_time', 0.5, 's', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'execution_success_rate', 0.90, '%', 'execution', {}),
                PerformanceMetric(current_time, service_name, 'cache_hit_rate', 0.70, '%', 'data', {}),
                PerformanceMetric(current_time, service_name, 'memory_usage', 0.40, '%', 'system', {}),
                PerformanceMetric(current_time, service_name, 'cpu_usage', 0.30, '%', 'system', {})
            ]
    
    def _store_metrics(self, service_name: str, metrics: List[PerformanceMetric], timestamp: str):
        """Store collected metrics"""
        try:
            # Add to metrics history
            self.metrics_history.extend(metrics)
            
            # Keep only last 1000 metrics per service
            service_metrics = [m for m in self.metrics_history if m.service_name == service_name]
            if len(service_metrics) > 1000:
                # Remove oldest metrics
                oldest_metrics = sorted(service_metrics, key=lambda x: x.timestamp)[:-1000]
                for metric in oldest_metrics:
                    self.metrics_history.remove(metric)
            
            # Update service metrics summary
            self.service_metrics[service_name] = {
                'last_updated': timestamp,
                'metrics_count': len(service_metrics),
                'latest_metrics': {m.metric_name: m.value for m in metrics}
            }
            
        except Exception as e:
            log.error(f"Error storing metrics: {e}")
    
    def _analyze_performance_trends(self):
        """Analyze performance trends across all services"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            for service_name in self.service_metrics.keys():
                # Get recent metrics for this service
                recent_metrics = self._get_recent_metrics(service_name, hours=1)
                
                if len(recent_metrics) < 5:  # Need enough data for trend analysis
                    continue
                
                # Analyze trends
                analysis = self._perform_service_analysis(service_name, recent_metrics)
                analysis.analysis_timestamp = current_time
                
                # Store analysis
                self.analysis_history.append(analysis)
                
                # Keep only last 100 analyses per service
                service_analyses = [a for a in self.analysis_history if a.service_name == service_name]
                if len(service_analyses) > 100:
                    oldest_analyses = sorted(service_analyses, key=lambda x: x.analysis_timestamp)[:-100]
                    for analysis in oldest_analyses:
                        self.analysis_history.remove(analysis)
                
        except Exception as e:
            log.error(f"Error analyzing performance trends: {e}")
    
    def _get_recent_metrics(self, service_name: str, hours: int = 1) -> List[PerformanceMetric]:
        """Get recent metrics for a service"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        return [
            m for m in self.metrics_history 
            if m.service_name == service_name and m.timestamp >= cutoff_str
        ]
    
    def _perform_service_analysis(self, service_name: str, metrics: List[PerformanceMetric]) -> PerformanceAnalysis:
        """Perform detailed analysis for a service"""
        try:
            # Group metrics by name
            metric_groups = {}
            for metric in metrics:
                if metric.metric_name not in metric_groups:
                    metric_groups[metric.metric_name] = []
                metric_groups[metric.metric_name].append(metric.value)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(metric_groups)
            
            # Determine performance trend
            performance_trend = self._determine_performance_trend(metric_groups)
            
            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(metric_groups)
            
            # Find optimization opportunities
            optimization_opportunities = self._find_optimization_opportunities(metric_groups)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metric_groups, bottlenecks, optimization_opportunities)
            
            # Create metrics summary
            metrics_summary = self._create_metrics_summary(metric_groups)
            
            # Generate alerts
            alerts = self._generate_alerts(metric_groups)
            
            return PerformanceAnalysis(
                service_name=service_name,
                analysis_timestamp="",  # Will be set by caller
                overall_score=overall_score,
                performance_trend=performance_trend,
                bottlenecks=bottlenecks,
                optimization_opportunities=optimization_opportunities,
                recommendations=recommendations,
                metrics_summary=metrics_summary,
                alerts=alerts
            )
            
        except Exception as e:
            log.error(f"Error performing service analysis: {e}")
            return PerformanceAnalysis(
                service_name=service_name,
                analysis_timestamp=datetime.utcnow().isoformat(),
                overall_score=0.0,
                performance_trend="unknown",
                bottlenecks=[],
                optimization_opportunities=[],
                recommendations=[],
                metrics_summary={},
                alerts=[f"Analysis error: {e}"]
            )
    
    def _calculate_overall_score(self, metric_groups: Dict[str, List[float]]) -> float:
        """Calculate overall performance score"""
        try:
            scores = []
            
            for metric_name, values in metric_groups.items():
                if not values:
                    continue
                
                latest_value = values[-1]
                threshold = self.thresholds.get(metric_name)
                
                if threshold:
                    if metric_name in ['signal_accuracy', 'execution_success_rate', 'cache_hit_rate']:
                        # Higher is better
                        if latest_value >= threshold['excellent']:
                            scores.append(1.0)
                        elif latest_value >= threshold['target']:
                            scores.append(0.8)
                        elif latest_value >= threshold['min']:
                            scores.append(0.6)
                        else:
                            scores.append(0.3)
                    else:
                        # Lower is better
                        if latest_value <= threshold['excellent']:
                            scores.append(1.0)
                        elif latest_value <= threshold['target']:
                            scores.append(0.8)
                        elif latest_value <= threshold['max']:
                            scores.append(0.6)
                        else:
                            scores.append(0.3)
            
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception as e:
            log.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _determine_performance_trend(self, metric_groups: Dict[str, List[float]]) -> str:
        """Determine overall performance trend"""
        try:
            trends = []
            
            for metric_name, values in metric_groups.items():
                if len(values) < 3:
                    continue
                
                # Simple trend calculation (latest vs earlier)
                recent_avg = sum(values[-3:]) / 3
                earlier_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else recent_avg
                
                threshold = self.thresholds.get(metric_name)
                if threshold:
                    if metric_name in ['signal_accuracy', 'execution_success_rate', 'cache_hit_rate']:
                        # Higher is better
                        if recent_avg > earlier_avg * 1.05:
                            trends.append('improving')
                        elif recent_avg < earlier_avg * 0.95:
                            trends.append('degrading')
                        else:
                            trends.append('stable')
                    else:
                        # Lower is better
                        if recent_avg < earlier_avg * 0.95:
                            trends.append('improving')
                        elif recent_avg > earlier_avg * 1.05:
                            trends.append('degrading')
                        else:
                            trends.append('stable')
            
            if not trends:
                return 'unknown'
            
            # Determine overall trend
            improving_count = trends.count('improving')
            degrading_count = trends.count('degrading')
            
            if improving_count > degrading_count:
                return 'improving'
            elif degrading_count > improving_count:
                return 'degrading'
            else:
                return 'stable'
                
        except Exception as e:
            log.error(f"Error determining performance trend: {e}")
            return 'unknown'
    
    def _identify_bottlenecks(self, metric_groups: Dict[str, List[float]]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        for metric_name, values in metric_groups.items():
            if not values:
                continue
            
            latest_value = values[-1]
            threshold = self.thresholds.get(metric_name)
            
            if threshold:
                if metric_name in ['signal_accuracy', 'execution_success_rate', 'cache_hit_rate']:
                    # Higher is better
                    if latest_value < threshold['min']:
                        bottlenecks.append(f"{metric_name} below minimum threshold ({latest_value:.2f} < {threshold['min']:.2f})")
                else:
                    # Lower is better
                    if latest_value > threshold['max']:
                        bottlenecks.append(f"{metric_name} above maximum threshold ({latest_value:.2f} > {threshold['max']:.2f})")
        
        return bottlenecks
    
    def _find_optimization_opportunities(self, metric_groups: Dict[str, List[float]]) -> List[str]:
        """Find optimization opportunities"""
        opportunities = []
        
        for metric_name, values in metric_groups.items():
            if not values:
                continue
            
            latest_value = values[-1]
            threshold = self.thresholds.get(metric_name)
            
            if threshold:
                if metric_name in ['signal_accuracy', 'execution_success_rate', 'cache_hit_rate']:
                    # Higher is better
                    if latest_value < threshold['target']:
                        opportunities.append(f"Improve {metric_name} from {latest_value:.2f} to {threshold['target']:.2f}")
                else:
                    # Lower is better
                    if latest_value > threshold['target']:
                        opportunities.append(f"Reduce {metric_name} from {latest_value:.2f} to {threshold['target']:.2f}")
        
        return opportunities
    
    def _generate_recommendations(self, 
                                metric_groups: Dict[str, List[float]],
                                bottlenecks: List[str],
                                optimization_opportunities: List[str]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Bottleneck-based recommendations
        for bottleneck in bottlenecks:
            if 'processing_time' in bottleneck:
                recommendations.append("Consider implementing async processing or parallel execution")
            elif 'memory_usage' in bottleneck:
                recommendations.append("Optimize memory usage with better caching strategies")
            elif 'cpu_usage' in bottleneck:
                recommendations.append("Optimize CPU usage with more efficient algorithms")
            elif 'signal_accuracy' in bottleneck:
                recommendations.append("Enhance signal generation with ML confidence scoring")
            elif 'cache_hit_rate' in bottleneck:
                recommendations.append("Improve caching strategy and increase cache size")
        
        # Opportunity-based recommendations
        for opportunity in optimization_opportunities:
            if 'signal_accuracy' in opportunity:
                recommendations.append("Enable multi-timeframe analysis and volume pattern recognition")
            elif 'processing_time' in opportunity:
                recommendations.append("Upgrade to ultra-high performance service")
            elif 'execution_success_rate' in opportunity:
                recommendations.append("Implement enhanced error handling and retry logic")
        
        # General recommendations
        if not bottlenecks and not optimization_opportunities:
            recommendations.append("Performance is optimal - consider monitoring for any degradation")
        
        return recommendations
    
    def _create_metrics_summary(self, metric_groups: Dict[str, List[float]]) -> Dict[str, Any]:
        """Create metrics summary"""
        summary = {}
        
        for metric_name, values in metric_groups.items():
            if values:
                summary[metric_name] = {
                    'latest': values[-1],
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return summary
    
    def _generate_alerts(self, metric_groups: Dict[str, List[float]]) -> List[str]:
        """Generate performance alerts"""
        alerts = []
        
        for metric_name, values in metric_groups.items():
            if not values:
                continue
            
            latest_value = values[-1]
            threshold = self.thresholds.get(metric_name)
            
            if threshold:
                if metric_name in ['signal_accuracy', 'execution_success_rate', 'cache_hit_rate']:
                    # Higher is better
                    if latest_value < threshold['min']:
                        alerts.append(f"CRITICAL: {metric_name} below minimum threshold")
                    elif latest_value < threshold['target']:
                        alerts.append(f"WARNING: {metric_name} below target")
                else:
                    # Lower is better
                    if latest_value > threshold['max']:
                        alerts.append(f"CRITICAL: {metric_name} above maximum threshold")
                    elif latest_value > threshold['target']:
                        alerts.append(f"WARNING: {metric_name} above target")
        
        return alerts
    
    def _generate_optimization_recommendations(self):
        """Generate high-level optimization recommendations"""
        try:
            # Analyze all services and generate recommendations
            current_time = datetime.utcnow().isoformat()
            
            # Get latest analysis for each service
            latest_analyses = {}
            for analysis in self.analysis_history:
                if analysis.service_name not in latest_analyses or analysis.analysis_timestamp > latest_analyses[analysis.service_name].analysis_timestamp:
                    latest_analyses[analysis.service_name] = analysis
            
            # Generate recommendations based on analysis
            recommendations = []
            
            for service_name, analysis in latest_analyses.items():
                if analysis.overall_score < 0.7:
                    recommendations.append({
                        'service': service_name,
                        'priority': 'high',
                        'recommendation': f"Service {service_name} has low performance score ({analysis.overall_score:.2f})",
                        'action': 'Consider upgrading to enhanced ultra performance service',
                        'timestamp': current_time
                    })
                
                if analysis.performance_trend == 'degrading':
                    recommendations.append({
                        'service': service_name,
                        'priority': 'medium',
                        'recommendation': f"Service {service_name} performance is degrading",
                        'action': 'Monitor closely and implement optimizations',
                        'timestamp': current_time
                    })
            
            self.optimization_recommendations.extend(recommendations)
            
            # Keep only last 100 recommendations
            if len(self.optimization_recommendations) > 100:
                self.optimization_recommendations = self.optimization_recommendations[-100:]
                
        except Exception as e:
            log.error(f"Error generating optimization recommendations: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            # Get latest analysis for each service
            latest_analyses = {}
            for analysis in self.analysis_history:
                if analysis.service_name not in latest_analyses or analysis.analysis_timestamp > latest_analyses[analysis.service_name].analysis_timestamp:
                    latest_analyses[analysis.service_name] = analysis
            
            return {
                'analyzer_uptime': time.time() - self.start_time if self.start_time else 0,
                'services_monitored': len(self.service_metrics),
                'metrics_collected': len(self.metrics_history),
                'analyses_performed': len(self.analysis_history),
                'service_performance': {
                    service_name: {
                        'overall_score': analysis.overall_score,
                        'performance_trend': analysis.performance_trend,
                        'bottlenecks_count': len(analysis.bottlenecks),
                        'recommendations_count': len(analysis.recommendations),
                        'alerts_count': len(analysis.alerts)
                    }
                    for service_name, analysis in latest_analyses.items()
                },
                'recent_recommendations': self.optimization_recommendations[-10:],
                'performance_thresholds': self.thresholds
            }
            
        except Exception as e:
            log.error(f"Error getting performance summary: {e}")
            return {}
    
    def export_performance_report(self, file_path: str = None) -> str:
        """Export comprehensive performance report"""
        try:
            if not file_path:
                file_path = f"data/performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = {
                'report_timestamp': datetime.utcnow().isoformat(),
                'analyzer_summary': self.get_performance_summary(),
                'service_metrics': self.service_metrics,
                'latest_analyses': [
                    asdict(analysis) for analysis in self.analysis_history[-50:]  # Last 50 analyses
                ],
                'optimization_recommendations': self.optimization_recommendations,
                'performance_thresholds': self.thresholds
            }
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            log.info(f"Performance report exported to {file_path}")
            return file_path
            
        except Exception as e:
            log.error(f"Error exporting performance report: {e}")
            return ""

# Service entry points
def start():
    """Start the service performance analyzer"""
    analyzer = ServicePerformanceAnalyzer()
    analyzer.start()

def main():
    """Main entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()

    def analyze_prime_system_performance(self) -> PerformanceAnalysis:
        """Analyze Prime system performance"""
        try:
            # Get Prime system components
            data_manager = get_prime_data_manager()
            trading_system = get_prime_trading_system()
            market_manager = get_prime_market_manager()
            news_manager = get_prime_news_manager()
            trading_manager = get_prime_trading_manager()
            signal_generator = get_enhanced_production_signal_generator()
            
            # Analyze each component
            component_scores = {}
            
            # Data Manager Performance
            if hasattr(data_manager, 'get_performance_metrics'):
                component_scores['data_manager'] = data_manager.get_performance_metrics()
            
            # Trading System Performance
            if hasattr(trading_system, 'get_performance_metrics'):
                component_scores['trading_system'] = trading_system.get_performance_metrics()
            
            # Market Manager Performance
            if hasattr(market_manager, 'get_performance_metrics'):
                component_scores['market_manager'] = market_manager.get_performance_metrics()
            
            # News Manager Performance
            if hasattr(news_manager, 'get_performance_metrics'):
                component_scores['news_manager'] = news_manager.get_performance_metrics()
            
            # Trading Manager Performance
            if hasattr(trading_manager, 'get_performance_metrics'):
                component_scores['trading_manager'] = trading_manager.get_performance_metrics()
            
            # Signal Generator Performance
            if hasattr(signal_generator, 'get_performance_metrics'):
                component_scores['signal_generator'] = signal_generator.get_performance_metrics()
            
            # Calculate overall Prime system score
            overall_score = self._calculate_prime_system_score(component_scores)
            
            # Generate recommendations
            recommendations = self._generate_prime_optimization_recommendations(component_scores)
            
            return PerformanceAnalysis(
                service_name="prime_system",
                analysis_timestamp=datetime.now().isoformat(),
                overall_score=overall_score,
                performance_trend="stable",
                bottlenecks=[],
                optimization_opportunities=recommendations,
                recommendations=recommendations,
                metrics_summary=component_scores,
                alerts=[]
            )
            
        except Exception as e:
            log.error(f"Prime system performance analysis failed: {e}")
            return PerformanceAnalysis(
                service_name="prime_system",
                analysis_timestamp=datetime.now().isoformat(),
                overall_score=0.0,
                performance_trend="unknown",
                bottlenecks=[f"Analysis error: {e}"],
                optimization_opportunities=[],
                recommendations=[],
                metrics_summary={},
                alerts=[f"Prime system analysis failed: {e}"]
            )
    
    def _calculate_prime_system_score(self, component_scores: Dict[str, Any]) -> float:
        """Calculate overall Prime system performance score"""
        try:
            if not component_scores:
                return 0.0
            
            total_score = 0.0
            component_count = 0
            
            for component, metrics in component_scores.items():
                if isinstance(metrics, dict) and 'score' in metrics:
                    total_score += metrics['score']
                    component_count += 1
            
            return total_score / component_count if component_count > 0 else 0.0
            
        except Exception as e:
            log.error(f"Error calculating Prime system score: {e}")
            return 0.0
    
    def _generate_prime_optimization_recommendations(self, component_scores: Dict[str, Any]) -> List[str]:
        """Generate Prime system optimization recommendations"""
        recommendations = []
        
        try:
            # Check data manager performance
            if 'data_manager' in component_scores:
                data_metrics = component_scores['data_manager']
                if isinstance(data_metrics, dict):
                    if data_metrics.get('cache_hit_rate', 0) < 0.85:
                        recommendations.append("Optimize data manager cache for better hit rate")
                    if data_metrics.get('response_time', 0) > 0.5:
                        recommendations.append("Improve data manager response time")
            
            # Check trading system performance
            if 'trading_system' in component_scores:
                trading_metrics = component_scores['trading_system']
                if isinstance(trading_metrics, dict):
                    if trading_metrics.get('execution_success_rate', 0) < 0.95:
                        recommendations.append("Improve trading system execution success rate")
                    if trading_metrics.get('latency', 0) > 0.1:
                        recommendations.append("Reduce trading system latency")
            
            # Check signal generator performance
            if 'signal_generator' in component_scores:
                signal_metrics = component_scores['signal_generator']
                if isinstance(signal_metrics, dict):
                    if signal_metrics.get('accuracy', 0) < 0.90:
                        recommendations.append("Improve signal generator accuracy")
                    if signal_metrics.get('throughput', 0) < 200:
                        recommendations.append("Increase signal generator throughput")
            
            return recommendations
            
        except Exception as e:
            log.error(f"Error generating Prime optimization recommendations: {e}")
            return [f"Error generating recommendations: {e}"]
