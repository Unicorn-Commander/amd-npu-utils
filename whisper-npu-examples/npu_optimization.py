#!/usr/bin/env python3
"""
NPU Optimization Module
Advanced NPU utilization optimization for concurrent VAD, Wake Word, and Whisper processing
"""

import numpy as np
import time
import logging
import os
import sys
import threading
import queue
import multiprocessing
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
import onnxruntime as ort

# Add our modules to path
sys.path.insert(0, '/home/ucadmin/Development/whisper_npu_project')
from whisperx_npu_accelerator import NPUAccelerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NPUResourceManager:
    """Advanced NPU resource management for optimal utilization"""
    
    def __init__(self):
        """Initialize NPU resource manager"""
        self.npu_accelerator = NPUAccelerator()
        self.active_sessions = {}
        self.resource_lock = threading.Lock()
        self.utilization_metrics = {
            "total_operations": 0,
            "concurrent_operations": 0,
            "average_latency": 0.0,
            "peak_utilization": 0.0,
            "power_efficiency": 0.0
        }
        
        # NPU scheduling
        self.operation_queue = queue.PriorityQueue()
        self.worker_thread = None
        self.is_running = False
        
        # Resource allocation
        self.max_concurrent_sessions = 3  # VAD + Wake Word + Whisper
        self.session_priorities = {
            "vad": 1,        # Highest priority - always on
            "wake_word": 2,  # High priority - activation
            "whisper": 3     # Normal priority - processing
        }
        
    def initialize(self):
        """Initialize NPU resource management"""
        try:
            logger.info("🧠 Initializing NPU Resource Manager...")
            
            if not self.npu_accelerator.is_available():
                logger.warning("⚠️ NPU not available, optimization will use CPU fallbacks")
                return False
            
            # Start resource management worker
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._resource_worker, daemon=True)
            self.worker_thread.start()
            
            logger.info("✅ NPU Resource Manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ NPU Resource Manager initialization failed: {e}")
            return False
    
    def create_optimized_session(self, model_path: str, session_type: str, providers: List[str] = None) -> ort.InferenceSession:
        """Create optimized ONNX session with NPU resource management"""
        try:
            with self.resource_lock:
                # Check if we can create another session
                if len(self.active_sessions) >= self.max_concurrent_sessions:
                    logger.warning(f"⚠️ Maximum concurrent sessions reached, optimizing...")
                    self._optimize_session_allocation()
                
                # Set optimal providers for NPU
                if providers is None:
                    providers = ['VitisAIExecutionProvider', 'CPUExecutionProvider']
                
                # Create session with optimization
                session_options = ort.SessionOptions()
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
                session_options.enable_cpu_mem_arena = False  # Better for NPU
                session_options.enable_mem_pattern = True
                
                # NPU-specific optimizations
                if 'VitisAIExecutionProvider' in providers:
                    session_options.add_session_config_entry('vitis_ai.enable_fallback', '1')
                    session_options.add_session_config_entry('vitis_ai.cache_dir', '/tmp/npu_cache')
                
                session = ort.InferenceSession(
                    model_path, 
                    providers=providers,
                    sess_options=session_options
                )
                
                # Register session
                session_id = f"{session_type}_{len(self.active_sessions)}"
                self.active_sessions[session_id] = {
                    "session": session,
                    "type": session_type,
                    "priority": self.session_priorities.get(session_type, 5),
                    "created_time": time.time(),
                    "usage_count": 0,
                    "total_latency": 0.0
                }
                
                logger.info(f"✅ Created optimized {session_type} session: {session_id}")
                logger.info(f"📊 Active sessions: {len(self.active_sessions)}/{self.max_concurrent_sessions}")
                
                return session
                
        except Exception as e:
            logger.error(f"❌ Failed to create optimized session: {e}")
            raise
    
    def schedule_operation(self, operation_func: Callable, session_type: str, priority: int = 5, *args, **kwargs) -> Any:
        """Schedule NPU operation with priority and resource management"""
        try:
            # Create operation item
            operation_id = f"{session_type}_{time.time()}"
            operation_item = (priority, time.time(), operation_id, operation_func, args, kwargs)
            
            # Add to queue
            self.operation_queue.put(operation_item)
            
            # Wait for result (simplified - in production, use futures/callbacks)
            # For now, execute immediately for real-time requirements
            return self._execute_operation(operation_func, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Operation scheduling failed: {e}")
            raise
    
    def _execute_operation(self, operation_func: Callable, *args, **kwargs) -> Any:
        """Execute NPU operation with monitoring"""
        start_time = time.time()
        
        try:
            # Update metrics
            self.utilization_metrics["total_operations"] += 1
            self.utilization_metrics["concurrent_operations"] += 1
            
            # Execute operation
            result = operation_func(*args, **kwargs)
            
            # Calculate metrics
            latency = time.time() - start_time
            self.utilization_metrics["total_latency"] += latency
            self.utilization_metrics["average_latency"] = (
                self.utilization_metrics["total_latency"] / 
                self.utilization_metrics["total_operations"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Operation execution failed: {e}")
            raise
            
        finally:
            self.utilization_metrics["concurrent_operations"] -= 1
    
    def _resource_worker(self):
        """Background worker for NPU resource management"""
        logger.info("🔄 NPU resource worker started")
        
        while self.is_running:
            try:
                # Monitor and optimize resource usage
                self._monitor_utilization()
                self._optimize_memory_usage()
                time.sleep(0.1)  # 100ms monitoring interval
                
            except Exception as e:
                logger.error(f"❌ Resource worker error: {e}")
        
        logger.info("🔄 NPU resource worker stopped")
    
    def _monitor_utilization(self):
        """Monitor NPU utilization and performance"""
        try:
            current_utilization = (
                self.utilization_metrics["concurrent_operations"] / 
                max(self.max_concurrent_sessions, 1)
            )
            
            if current_utilization > self.utilization_metrics["peak_utilization"]:
                self.utilization_metrics["peak_utilization"] = current_utilization
            
            # Calculate power efficiency (operations per watt approximation)
            if self.utilization_metrics["total_operations"] > 0:
                estimated_power = 1.0 + (current_utilization * 4.0)  # 1-5W estimate
                self.utilization_metrics["power_efficiency"] = (
                    self.utilization_metrics["total_operations"] / estimated_power
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Utilization monitoring error: {e}")
    
    def _optimize_session_allocation(self):
        """Optimize NPU session allocation"""
        try:
            # Find least used session with lowest priority
            least_used = None
            min_priority = float('inf')
            min_usage = float('inf')
            
            for session_id, session_info in self.active_sessions.items():
                if (session_info["priority"] >= min_priority and 
                    session_info["usage_count"] < min_usage):
                    min_priority = session_info["priority"]
                    min_usage = session_info["usage_count"]
                    least_used = session_id
            
            # Remove least used session if needed
            if least_used and len(self.active_sessions) >= self.max_concurrent_sessions:
                removed_session = self.active_sessions.pop(least_used)
                logger.info(f"🗑️ Removed session {least_used} for optimization")
                
        except Exception as e:
            logger.warning(f"⚠️ Session optimization error: {e}")
    
    def _optimize_memory_usage(self):
        """Optimize NPU memory usage"""
        try:
            # Simple memory optimization - in production, implement more sophisticated logic
            if len(self.active_sessions) > 0:
                # Trigger garbage collection periodically
                if self.utilization_metrics["total_operations"] % 100 == 0:
                    import gc
                    gc.collect()
                    
        except Exception as e:
            logger.warning(f"⚠️ Memory optimization error: {e}")
    
    def get_utilization_metrics(self) -> Dict[str, Any]:
        """Get current NPU utilization metrics"""
        return {
            **self.utilization_metrics,
            "active_sessions": len(self.active_sessions),
            "max_sessions": self.max_concurrent_sessions,
            "session_types": [info["type"] for info in self.active_sessions.values()],
            "npu_available": self.npu_accelerator.is_available()
        }
    
    def shutdown(self):
        """Shutdown NPU resource manager"""
        logger.info("🔇 Shutting down NPU Resource Manager...")
        
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        
        # Close all sessions
        with self.resource_lock:
            for session_id in list(self.active_sessions.keys()):
                self.active_sessions.pop(session_id)
        
        logger.info("✅ NPU Resource Manager shutdown complete")

class NPUPerformanceOptimizer:
    """NPU-specific performance optimization utilities"""
    
    def __init__(self):
        """Initialize performance optimizer"""
        self.npu_accelerator = NPUAccelerator()
        self.optimization_cache = {}
        
    def optimize_audio_preprocessing(self, audio_data: np.ndarray, target_shape: Tuple[int, ...]) -> np.ndarray:
        """Optimize audio preprocessing for NPU"""
        try:
            # Cache key for optimization
            cache_key = (audio_data.shape, target_shape, audio_data.dtype)
            
            if cache_key in self.optimization_cache:
                transform_func = self.optimization_cache[cache_key]
                return transform_func(audio_data)
            
            # Create optimized transformation
            def transform_func(data):
                # NPU-optimized reshaping and padding
                if data.shape != target_shape:
                    if len(data) < target_shape[0]:
                        # Pad efficiently
                        padding = target_shape[0] - len(data)
                        data = np.pad(data, (0, padding), mode='constant', constant_values=0)
                    else:
                        # Truncate efficiently
                        data = data[:target_shape[0]]
                
                # Ensure correct dtype for NPU
                if data.dtype != np.float32:
                    data = data.astype(np.float32)
                
                # Reshape for NPU processing
                return data.reshape(target_shape)
            
            # Cache the transformation
            self.optimization_cache[cache_key] = transform_func
            
            return transform_func(audio_data)
            
        except Exception as e:
            logger.warning(f"⚠️ Audio preprocessing optimization failed: {e}")
            # Fallback to simple processing
            return self._simple_audio_transform(audio_data, target_shape)
    
    def _simple_audio_transform(self, audio_data: np.ndarray, target_shape: Tuple[int, ...]) -> np.ndarray:
        """Simple fallback audio transformation"""
        if len(audio_data) < target_shape[0]:
            audio_data = np.pad(audio_data, (0, target_shape[0] - len(audio_data)), mode='constant')
        else:
            audio_data = audio_data[:target_shape[0]]
        
        return audio_data.astype(np.float32).reshape(target_shape)
    
    def create_optimized_providers(self, session_type: str) -> List[str]:
        """Create optimized provider list for specific session types"""
        if not self.npu_accelerator.is_available():
            return ['CPUExecutionProvider']
        
        # NPU-optimized provider configurations
        if session_type == "vad":
            # VAD benefits from NPU acceleration
            return ['VitisAIExecutionProvider', 'CPUExecutionProvider']
        elif session_type == "wake_word":
            # Wake word detection benefits from NPU
            return ['VitisAIExecutionProvider', 'CPUExecutionProvider']
        elif session_type == "whisper":
            # Whisper encoder/decoder benefit from NPU
            return ['VitisAIExecutionProvider', 'CPUExecutionProvider']
        else:
            return ['VitisAIExecutionProvider', 'CPUExecutionProvider']
    
    def optimize_model_loading(self, model_path: str, session_type: str) -> Dict[str, Any]:
        """Optimize model loading for NPU"""
        try:
            # Model-specific optimizations
            optimizations = {
                "providers": self.create_optimized_providers(session_type),
                "session_options": {
                    "graph_optimization_level": "all",
                    "execution_mode": "parallel",
                    "enable_cpu_mem_arena": False,
                    "enable_mem_pattern": True
                }
            }
            
            # NPU-specific optimizations
            if 'VitisAIExecutionProvider' in optimizations["providers"]:
                optimizations["npu_config"] = {
                    "enable_fallback": True,
                    "cache_dir": "/tmp/npu_model_cache",
                    "optimization_level": "aggressive"
                }
            
            return optimizations
            
        except Exception as e:
            logger.warning(f"⚠️ Model loading optimization failed: {e}")
            return {"providers": ["CPUExecutionProvider"]}

# Global NPU resource manager instance
npu_resource_manager = NPUResourceManager()
npu_performance_optimizer = NPUPerformanceOptimizer()

def initialize_npu_optimization():
    """Initialize global NPU optimization"""
    return npu_resource_manager.initialize()

def get_npu_metrics():
    """Get NPU utilization metrics"""
    return npu_resource_manager.get_utilization_metrics()

def shutdown_npu_optimization():
    """Shutdown NPU optimization"""
    npu_resource_manager.shutdown()

def test_npu_optimization():
    """Test NPU optimization system"""
    print("🧪 Testing NPU Optimization System...")
    
    # Initialize
    if not initialize_npu_optimization():
        print("❌ Failed to initialize NPU optimization")
        return False
    
    # Test metrics
    metrics = get_npu_metrics()
    print(f"\n📊 NPU Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Test audio optimization
    optimizer = NPUPerformanceOptimizer()
    test_audio = np.random.randn(8000).astype(np.float32)
    optimized_audio = optimizer.optimize_audio_preprocessing(test_audio, (16000,))
    
    print(f"\n🎵 Audio Optimization Test:")
    print(f"  Input shape: {test_audio.shape}")
    print(f"  Output shape: {optimized_audio.shape}")
    print(f"  Data type: {optimized_audio.dtype}")
    
    # Cleanup
    shutdown_npu_optimization()
    
    print("\n🎉 NPU Optimization test completed!")
    return True

if __name__ == "__main__":
    test_npu_optimization()