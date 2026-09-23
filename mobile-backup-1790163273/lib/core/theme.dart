// ═══════════════════════════════════════════════════════════
// H1-AI Mobile — Theme
// ═══════════════════════════════════════════════════════════
import 'package:flutter/material.dart';

// Colors
const Color kPrimaryColor = Color(0xFF0EA5E9);  // Sky blue
const Color kAccentColor = Color(0xFF8B5CF6);   // Purple
const Color kSuccessColor = Color(0xFF10B981);  // Green
const Color kWarningColor = Color(0xFFF59E0B);  // Amber
const Color kErrorColor = Color(0xFFEF4444);    // Red
const Color kDarkBg = Color(0xFF0F172A);        // Navy
const Color kDarkCard = Color(0xFF1E293B);      // Slate

ThemeData get lightTheme => ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: kPrimaryColor,
    brightness: Brightness.light,
  ),
  fontFamily: 'Cairo',  // Arabic font
  appBarTheme: const AppBarTheme(
    centerTitle: true,
    elevation: 0,
  ),
  cardTheme: CardTheme(
    elevation: 2,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
  ),
);

ThemeData get darkTheme => ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: kPrimaryColor,
    brightness: Brightness.dark,
  ),
  scaffoldBackgroundColor: kDarkBg,
  cardColor: kDarkCard,
  fontFamily: 'Cairo',
  appBarTheme: const AppBarTheme(
    centerTitle: true,
    elevation: 0,
    backgroundColor: kDarkCard,
  ),
  cardTheme: CardTheme(
    elevation: 2,
    color: kDarkCard,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: kDarkCard,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
  ),
);
