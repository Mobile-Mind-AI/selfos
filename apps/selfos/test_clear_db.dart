import 'package:flutter/material.dart';
import 'lib/utils/dev_tools.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  print('🧹 Clearing local database...');
  
  try {
    // Choose one:
    
    // Option 1: Clear everything (logs you out)
    // await DevTools.clearAllLocalData();
    
    // Option 2: Clear just database (stays logged in)
    await DevTools.clearLocalDatabase();
    
    print('✅ Done! You can now run the app normally.');
  } catch (e) {
    print('❌ Error: $e');
  }
}