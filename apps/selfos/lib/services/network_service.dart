/// Network Service for monitoring connectivity and managing retry logic
/// 
/// This service provides:
/// - Real-time network connectivity monitoring
/// - Intelligent retry logic with exponential backoff
/// - Network state changes notification
/// - Connection quality assessment

import 'dart:async';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:http/http.dart' as http;

/// Network connection status
enum NetworkStatus {
  online,
  offline,
  unstable,
  unknown,
}

/// Network quality assessment
enum NetworkQuality {
  excellent,  // Fast, reliable connection
  good,       // Good connection with minor delays
  poor,       // Slow or unreliable connection
  offline,    // No connection
}

/// Network status information
class NetworkState {
  final NetworkStatus status;
  final NetworkQuality quality;
  final ConnectivityResult connectivityType;
  final Duration? latency;
  final DateTime lastChecked;
  final bool canReachBackend;

  NetworkState({
    required this.status,
    required this.quality,
    required this.connectivityType,
    this.latency,
    required this.lastChecked,
    required this.canReachBackend,
  });

  bool get isOnline => status == NetworkStatus.online;
  bool get isGoodQuality => quality == NetworkQuality.excellent || quality == NetworkQuality.good;
}

/// Network monitoring and retry service
class NetworkService {
  static NetworkService? _instance;
  NetworkService._();

  static NetworkService get instance {
    _instance ??= NetworkService._();
    return _instance!;
  }

  final Connectivity _connectivity = Connectivity();
  
  // Network state
  NetworkState _currentState = NetworkState(
    status: NetworkStatus.unknown,
    quality: NetworkQuality.offline,
    connectivityType: ConnectivityResult.none,
    lastChecked: DateTime.now(),
    canReachBackend: false,
  );

  // Stream controllers
  final StreamController<NetworkState> _stateController = 
      StreamController<NetworkState>.broadcast();
  
  // Timers and subscriptions
  Timer? _healthCheckTimer;
  StreamSubscription<ConnectivityResult>? _connectivitySubscription;
  
  // Configuration
  static const Duration _healthCheckInterval = Duration(seconds: 30);
  static const String _backendHealthEndpoint = 'http://127.0.0.1:8000/'; // From app_config.dart
  static const Duration _requestTimeout = Duration(seconds: 10);

  /// Stream of network state changes
  Stream<NetworkState> get stateStream => _stateController.stream;

  /// Current network state
  NetworkState get currentState => _currentState;

  /// Initialize network monitoring
  Future<void> initialize() async {
    print('🌐 Initializing network service...');

    // Listen to connectivity changes
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      _onConnectivityChanged,
    );

    // Check initial connectivity
    final connectivityResult = await _connectivity.checkConnectivity();
    await _onConnectivityChanged(connectivityResult);

    // Start periodic health checks
    _healthCheckTimer = Timer.periodic(_healthCheckInterval, (_) {
      _performHealthCheck();
    });

    print('✅ Network service initialized');
  }

  /// Handle connectivity changes
  Future<void> _onConnectivityChanged(ConnectivityResult result) async {
    print('📶 Connectivity changed: ${result.name}');

    if (result == ConnectivityResult.none) {
      // Definitely offline
      _updateState(NetworkState(
        status: NetworkStatus.offline,
        quality: NetworkQuality.offline,
        connectivityType: result,
        lastChecked: DateTime.now(),
        canReachBackend: false,
      ));
    } else {
      // Potentially online - verify with health check
      await _performHealthCheck(connectivityType: result);
    }
  }

  /// Perform backend health check
  Future<void> _performHealthCheck({ConnectivityResult? connectivityType}) async {
    try {
      final connectivityResult = connectivityType ?? await _connectivity.checkConnectivity();
      
      if (connectivityResult == ConnectivityResult.none) {
        _updateState(NetworkState(
          status: NetworkStatus.offline,
          quality: NetworkQuality.offline,
          connectivityType: connectivityResult,
          lastChecked: DateTime.now(),
          canReachBackend: false,
        ));
        return;
      }

      // Measure latency and backend reachability
      final stopwatch = Stopwatch()..start();
      
      final response = await http.get(
        Uri.parse(_backendHealthEndpoint),
        headers: {'Connection': 'close'},
      ).timeout(_requestTimeout);

      stopwatch.stop();
      final latency = stopwatch.elapsed;

      final canReach = response.statusCode == 200;
      final quality = _assessQuality(latency, canReach);
      final status = canReach ? NetworkStatus.online : NetworkStatus.unstable;

      _updateState(NetworkState(
        status: status,
        quality: quality,
        connectivityType: connectivityResult,
        latency: latency,
        lastChecked: DateTime.now(),
        canReachBackend: canReach,
      ));

      if (canReach) {
        print('✅ Backend reachable - latency: ${latency.inMilliseconds}ms');
      } else {
        print('⚠️ Backend unreachable - status: ${response.statusCode}');
      }

    } catch (e) {
      // Network error or timeout
      final connectivityResult = connectivityType ?? await _connectivity.checkConnectivity();
      
      _updateState(NetworkState(
        status: NetworkStatus.offline,
        quality: NetworkQuality.offline,
        connectivityType: connectivityResult,
        lastChecked: DateTime.now(),
        canReachBackend: false,
      ));

      print('❌ Network health check failed: $e');
    }
  }

  /// Assess network quality based on latency and reachability
  NetworkQuality _assessQuality(Duration latency, bool canReach) {
    if (!canReach) return NetworkQuality.offline;

    final latencyMs = latency.inMilliseconds;
    
    if (latencyMs < 200) return NetworkQuality.excellent;
    if (latencyMs < 1000) return NetworkQuality.good;
    return NetworkQuality.poor;
  }

  /// Update network state and notify listeners
  void _updateState(NetworkState newState) {
    final wasOnline = _currentState.isOnline;
    final isNowOnline = newState.isOnline;

    _currentState = newState;
    _stateController.add(newState);

    // Log significant state changes
    if (!wasOnline && isNowOnline) {
      print('🌐 Network restored: ${newState.quality.name} quality');
    } else if (wasOnline && !isNowOnline) {
      print('📶 Network lost');
    }
  }

  /// Execute operation with retry logic
  Future<T> withRetry<T>(
    Future<T> Function() operation, {
    int maxRetries = 3,
    Duration baseDelay = const Duration(seconds: 1),
    bool requiresNetwork = true,
  }) async {
    int attempt = 0;
    Duration delay = baseDelay;

    while (attempt <= maxRetries) {
      try {
        // Check network requirement
        if (requiresNetwork && !_currentState.isOnline) {
          throw NetworkException('Operation requires network connection');
        }

        // Attempt operation
        return await operation();

      } catch (e) {
        attempt++;
        
        if (attempt > maxRetries) {
          throw NetworkException('Max retries exceeded: $e');
        }

        // Exponential backoff with jitter
        final jitter = Duration(milliseconds: (DateTime.now().millisecond % 200));
        final totalDelay = delay + jitter;
        
        print('🔄 Retry attempt $attempt after ${totalDelay.inSeconds}s: $e');
        await Future.delayed(totalDelay);
        
        delay = Duration(milliseconds: (delay.inMilliseconds * 1.5).round());

        // Refresh network state before retry
        if (requiresNetwork) {
          await _performHealthCheck();
        }
      }
    }

    throw NetworkException('Retry logic failed unexpectedly');
  }

  /// Wait for network to be available
  Future<void> waitForNetwork({Duration? timeout}) async {
    if (_currentState.isOnline) return;

    final completer = Completer<void>();
    late StreamSubscription<NetworkState> subscription;
    Timer? timeoutTimer;

    subscription = stateStream.listen((state) {
      if (state.isOnline) {
        subscription.cancel();
        timeoutTimer?.cancel();
        if (!completer.isCompleted) {
          completer.complete();
        }
      }
    });

    // Setup timeout if specified
    if (timeout != null) {
      timeoutTimer = Timer(timeout, () {
        subscription.cancel();
        if (!completer.isCompleted) {
          completer.completeError(TimeoutException('Network wait timeout', timeout));
        }
      });
    }

    return completer.future;
  }

  /// Get network statistics
  Map<String, dynamic> getNetworkStats() {
    return {
      'status': _currentState.status.name,
      'quality': _currentState.quality.name,
      'connectivity_type': _currentState.connectivityType.name,
      'latency_ms': _currentState.latency?.inMilliseconds,
      'last_checked': _currentState.lastChecked.toIso8601String(),
      'can_reach_backend': _currentState.canReachBackend,
      'is_online': _currentState.isOnline,
      'is_good_quality': _currentState.isGoodQuality,
    };
  }

  /// Force immediate network check
  Future<NetworkState> checkNetwork() async {
    await _performHealthCheck();
    return _currentState;
  }

  /// Dispose resources
  void dispose() {
    _healthCheckTimer?.cancel();
    _connectivitySubscription?.cancel();
    _stateController.close();
    print('🔒 Network service disposed');
  }
}

/// Network-related exceptions
class NetworkException implements Exception {
  final String message;
  
  NetworkException(this.message);
  
  @override
  String toString() => 'NetworkException: $message';
}

/// Timeout exception
class TimeoutException implements Exception {
  final String message;
  final Duration timeout;
  
  TimeoutException(this.message, this.timeout);
  
  @override
  String toString() => 'TimeoutException: $message (${timeout.inSeconds}s)';
}