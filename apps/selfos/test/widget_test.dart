// Basic Flutter widget test for SelfOS app
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:selfos/main.dart';

void main() {
  testWidgets('SelfOS app initialization test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: SelfOSApp(),
      ),
    );

    // Verify that the splash screen is shown initially
    expect(find.text('SelfOS'), findsOneWidget);
    expect(find.text('Personal Growth Operating System'), findsOneWidget);

    // Wait for initialization
    await tester.pumpAndSettle();
  });
}