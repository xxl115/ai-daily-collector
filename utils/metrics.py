# AI Daily Collector - 监控指标
# 支持 Prometheus 格式指标收集

import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from config.settings import config


@dataclass
class Metrics:
    """监控指标数据类"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._start_times: Dict[str, float] = {}
        self._events: List[Dict] = []
    
    # ========== Counter（计数器）==========
    
    def counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """增加计数器"""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        return self._counters[key]
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """获取计数器值"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)
    
    # ========== Gauge（仪表盘）==========
    
    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表盘值"""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        return value
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """获取仪表盘值"""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0)
    
    def gauge_inc(self, name: str, labels: Dict[str, str] = None):
        """仪表盘 +1"""
        return self.gauge(name, self.get_gauge(name, labels) + 1, labels)
    
    def gauge_dec(self, name: str, labels: Dict[str, str] = None):
        """仪表盘 -1"""
        return self.gauge(name, self.get_gauge(name, labels) - 1, labels)
    
    # ========== Histogram（直方图）==========
    
    def histogram_start(self, name: str, labels: Dict[str, str] = None):
        """开始计时"""
        key = self._make_key(name, labels)
        self._start_times[key] = time.time()
        return key
    
    def histogram_end(self, name: str, labels: Dict[str, str] = None) -> float:
        """结束计时，返回耗时（秒）"""
        key = self._make_key(name, labels)
        if key not in self._start_times:
            return 0
        
        duration = time.time() - self._start_times.pop(key)
        
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(duration)
        
        return duration
    
    def histogramObserve(self, name: str, value: float, labels: Dict[str, str] = None):
        """观察直方图值"""
        key = self._make_key(name, labels)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
    
    # ========== Events（事件）==========
    
    def event(self, name: str, message: str, level: str = "info", **kwargs):
        """记录事件"""
        self._events.append({
            "name": name,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    # ========== 导出 ==========
    
    def get_metrics(self) -> str:
        """获取 Prometheus 格式的指标"""
        lines = ["# AI Daily Collector Metrics", f"# Generated at {datetime.now().isoformat()}", ""]
        
        # Counters
        for key, value in self._counters.items():
            name, labels = self._parse_key(key)
            labels_str = self._format_labels(labels)
            lines.append(f"# TYPE {name} counter")
            lines.append(f'{name}{labels_str} {value}')
        
        # Gauges
        for key, value in self._gauges.items():
            name, labels = self._parse_key(key)
            labels_str = self._format_labels(labels)
            lines.append(f"# TYPE {name} gauge")
            lines.append(f'{name}{labels_str} {value}')
        
        # Histograms
        for key, values in self._histograms.items():
            name, labels = self._parse_key(key)
            labels_str = self._format_labels(labels)
            lines.append(f"# TYPE {name} histogram")
            lines.append(f'{name}_count{labels_str} {len(values)}')
            lines.append(f'{name}_sum{labels_str} {sum(values)}')
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "counters": len(self._counters),
            "gauges": len(self._gauges),
            "histograms": len(self._histograms),
            "events": len(self._events),
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds() if hasattr(self, '_start_time') else 0
        }
    
    def reset(self):
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._start_times.clear()
        self._events.clear()
        self._start_time = datetime.now()
    
    # ========== 辅助方法 ==========
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成唯一 key"""
        if labels:
            sorted_labels = sorted(labels.items())
            labels_str = ",".join([f"{k}={v}" for k, v in sorted_labels])
            return f"{name}{{{labels_str}}}"
        return name
    
    def _parse_key(self, key: str) -> tuple:
        """解析 key"""
        if key.startswith("{") and key.endswith("}"):
            name = key.split("{")[0]
            labels_str = key.split("{")[1].rstrip("}")
            labels = {}
            for part in labels_str.split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    labels[k] = v
            return name, labels
        return key, {}
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """格式化 labels 为字符串"""
        if not labels:
            return ""
        sorted_labels = sorted(labels.items())
        return "{" + ",".join([f'{k}="{v}"' for k, v in sorted_labels]) + "}"


# 全局指标收集器
metrics = MetricsCollector()
metrics._start_time = datetime.now()


# 常用指标记录
class CollectorMetrics:
    """采集器相关指标"""
    
    @staticmethod
    def record_articles_collected(source: str, count: int):
        metrics.counter("articles_collected_total", count, {"source": source})
    
    @staticmethod
    def record_summaries_generated(success: bool):
        metrics.counter("summaries_generated_total", 1, {"status": "success" if success else "failed"})
    
    @staticmethod
    def record_report_generated(category: str):
        metrics.counter("reports_generated_total", 1, {"category": category})
    
    @staticmethod
    def record_api_request(endpoint: str, status: str):
        metrics.counter("api_requests_total", 1, {"endpoint": endpoint, "status": status})
    
    @staticmethod
    def record_workflow_duration(duration: float):
        metrics.histogramObserve("workflow_duration_seconds", duration)
    
    @staticmethod
    def set_articles_count(count: int):
        metrics.gauge("articles_count", count)


# 上下文管理器
class track_duration:
    """计时上下文管理器"""
    
    def __init__(self, name: str, labels: Dict[str, str] = None):
        self.name = name
        self.labels = labels
        self.duration = 0
    
    def __enter__(self):
        self.key = metrics.histogram_start(self.name, self.labels)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = metrics.histogram_end(self.name, self.labels)
        return False
    
    @property
    def seconds(self) -> float:
        return self.duration
