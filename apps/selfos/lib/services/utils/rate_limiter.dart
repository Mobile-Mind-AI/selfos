/// Simple rate limiter to prevent API rate limit errors
/// 
/// This utility helps manage API request rates by enforcing
/// minimum delays between requests to avoid 429 errors.

import 'dart:async';

class RateLimiter {
  static final Map<String, DateTime> _lastRequestTimes = {};
  static final Map<String, int> _requestCounts = {};
  static final Map<String, DateTime> _windowStarts = {};
  
  // Default rate limits
  static const Duration _minDelay = Duration(milliseconds: 100); // 100ms between requests
  static const int _maxRequestsPerWindow = 10; // 10 requests per window
  static const Duration _windowDuration = Duration(seconds: 10); // 10 second window
  
  /// Execute a function with rate limiting
  /// 
  /// [key] - Unique identifier for the rate limit bucket
  /// [function] - The async function to execute
  /// [minDelay] - Minimum delay between requests (default: 100ms)
  /// [maxRequests] - Maximum requests per window (default: 10)
  /// [windowDuration] - Window duration (default: 10 seconds)
  static Future<T> execute<T>(
    String key,
    Future<T> Function() function, {
    Duration minDelay = _minDelay,
    int maxRequests = _maxRequestsPerWindow,
    Duration windowDuration = _windowDuration,
  }) async {
    // Check and update window
    final now = DateTime.now();
    final windowStart = _windowStarts[key];
    
    if (windowStart == null || now.difference(windowStart) > windowDuration) {
      // New window
      _windowStarts[key] = now;
      _requestCounts[key] = 0;
    }
    
    // Check request count in current window
    final currentCount = _requestCounts[key] ?? 0;
    if (currentCount >= maxRequests) {
      // Wait until window expires
      final waitTime = windowDuration - now.difference(_windowStarts[key]!);
      if (waitTime.isNegative == false) {
        print('⏳ Rate limit reached for $key. Waiting ${waitTime.inMilliseconds}ms...');
        await Future.delayed(waitTime);
        // Reset window after waiting
        _windowStarts[key] = DateTime.now();
        _requestCounts[key] = 0;
      }
    }
    
    // Check minimum delay between requests
    final lastRequest = _lastRequestTimes[key];
    if (lastRequest != null) {
      final elapsed = now.difference(lastRequest);
      if (elapsed < minDelay) {
        final waitTime = minDelay - elapsed;
        print('⏳ Rate limiting $key: waiting ${waitTime.inMilliseconds}ms');
        await Future.delayed(waitTime);
      }
    }
    
    // Update tracking
    _lastRequestTimes[key] = DateTime.now();
    _requestCounts[key] = currentCount + 1;
    
    // Execute the function
    return await function();
  }
  
  /// Clear rate limit tracking for a specific key
  static void clear(String key) {
    _lastRequestTimes.remove(key);
    _requestCounts.remove(key);
    _windowStarts.remove(key);
  }
  
  /// Clear all rate limit tracking
  static void clearAll() {
    _lastRequestTimes.clear();
    _requestCounts.clear();
    _windowStarts.clear();
  }
}